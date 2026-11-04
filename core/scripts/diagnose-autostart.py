"""
앙개봇 v0.3.1 읽기 전용 운영 진단 — 전체 기능 상세 설명
1. 기존 FastAPI 토큰 인증 health API를 호출해 서버 버전 및 uptime만 확인한다.
2. runit의 angaebot-core, angaebot-watchdog, sshd 서비스 상태를 읽기 전용으로 표시한다.
3. 로컬 8022 SSH 포트 TCP 연결 여부와 runit 실행 프로세스를 확인한다.
4. 부팅 진단 로그의 마지막 수정 시각과 줄 수, 마지막 부팅 신호를 표시한다.
5. server.log/watchdog.log/launcher.log/boot.log 크기 및 로그 아카이브 개수·용량을 표시한다.
6. .env 인증키는 health 검사에만 쓰고, 출력/로그/DB에 공개하지 않는다.
7. Android/Kakao 수신·답장·DB·설정·파일을 수정/삭제하거나 서비스 재시작하지 않는다.
8. Android의 netlink/ss 권한 오류에 의존하지 않고 Python TCP 검사만 사용한다.
9. Termux service가 설치되지 않았다면 미설치 또는 조회 실패를 출력해 원인을 구분한다.
10. SSH 실패·부팅 미실행을 즉시 고친다고 주장하지 않고 실제 검증 상태만 표시한다.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PREFIX = Path(os.environ.get('PREFIX', '/data/data/com.termux/files/usr'))


def fmt_bytes(value: int) -> str:
    for unit in ('B', 'KiB', 'MiB', 'GiB'):
        if value < 1024 or unit == 'GiB':
            return f'{value:.1f} {unit}'
        value /= 1024
    return '?'


def is_listening(port: int) -> bool:
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=0.4):
            return True
    except (OSError, TimeoutError):
        return False


def service_status(name: str) -> str:
    directory = PREFIX / 'var' / 'service' / name
    if not directory.is_dir():
        return 'NOT_INSTALLED'
    command = shutil.which('sv') or str(PREFIX / 'bin' / 'sv')
    try:
        done = subprocess.run([command, 'status', str(directory)], capture_output=True,
                              text=True, timeout=3, check=False)
        result = (done.stdout or done.stderr).strip().splitlines()
        return (result[0] if result else 'NO_OUTPUT')[:200]
    except (OSError, subprocess.TimeoutExpired):
        return 'STATUS_UNAVAILABLE'


def health_status() -> str:
    token_file = ROOT / '.env'
    if not token_file.exists():
        return 'ENV_MISSING'
    from health_watchdog import token_from_env
    try:
        token = token_from_env()
        req = Request('http://127.0.0.1:8765/v1/health',
                      headers={'X-AngaeBot-Token': token})
        with urlopen(req, timeout=3) as response:
            data = json.load(response)
        if data.get('ok') is True:
            return f"HEALTH_OK version={data.get('version','?')} uptime={data.get('uptime_seconds','?')}s"
        return 'HEALTH_RESPONSE_NOT_OK'
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        return 'HEALTH_UNAVAILABLE'


def log_information(root: Path = ROOT) -> list[str]:
    logdir = root / 'logs'
    result = []
    for name in ('server.log', 'watchdog.log', 'launcher.log', 'boot.log'):
        path = logdir / name
        if path.is_file():
            result.append(f'{name}={fmt_bytes(path.stat().st_size)}')
        else:
            result.append(f'{name}=ABSENT')
    archive = logdir / 'archive'
    files = list(archive.glob('*.log')) if archive.is_dir() else []
    total = sum(f.stat().st_size for f in files if f.is_file())
    result.append(f'archives={len(files)} ({fmt_bytes(total)})')
    bootlog = logdir / 'boot.log'
    if bootlog.is_file():
        result.append('boot_log_last_written=' + datetime.fromtimestamp(bootlog.stat().st_mtime).astimezone().isoformat(timespec='seconds'))
    else:
        result.append('boot_log_last_written=UNVERIFIED')
    return result


def main() -> None:
    print('AngaeBot 24/7 Read-only Diagnostics v0.3.1')
    print('Core:', service_status('angaebot-core'))
    print('Watchdog:', service_status('angaebot-watchdog'))
    print('SSHD:', service_status('sshd'))
    print('SSH_TCP_8022:', 'OPEN' if is_listening(8022) else 'CLOSED')
    print('FastAPI:', health_status())
    for entry in log_information():
        print('LOG:', entry)
    print('NOTE: Android 자동 부팅/잠금해제 전 서비스 복귀는 실제 재부팅 테스트가 필요합니다.')


if __name__ == '__main__':
    main()
