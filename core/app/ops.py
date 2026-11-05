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
15. 설정·운영 메뉴에서 서버 상태, 배포 기록, 사용자별 실행 로그, 구성 상태를 안전하게 읽기 전용으로 조회한다.
16. 배포 기록은 검증된 SHA와 브랜치만 읽으며 누락되면 '미기록'으로 표시하고 추측하지 않는다.
17. 로그는 같은 방·발신자의 최근 명령/성공 여부·시간만 보여주고 인수·질문·토큰·이벤트 원문은 표시하지 않는다.
18. 설정 화면은 AI 설정 상태와 세션 제한만 표시하고 환경변수·인증키·비밀 정보를 노출하지 않는다.
19. 기존 SQLite 테이블·로그·DB 스키마·원격 작업·Android UI·기존 운영 명령의 출력은 변경하지 않는다.
20. 인증된 상태 API에 로컬 배포기록에서 읽은 브랜치와 SHA만 노출하며 기록이 없으면 미확인 반환한다.
21. 실제 배포된 코어와 GitHub의 main 최신 커밋을 혼동하지 않고 기존 배포정보 화면은 유지한다.
"""
from __future__ import annotations

import os
import json
import re
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
    return ("🛠 서버 상세상태\n"
            f"Core {services('angaebot-core')} · 감시 {services('angaebot-watchdog')}\n"
            f"SSH {services('sshd')} · 8022 {ssh()}\n"
            f"⏱ {format_uptime(uptime_seconds)}")


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
    lines = ["📊 명령 통계 (현재 대화)",
             f"전체 {total:,} · 성공 {passed:,} · 실패 {failed:,}"]
    if tops:
        lines.append("주요 명령:")
        lines.extend(f"• {name[:24]}: {count:,}건" for name, count in tops)
    else:
        lines.append("저장된 명령이 없습니다.")
    
    return "\n".join(lines)


def recent_errors(db: sqlite3.Connection, room: str, sender: str) -> str:
    rows = db.execute("""SELECT created_at, command, result FROM jobs
                         WHERE room=? AND sender=? AND ok=0
                         ORDER BY created_at DESC, rowid DESC LIMIT 5""",
                      (room, sender)).fetchall()
    if not rows:
        return "✅ 최근 오류 없음 (현재 대화)"
    lines = ["⚠️ 최근 오류 (현재 대화·최대 5건)"]
    for created, command, message in rows:
        timestamp = datetime.fromtimestamp(int(created), tz=KST).strftime("%m-%d %H:%M")
        # 기존 jobs의 실패 응답만 인용한다. 사용자 명령 인수나 이벤트 로그는 출력하지 않는다.
        reason = " ".join(str(message).split())[:95]
        lines.append(f"• {timestamp} {str(command)[:24]}: {reason}")
    return "\n".join(lines)


def uptime_report(uptime_seconds: int) -> str:
    now = datetime.now(KST)
    began = now - timedelta(seconds=max(0, int(uptime_seconds)))
    return (f"⏱ Python 가동 {format_uptime(uptime_seconds)}\n"
            f"시작 {began:%m/%d %H:%M} KST · Core 기준")


def deployment_report(core_version: str, *, info_path: Path | None = None) -> str:
    """단독 Core 버전은 확정 표시, 실제 배포 커밋은 검증된 로컬 기록이 있을 때만 표시한다."""
    file_path = info_path or Path(__file__).resolve().parent.parent / '.deploy-info.json'
    lines = ['📦 배포 정보', f'Python Core v{core_version}']
    try:
        # 고정된 로컬 상태 파일만 읽는다. 원격 요청이나 git 명령을 실행하지 않는다.
        if file_path.stat().st_size > 2048:
            raise ValueError('metadata too large')
        meta = json.loads(file_path.read_text(encoding='utf-8'))
        sha = str(meta.get('sha', ''))
        branch = str(meta.get('branch', ''))
        if not re.fullmatch(r'[a-fA-F0-9]{40}', sha):
            raise ValueError('invalid commit hash')
        if not re.fullmatch(r'[A-Za-z0-9_/.-]{1,100}', branch):
            raise ValueError('invalid branch')
        lines.append('배포 커밋: ' + sha[:12])
        lines.append('브랜치: ' + branch)
        lines.append('확인 시각: ' + str(meta.get('deployed_at', '미기록'))[:32])
        if meta.get('android_updated') is True:
            lines.append('Android APK: 동일 배포에서 설치 요청·패키지 확인 완료')
        else:
            lines.append('Android APK: 이 배포에서는 업데이트 미수행')
    except (OSError, ValueError, TypeError, json.JSONDecodeError, AttributeError):
        lines.append('배포 커밋: 미기록 (기존 배포 또는 기록 없음)')
    lines.append('※ Android 앱 버전은 카톡 단축어 상에서 확인')
    return '\n'.join(lines)


def recent_command_log(db: sqlite3.Connection, room: str, sender: str) -> str:
    """정확한 채팅방/발신자의 명령 결과 상태만 표시; 인수·결과·비밀·타인 로그 제외."""
    if not room.strip() or not sender.strip():
        return '⚠️ 로그 조회에 채팅방/발신자 정보가 필요합니다.'
    rows = db.execute('''SELECT created_at,command,ok FROM jobs
        WHERE room=? AND sender=? ORDER BY rowid DESC LIMIT 6''',
        (room, sender)).fetchall()
    if not rows:
        return '📜 최근 실행 로그가 없습니다. (현재 대화)'
    lines = ['📜 최근 명령 로그 (현재 대화)']
    for created, cmd, ok in rows:
        stamp = datetime.fromtimestamp(int(created), tz=KST).strftime('%m/%d %H:%M')
        # 명령어 필드도 혹시 모를 줄바꿈을 제거해 24자로 제한한다.
        safe_cmd = ' '.join(str(cmd).split())[:24]
        lines.append(f"{stamp} {'✅' if ok else '⚠️'} {safe_cmd}")
    lines.append('※ 명령 인수·질문 원문·토큰 미표시')
    return '\n'.join(lines)


def configuration_report(ai_status: str, *, menu_ttl_seconds: int = 300) -> str:
    """API 키 또는 환경변수 원문 없이 안전한 설정 상태만 보여준다."""
    return ('🔧 설정 현황 (읽기 전용)\n'
            f'메뉴 유효시간: {int(menu_ttl_seconds) // 60}분\n'
            '메뉴 범위: 방·발신자별 분리\n'
            f'{ai_status}\n'
            '※ 권한·비밀키·연결 주소는 미표시\n'
            '※ 설정 변경은 승인된 관리자 경로에서 수행')


def deployment_identity(*, info_path: Path | None = None) -> dict[str, str]:
    """Read the existing deployer's local, non-secret recorded revision, never guessing."""
    path = info_path or Path(__file__).resolve().parent.parent / '.deploy-info.json'
    try:
        if path.stat().st_size > 2048:
            return {'branch': '', 'sha': ''}
        obj = json.loads(path.read_text(encoding='utf-8'))
        sha = str(obj.get('sha', ''))
        branch = str(obj.get('branch', ''))
        if not re.fullmatch(r'[a-fA-F0-9]{40}', sha):
            return {'branch': '', 'sha': ''}
        if not re.fullmatch(r'[A-Za-z0-9_/.-]{1,100}', branch):
            return {'branch': '', 'sha': ''}
        return {'branch': branch, 'sha': sha}
    except (OSError, ValueError, TypeError, AttributeError, json.JSONDecodeError):
        return {'branch': '', 'sha': ''}
