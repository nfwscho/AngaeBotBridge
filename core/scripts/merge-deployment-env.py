"""
앙개봇 Windows .env → Galaxy S20+ 안전 병합 배포 — 전체 기능 명세
1. Windows .env와 S20+의 core/.env를 비교해 필요한 환경변수만 병합한다.
2. Windows KEY=VALUE/export KEY=VALUE 항목은 기존값을 갱신하고 새 항목은 끝에 추가한다.
3. S20+ 기존 전용 환경변수·주석·빈 줄은 삭제하거나 초기화하지 않는다.
4. Android Bridge 인증 토큰 ANGAE_TOKEN은 Windows 값으로 덮어쓰지 않는다.
5. S20+에 기존 ANGAE_TOKEN이 없으면 인증 연결 보호를 위해 작업을 거부한다.
6. 인증키·변수값을 GitHub, SSH 인수, 프로그램 출력, 로그에 기록하지 않는다.
7. Windows UTF-8 BOM/CRLF를 처리해 POSIX 셸이 읽을 수 있는 설정을 기록한다.
8. 잘못된 변수 선언·중복 키·셸 명령 치환·과도한 파일 크기를 거부한다.
9. 원본 파일 부재·심볼릭 링크·인코딩 오류를 사전에 거부한다.
10. 원본 .env를 별도 private 0600 롤백 파일에 백업한 뒤 수정한다.
11. 수정본을 S20+ core 경로의 0600 임시 파일에 작성 후 os.replace로 원자 교체한다.
12. 쓰기 중 오류가 발생하면 원본을 유지하고 남은 임시 파일을 정리한다.
13. 수정 사항이 없으면 원본 .env를 재작성하지 않는다.
14. DB/로그/Android Bridge/UI/watchdog/SSH 프로그램에는 직접 접근하지 않는다.
15. 실제 인증키 없이 가짜 입력값을 사용한 독립적 회귀 테스트가 가능하다.
"""
from __future__ import annotations

import os
import re
import stat
import sys
import tempfile
from pathlib import Path

MAX_ENV_BYTES = 65536
ASSIGNMENT = re.compile(r"^(?:export[ \t]+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
PROTECTED_KEYS = frozenset({"ANGAE_TOKEN"})


class DeploymentEnvError(ValueError):
    """Error messages never include environment variable values."""


def _read_env(path: Path, label: str, *, windows: bool) -> list[str]:
    if path.is_symlink() or not path.is_file():
        raise DeploymentEnvError(f"{label}: .env가 없거나 심볼릭 링크입니다.")
    if not stat.S_ISREG(path.stat().st_mode):
        raise DeploymentEnvError(f"{label}: 일반 파일이 아닙니다.")
    try:
        raw = path.read_bytes()
    except OSError:
        raise DeploymentEnvError(f"{label}: .env 읽기 실패") from None
    if len(raw) > MAX_ENV_BYTES or b"\x00" in raw:
        raise DeploymentEnvError(f"{label}: 잘못된 파일 크기 또는 데이터") from None
    try:
        content = raw.decode("utf-8-sig" if windows else "utf-8")
    except UnicodeError:
        raise DeploymentEnvError(f"{label}: UTF-8 인코딩이 아닙니다.") from None
    if "\r" in content.replace("\r\n", ""):
        raise DeploymentEnvError(f"{label}: 줄바꿈 형식이 잘못되었습니다.")
    if windows:
        content = content.replace("\r\n", "\n")
    return content.splitlines(keepends=True)


def _assignment(line: str, *, strict: bool) -> tuple[str, str] | None:
    trimmed = line.rstrip("\r\n")
    if not trimmed.strip() or trimmed.lstrip().startswith("#"):
        return None
    match = ASSIGNMENT.fullmatch(trimmed)
    if not match:
        if strict:
            raise DeploymentEnvError("Windows .env에 잘못된 변수 선언이 있습니다.")
        return None
    name, value = match.groups()
    if strict and ("$(" in value or chr(96) in value or ("$" + "{") in value):
        raise DeploymentEnvError("Windows .env에 셸 명령/변수 치환 문법이 있습니다.")
    return name, trimmed


def merge_deployment_env(remote: Path, incoming: Path, backup: Path) -> int:
    """Merge settings; return changed assignment count without revealing values."""
    remote, incoming, backup = Path(remote), Path(incoming), Path(backup)
    remote_lines = _read_env(remote, "S20+", windows=False)
    incoming_lines = _read_env(incoming, "Windows", windows=True)
    replacement: dict[str, str] = {}
    for line in incoming_lines:
        parsed = _assignment(line, strict=True)
        if parsed is None:
            continue
        name, declaration = parsed
        if name in replacement:
            raise DeploymentEnvError("Windows .env에 중복된 변수명이 있습니다.")
        replacement[name] = declaration
    if not replacement:
        raise DeploymentEnvError("Windows .env에 적용할 환경변수가 없습니다.")
    existing = {
        parsed[0] for line in remote_lines
        if (parsed := _assignment(line, strict=False)) is not None
    }
    if "ANGAE_TOKEN" not in existing:
        raise DeploymentEnvError("S20+의 기존 ANGAE_TOKEN을 찾을 수 없습니다.")

    newline = "\r\n" if any(line.endswith("\r\n") for line in remote_lines) else "\n"
    updated, processed, result_lines = 0, set(), []
    for line in remote_lines:
        parsed = _assignment(line, strict=False)
        if parsed is None:
            result_lines.append(line)
            continue
        name, _ = parsed
        if name in PROTECTED_KEYS or name not in replacement:
            result_lines.append(line)
            continue
        if name in processed:
            updated += 1
            continue
        processed.add(name)
        new_line = replacement[name] + newline
        updated += int(new_line != line)
        result_lines.append(new_line)
    for name, declaration in replacement.items():
        if name in processed or name in PROTECTED_KEYS:
            continue
        if result_lines and not result_lines[-1].endswith(("\r", "\n")):
            result_lines.append(newline)
        result_lines.append(declaration + newline)
        updated += 1

    new_content = "".join(result_lines)
    original_content = "".join(remote_lines)
    if new_content == original_content:
        return 0
    if backup.is_symlink() or backup.exists():
        raise DeploymentEnvError("기존 롤백 파일은 덮어쓰지 않습니다.")
    if backup.parent.resolve() == remote.parent.resolve():
        raise DeploymentEnvError("롤백 파일의 별도 디렉터리가 필요합니다.")
    temporary: Path | None = None
    try:
        backup.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(backup.parent, 0o700)
        descriptor = os.open(str(backup), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(original_content.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="", dir=str(remote.parent),
            prefix=".env.deployment-", delete=False
        ) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            stream.write(new_content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, remote)
        temporary = None
        return updated
    except OSError:
        raise DeploymentEnvError("S20+ .env의 백업 또는 원자적 저장에 실패했습니다.") from None
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print("ERROR: usage: merge-deployment-env.py REMOTE INCOMING BACKUP", file=sys.stderr)
        return 2
    try:
        count = merge_deployment_env(Path(argv[1]), Path(argv[2]), Path(argv[3]))
    except DeploymentEnvError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: Windows .env securely merged; updated_entries={count}; ANGAE_TOKEN preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
