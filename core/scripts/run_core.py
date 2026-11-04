"""
앙개봇 Python Core v0.4.2 실행기 — 모든 기능 상세 설명
1. 기존 start-termux.sh의 .env 인증키 로딩, FastAPI 앱, 127.0.0.1:8765 바인딩을 유지한다.
2. data/.core-run.lock에 POSIX flock을 걸어 runit/수동 실행 중복을 방지한다.
3. 잠금 FD를 uvicorn 프로세스에 상속해 exec 이후에도 단일 실행 상태를 유지한다.
4. 포트 8765에서 다른 프로세스가 이미 수신 중이면 기존 로그를 회전하거나 서버를 띄우지 않는다.
5. 기존 logs/server.log의 stdout/stderr 누적 기록을 유지하고 시작할 때 8 MiB 이상이면 보관한다.
6. 회전한 로그는 logs/archive/에 이름 충돌 없이 보존하며 자동 삭제하지 않는다.
7. runit이 감시하는 PID를 os.execv로 직접 uvicorn에 넘겨 종료/재시작 신호 흐름을 보존한다.
8. 기존 SQLite jobs/events/AI 문맥/Android UI/알림/카톡 답장 설정을 수정하지 않는다.
9. 새로운 암호/네트워크 포트/외부 PC 명령/비밀정보 출력 기능을 추가하지 않는다.
10. 실행 실패 및 중복 상태만 logs/launcher.log에 기록한다. 로그 본문에 토큰을 쓰지 않는다.
11. v0.5.0 관심종목 그룹 운영도 기존 단일 실행/백업/포트 방침을 유지한다.
12. v0.5.1 프리셋/그룹 10종목에서도 시작/중복잠금/로그/DB/기존 runit 처리 기능을 유지한다.
13. v0.5.2 과거 시세 조회를 추가하더라도 Core 단일 실행·로그 보존·워치독 복구는 변경하지 않는다.
11. FastAPI 런처 시작 로그의 버전 문자열을 0.4.1로 갱신하고 로그 이벤트 형식은 유지한다.
12. v0.4.2 런처 버전만 갱신하고 이전 로그 형식/단일실행/SSH/Watchdog 기능을 보존한다.
14. v0.5.3에서 한글 종목 별칭 조회가 추가되어도 재시작·단일 인스턴스·로그 보관은 이전과 같다.
15. v0.5.6 자원정리 회귀테스트에도 기존 runit 단일실행/서버 로그 보존/락/포트 점유검사는 변경하지 않는다.
"""
from __future__ import annotations

import errno
import fcntl
import os
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

CORE = Path(__file__).resolve().parents[1]
PORT = 8765
ROTATE_BYTES = 8 * 1024 * 1024


def startup_log(core: Path, message: str) -> None:
    """서버 실행 전 오류 전용 누적 로그(기존 server.log 유지)."""
    directory = core / 'logs'
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / 'launcher.log').open('a', encoding='utf-8') as stream:
        stream.write(f'{datetime.now().astimezone().isoformat(timespec="seconds")} {message}\n')


def acquire_lock(core: Path) -> int | None:
    """성공 시 uvicorn 프로세스까지 물려줄 잠금 FD; 실패 시 None."""
    directory = core / 'data'
    directory.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(str(directory / '.core-run.lock'), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        os.close(descriptor)
        if error.errno in (errno.EACCES, errno.EAGAIN):
            return None
        raise
    os.set_inheritable(descriptor, True)
    return descriptor


def port_in_use(port: int = PORT) -> bool:
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=0.4):
            return True
    except (OSError, TimeoutError):
        return False


def rotate_server_log(core: Path, max_bytes: int = ROTATE_BYTES) -> Path | None:
    """활성 로그 파일을 열기 *전*에 아카이브한다. 보관본은 삭제하지 않는다."""
    logfile = core / 'logs' / 'server.log'
    if not logfile.is_file() or logfile.stat().st_size < max_bytes:
        return None
    archive = core / 'logs' / 'archive'
    archive.mkdir(parents=True, exist_ok=True)
    name = f'server_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}_{os.getpid()}.log'
    target = archive / name
    logfile.rename(target)
    return target


def launch(core: Path = CORE) -> int:
    os.umask(0o077)
    os.chdir(core)
    (core / 'logs').mkdir(parents=True, exist_ok=True)
    fd = acquire_lock(core)
    if fd is None:
        startup_log(core, 'CORE_DUPLICATE_BLOCKED lock_already_held')
        time.sleep(10)  # runit의 초고속 재시도 루프 방지
        return 2
    if port_in_use():
        startup_log(core, 'CORE_DUPLICATE_BLOCKED port_8765_in_use')
        time.sleep(10)
        return 2
    archived = rotate_server_log(core)
    output = os.open(str(core / 'logs' / 'server.log'), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.dup2(output, 1)
        os.dup2(output, 2)
    finally:
        if output > 2:
            os.close(output)
    marker = f'CORE_START version=0.5.6 pid={os.getpid()}'
    if archived:
        marker += f' previous_log_archived={archived.name}'
    os.write(2, (marker + '\n').encode('utf-8'))
    # runit이 감시하는 바로 그 PID로 교체. fd 잠금은 exec 뒤에도 살아 있다.
    args = [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
            '--port', str(PORT), '--no-access-log']
    os.execv(sys.executable, args)
    return 0  # execv 성공 시 도달 불가


if __name__ == '__main__':
    raise SystemExit(launch())
