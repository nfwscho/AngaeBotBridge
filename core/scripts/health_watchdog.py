"""
앙개봇 v0.2.1 Python 상태 감시기 — 모든 기능 상세 주석
1. 기존 v0.2.0 FastAPI `/v1/health` 엔드포인트에 127.0.0.1로만 접속한다.
2. .env에 저장된 기존 ANGAE_TOKEN을 읽어 인증한다. 토큰은 절대 로그에 남기지 않는다.
3. 서버 미응답/오류가 3회 연속이면 `runit sv restart angaebot-core`를 실행한다.
4. 검사 간격 30초, HTTP 타임아웃 4초. 정상 복구 시 상태 전환을 기록한다.
5. watchdog 서비스 자체도 runit이 감시하므로 예외 종료 시 재시작된다.
6. logs/watchdog.log에 기록을 추가하며 기존 로그와 SQLite DB는 수정/삭제하지 않는다.
7. Android 앱의 수신, 명령, UI 및 SQLite 로그 로직에는 영향을 주지 않는다.
8. Android가 Termux 전체를 강제 종료하는 상황을 복구할 수는 없다.
"""
from __future__ import annotations

import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CORE = Path(__file__).resolve().parents[1]
INTERVAL = 30
THRESHOLD = 3
HEALTH_URL = 'http://127.0.0.1:8765/v1/health'


def log(message: str) -> None:
    folder = CORE / 'logs'
    folder.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
    with (folder / 'watchdog.log').open('a', encoding='utf-8') as fh:
        fh.write(f'{timestamp} {message}\n')


def token_from_env() -> str:
    path = CORE / '.env'
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('ANGAE_TOKEN='):
            return line.split('=', 1)[1].strip().strip('"').strip("'")
    raise RuntimeError('ANGAE_TOKEN missing')


def health_ok(token: str, url: str = HEALTH_URL) -> bool:
    request = Request(url, headers={'X-AngaeBot-Token': token})
    try:
        with urlopen(request, timeout=4) as response:
            return response.status == 200
    except (OSError, HTTPError, URLError, ValueError):
        return False


def restart_service() -> bool:
    prefix = os.environ.get('PREFIX', '/data/data/com.termux/files/usr')
    sv = str(Path(prefix) / 'bin' / 'sv')
    service = str(Path(prefix) / 'var' / 'service' / 'angaebot-core')
    try:
        result = subprocess.run([sv, 'restart', service], capture_output=True,
                                text=True, timeout=12, check=False)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def main() -> None:
    token = token_from_env()
    failures = 0
    was_healthy = None
    log('WATCHDOG_STARTED interval=30s threshold=3')
    while True:
        ok = health_ok(token)
        if ok:
            if was_healthy is not True:
                log('HEALTH_OK')
            failures = 0
            was_healthy = True
        else:
            failures += 1
            if was_healthy is not False:
                log('HEALTH_FAILED')
            was_healthy = False
            if failures >= THRESHOLD:
                success = restart_service()
                log('RESTART_REQUESTED success=' + str(success).lower())
                failures = 0
        time.sleep(INTERVAL)


if __name__ == '__main__':
    main()
