"""
앙개봇 Python Core v0.4.2 읽기 전용 운영 명령 — 전체 구현 기능 상세 설명
1. '상세상태': Python Core/Watchdog/SSH의 runit 상태와 SSH 로컬 8022 포트를 읽기만 한다.
2. '통계': 기존 SQLite jobs를 채팅방·발신자별로 집계하고 성공·실패·명령 TOP5를 표시한다.
3. '최근오류': 같은 방·발신자의 실패 작업 5건에서 시간·명령·오류 메시지만 제한해 보여준다.
4. '가동시간': 현재 Python 프로세스 시작 시각과 가동 시간을 한국 시각으로 보여준다.
5. 기존 jobs/events/AI 문맥/Android 로그의 레코드를 삭제하거나 구조를 바꾸지 않는다.
6. 통계는 실제 Python Core에 저장된 명령만 포함하며 Android의 로컬 테스트·도움말은 세지 않는다.
7. 서버 조회는 로컬 파일·runit 상태·SQLite 읽기만 수행하며 SSH·서비스를 재시작하지 않는다.
8. 서비스 조회에 짧은 상한을 적용해 기존 Android의 4초 HTTP 제한 이내에 동작하도록 한다.
9. 토큰·질문 본문·방과 발신자 이름·서버 로그 원문을 응답 또는 진단 로그에 출력하지 않는다.
10. 미설치 서비스나 포트 제한은 미확인/중지로 표시하고 실행 중이라고 추측하지 않는다.
11. 같은 request_id 재전송은 기존 main.py SQLite jobs 중복 방지로 처리한다.
12. OpenAI/Ollama는 호출하지 않고, AI가 OFF여도 기존 계산·시간·상태 및 새 명령을 사용한다.
13. v0.4.1에서는 기존 운영 명령의 출력·로그·SQL을 유지하고 상세상태 버전 표시만 최신화한다.
14. v0.4.2에서도 SQLite 조회 범위와 상세상태·통계·최근오류·가동시간 내용을 유지한다.
v0.5.3은 기존 운영 상태·로그 흐름을 유지한 채 종목 이름 조회만 확장한다.
"""
from __future__ import annotations

import os
import shutil
import socket
import sqlite3
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
PREFIX = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))


def format_uptime(seconds: int) -> str:
    value = max(0, int(seconds))
    days, rem = divmod(value, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{days}일 {hours}시간 {minutes}분 {secs}초"


def service_status(name: str, *, prefix: Path | None = None) -> str:
    """최대 0.8초 동안 runit 상태 조회; 프로세스/서비스 상태 변경 금지."""
    root = prefix or PREFIX
    path = root / "var" / "service" / name
    if not path.is_dir():
        return "미설치"
    program = shutil.which("sv") or str(root / "bin" / "sv")
    try:
        result = subprocess.run([program, "status", str(path)], capture_output=True,
                                text=True, timeout=0.8, check=False)
        line = (result.stdout or result.stderr).strip().splitlines()
        if result.returncode == 0 and line and line[0].startswith("run:"):
            return "실행 중"
        if line and line[0].startswith("down:"):
            return "중지됨"
        return "확인 불가"
    except (OSError, subprocess.TimeoutExpired):
        return "확인 불가"


def ssh_status(port: int = 8022) -> str:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return "연결 가능"
    except (OSError, TimeoutError):
        return "연결 불가"


def details(uptime_seconds: int, *, services=service_status, ssh=ssh_status) -> str:
    return ("🛠 앙개봇 운영 상세상태 (v0.4.2)\n"
            f"Python Core: {services('angaebot-core')}\n"
            f"Watchdog: {services('angaebot-watchdog')}\n"
            f"SSH 서비스: {services('sshd')}\n"
            f"SSH 8022: {ssh()}\n"
            f"Python 가동: {format_uptime(uptime_seconds)}\n"
            "※ 서비스 확인만 수행하며 재시작하지 않습니다.")


def command_stats(db: sqlite3.Connection, room: str, sender: str) -> str:
    row = db.execute("""SELECT COUNT(*),
                         COALESCE(SUM(CASE WHEN ok=1 THEN 1 ELSE 0 END), 0),
                         COALESCE(SUM(CASE WHEN ok=0 THEN 1 ELSE 0 END), 0)
                      FROM jobs WHERE room=? AND sender=?""", (room, sender)).fetchone()
    total, passed, failed = (int(x) for x in row)
    tops = db.execute("""SELECT command, COUNT(*) AS n FROM jobs
                         WHERE room=? AND sender=?
                         GROUP BY command ORDER BY n DESC, command ASC LIMIT 5""",
                      (room, sender)).fetchall()
    lines = ["📊 앙개봇 Python 명령 통계 (이 채팅·발신자)",
             f"전체: {total:,}건 / 성공: {passed:,}건 / 실패: {failed:,}건"]
    if tops:
        lines.append("많이 사용한 명령:")
        lines.extend(f"• {name[:24]}: {count:,}건" for name, count in tops)
    else:
        lines.append("저장된 명령이 없습니다.")
    lines.append("※ 이번 조회 직전까지 기록된 Python 명령 기준")
    return "\n".join(lines)


def recent_errors(db: sqlite3.Connection, room: str, sender: str) -> str:
    rows = db.execute("""SELECT created_at, command, result FROM jobs
                         WHERE room=? AND sender=? AND ok=0
                         ORDER BY created_at DESC, rowid DESC LIMIT 5""",
                      (room, sender)).fetchall()
    if not rows:
        return "✅ 최근 오류: 이 채팅·발신자의 Python 명령 실패 기록이 없습니다."
    lines = ["⚠️ 최근 Python 명령 오류 5건 이내 (이 채팅·발신자)"]
    for created, command, message in rows:
        timestamp = datetime.fromtimestamp(int(created), tz=KST).strftime("%m-%d %H:%M")
        # 기존 jobs의 실패 응답만 인용한다. 사용자 명령 인수나 이벤트 로그는 출력하지 않는다.
        reason = " ".join(str(message).split())[:95]
        lines.append(f"• {timestamp} {str(command)[:24]}: {reason}")
    return "\n".join(lines)


def uptime_report(uptime_seconds: int) -> str:
    now = datetime.now(KST)
    began = now - timedelta(seconds=max(0, int(uptime_seconds)))
    return ("⏱ 앙개봇 Python 가동시간\n"
            f"현재 프로세스 시작: {began:%Y-%m-%d %H:%M:%S} KST\n"
            f"연속 가동: {format_uptime(uptime_seconds)}\n"
            "※ FastAPI 프로세스 기준 (S20+ 기기 가동시간과 다름)")
