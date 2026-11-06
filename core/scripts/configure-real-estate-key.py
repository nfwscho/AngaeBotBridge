"""
앙개봇 국토교통부 실거래가 인증키 비공개 설정기 — 기능 전체 명세
1. Galaxy S20+ Termux에서 사용 중인 core/.env 파일을 검증하고 기존 내용을 보존한다.
2. 입력받은 MOLIT_API_KEY만 추가 또는 수정하며 ANGAE_TOKEN·AI 설정·다른 키를 바꾸지 않는다.
3. 키는 stdin으로만 전달받고 화면·로그·프로세스 인수·GitHub 소스에 기록하거나 출력하지 않는다.
4. 서비스키는 공공데이터포털 인코딩/디코딩 형식을 허용하고 길이·문자 집합을 검증한다.
5. 기존 MOLIT_API_KEY 항목이 중복이면 하나로 합쳐 최초 위치를 유지한다.
6. 다른 환경변수/코멘트/빈 줄과 기존 줄바꿈을 가능한 한 그대로 보존한다.
7. .env 파일이 없거나 심볼릭 링크면 생성·덮어쓰지 않고 거부한다.
8. 원본 권한보다 느슨해지지 않게 임시 파일을 0600으로 만들고 fsync/원자적 교체로 저장한다.
9. 쓰기 오류 시 임시 파일을 정리하고 기존 .env를 유지하며 삭제·초기화하지 않는다.
10. 개인 DB·SQLite jobs/events·Android Bridge·watchdog·SSH·로그 파일에는 접근하지 않는다.
11. 이 파일에는 인증키 값이 전혀 없으며 GitHub에 커밋해도 인증키가 노출되지 않는다.
12. 테스트는 임시 .env와 가짜 키로 수행하고 운영 S20+나 외부 API에 접속하지 않는다.
"""
from __future__ import annotations

import os
import re
import stat
import sys
import tempfile
from pathlib import Path

KEY_NAME = "MOLIT_API_KEY"
KEY_PATTERN = re.compile(r"[A-Za-z0-9%+/=_-]{16,500}\Z")


class KeyConfigurationError(ValueError):
    """Key validation or safe configuration update failed."""


def configure_env(env_file: Path, service_key: str) -> None:
    """Only update the service-key entry; never disclose its value."""
    if not isinstance(service_key, str) or not KEY_PATTERN.fullmatch(service_key):
        raise KeyConfigurationError("서비스키 형식이 잘못되었습니다.")
    path = Path(env_file)
    if path.is_symlink() or not path.is_file():
        raise KeyConfigurationError("기존 core/.env 파일을 확인할 수 없습니다.")
    if not stat.S_ISREG(path.stat().st_mode):
        raise KeyConfigurationError("기존 .env 파일은 일반 파일이어야 합니다.")
    try:
        with path.open("r", encoding="utf-8", newline="") as stream:
            original = stream.read()
    except (OSError, UnicodeError) as exc:
        raise KeyConfigurationError("기존 .env 파일을 안전하게 읽지 못했습니다.") from None

    newline = "\r\n" if "\r\n" in original else "\n"
    lines = original.splitlines(keepends=True)
    new_lines: list[str] = []
    updated = False
    for line in lines:
        # Explicit KEY= format is expected by the existing start-termux.sh loader.
        if re.match(r"^\s*MOLIT_API_KEY=", line):
            if not updated:
                line_break = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
                new_lines.append(f"{KEY_NAME}={service_key}{line_break}")
                updated = True
            continue
        new_lines.append(line)
    if not updated:
        if new_lines and not new_lines[-1].endswith(("\r", "\n")):
            new_lines.append(newline)
        new_lines.append(f"{KEY_NAME}={service_key}{newline}")
    new_content = "".join(new_lines)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="", dir=str(path.parent),
            prefix=".env.molit-", delete=False
        ) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            stream.write(new_content)
            stream.flush()
            os.fsync(stream.fileno())
        # No existing .env permission is widened. Owner read/write only.
        os.replace(temporary, path)
        temporary = None
    except OSError:
        raise KeyConfigurationError(".env 파일을 안전하게 저장하지 못했습니다.") from None
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def main() -> int:
    # Remote staging copies this script directly into core/, beside the existing .env.
    env_file = Path(__file__).resolve().parent / ".env"
    try:
        # A single stdin line; reject unexpected multi-line or overlong values.
        received = sys.stdin.read(1024).rstrip("\r\n")
        configure_env(env_file, received)
    except KeyConfigurationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print("OK: MOLIT_API_KEY configured in private .env (key not displayed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
