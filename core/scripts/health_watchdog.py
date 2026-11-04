"""
앙개봇 v0.3.1 FastAPI 감시기 — 기존 및 신규 기능 전체 설명
1. 127.0.0.1:8765/v1/health에 X-AngaeBot-Token 인증으로 30초마다 연결한다.
2. 기존 WATCHDOG_STARTED/HEALTH_OK/HEALTH_FAILED/RESTART_REQUESTED 로그 표기를 유지한다.
3. 연속 3회 실패 시 기존 runit `sv restart angaebot-core`를 통해 서버만 재시작한다.
4. 반복 장애 시 최대 5분 지수 백오프로 무한 재시작 폭주를 방지하고 백오프를 기록한다.
5. 매 검사마다 .env 토큰을 다시 읽어 설정 변경 후에도 watchdog을 중단하지 않는다.
6. logs/watchdog.log가 2 MiB 이상이면 logs/archive로 이동한 뒤 새로운 파일에 기록한다.
7. 이전 로그 아카이브와 server.log, DB, 모든 사용자 인증정보를 삭제하지 않는다.
8. 기존 watchdog runit 실행, Android 수신·명령·빠른답장·로그 UI를 변경하지 않는다.
9. 자체 SSH·시스템 앱·외부 서버를 재시작하지 않고 새 패키지를 설치하지 않는다.
10. 오류 로그에는 토큰 값·요청 질문 본문을 출력하지 않는다.
"""
from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CORE = Path(__file__).resolve().parents[1]
INTERVAL = 30
THRESHOLD = 3
MAX_BACKOFF = 300
WATCHDOG_LOG_MAX_BYTES = 2 * 1024 * 1024
HEALTH_URL = 'http://127.0.0.1:8765/v1/health'


def log(message: str) -> None:
    folder = CORE / 'logs'
    folder.mkdir(parents=True, exist_ok=True)
    logfile = folder / 'watchdog.log'
    if logfile.exists() and logfile.stat().st_size >= WATCHDOG_LOG_MAX_BYTES:
        archive = folder / 'archive'
        archive.mkdir(parents=True, exist_ok=True)
        target = archive / f'watchdog_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}_{os.getpid()}.log'
        logfile.rename(target)
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
    with logfile.open('a', encoding='utf-8') as fh:
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


@dataclass
class WatchdogState:
    failures: int = 0
    attempts: int = 0
    next_retry: float = 0.0
    was_healthy: bool | None = None

    def step(self, ok: bool, now: float, restart=restart_service, logger=log) -> None:
        if ok:
            if self.was_healthy is not True:
                logger('HEALTH_OK')
            self.failures = 0
            self.attempts = 0
            self.next_retry = 0.0
            self.was_healthy = True
            return
        self.failures += 1
        if self.was_healthy is not False:
            logger('HEALTH_FAILED')
        self.was_healthy = False
        if self.failures < THRESHOLD or now < self.next_retry:
            return
        success = restart()
        logger('RESTART_REQUESTED success=' + str(success).lower())
        delay = min(MAX_BACKOFF, INTERVAL * (2 ** min(self.attempts, 4)))
        self.attempts += 1
        self.next_retry = now + delay
        self.failures = 0
        logger('RESTART_BACKOFF seconds=' + str(delay))


def main() -> None:
    state = WatchdogState()
    log('WATCHDOG_STARTED interval=30s threshold=3')
    while True:
        try:
            token = token_from_env()
            healthy = health_ok(token)
        except (OSError, ValueError, RuntimeError):
            healthy = False
            if state.was_healthy is not False:
                log('TOKEN_LOAD_FAILED')
        state.step(healthy, time.monotonic())
        time.sleep(INTERVAL)


if __name__ == '__main__':
    main()
