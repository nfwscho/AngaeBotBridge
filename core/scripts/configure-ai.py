"""
앙개봇 v0.3.0 Termux AI 설정 관리기 — 전체 기능 상세 설명
1. 기존 .env의 ANGAE_TOKEN과 다른 Python/Android 관련 환경변수를 수정·삭제하지 않는다.
2. OpenAI 클라우드 API와 Ollama(미니PC/LAN) 호환 API 중 하나를 선택한다.
3. API 인증키는 getpass()로 화면에 노출하지 않고 .env(0600)에만 기록한다.
4. AI 기능은 사용자의 명시적 설정 전까지 OFF이며, --disable로 즉시 설정을 OFF로 전환한다.
5. .env 설정 변경 시 민감정보가 포함된 백업 파일을 권한 0600으로 보관한다.
6. AI 제공자/모델/주소/타임아웃/문맥 보존 설정을 검증하고 비밀키는 출력하지 않는다.
7. 기존 데이터베이스·명령 이력·runit/SSH/부팅 스크립트·서버 로그를 건드리지 않는다.
8. 설정 적용은 현재 실행 중인 FastAPI 프로세스를 재시작한 뒤부터 유효하다.
9. --status로 키를 출력하지 않고 현재 AI 설정만 확인할 수 있다.
10. 직접 셸/파일 원격제어 기능이나 모델 자동 다운로드는 포함하지 않는다.
"""
from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"
NAMES = ("ANGAE_AI_ENABLED", "ANGAE_AI_PROVIDER", "ANGAE_AI_BASE_URL", "ANGAE_AI_MODEL",
         "ANGAE_AI_API_KEY", "ANGAE_AI_TIMEOUT", "ANGAE_AI_MEMORY_ENABLED", "ANGAE_AI_CONTEXT_TURNS")


def read_env() -> dict[str, str]:
    from shlex import split
    result: dict[str, str] = {}
    if ENV.exists():
        for line in ENV.read_text(encoding="utf-8").splitlines():
            if not line or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, raw = line.split("=", 1)
            try:
                parts = split(raw, comments=False)
                if len(parts) == 1:
                    result[key.strip()] = parts[0]
                elif raw.strip() == "":
                    result[key.strip()] = ""
            except ValueError:
                continue
    return result


def patch_env(updates: dict[str, str]) -> None:
    if not ENV.exists():
        raise RuntimeError(".env가 없습니다. 먼저 기존 core/scripts/install-termux.sh를 실행하세요.")
    old = ENV.read_text(encoding="utf-8")
    lines = old.splitlines(keepends=True)
    result: list[str] = []
    updated = set()
    for line in lines:
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=", line)
        if match and match.group(1) in updates:
            key = match.group(1)
            if key not in updated:
                result.append(key + "=" + shlex.quote(updates[key]) + "\n")
                updated.add(key)
        else:
            result.append(line)
    if result and not result[-1].endswith("\n"):
        result.append("\n")
    for key, value in updates.items():
        if key not in updated:
            result.append(key + "=" + shlex.quote(value) + "\n")
    backup = ROOT / (".env.backup." + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    shutil.copy2(ENV, backup)
    os.chmod(backup, 0o600)
    fd, tmp = tempfile.mkstemp(prefix=".env.tmp.", dir=ROOT)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.writelines(result)
        os.replace(tmp, ENV)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    print("[OK] AI 설정을 저장했습니다. 기존 인증키/DB/로그 유지. 백업:", backup.name)
    print("[INFO] 적용하려면: bash scripts/restart-autostart.sh")


def prompt(label: str, default: str) -> str:
    data = input(f"{label} [{default}]: ").strip()
    return data or default


def run() -> None:
    parser = argparse.ArgumentParser(description="AngaeBot AI provider setup; keys are never printed")
    parser.add_argument("--status", action="store_true", help="설정 상태(키 제외) 출력")
    parser.add_argument("--disable", action="store_true", help="AI 기능 OFF")
    args = parser.parse_args()
    values = read_env()
    if args.status:
        print("AI 상태:", "ON" if values.get("ANGAE_AI_ENABLED") == "1" else "OFF")
        print("제공자:", values.get("ANGAE_AI_PROVIDER", "미설정"))
        print("모델:", values.get("ANGAE_AI_MODEL", "미설정"))
        print("주소:", values.get("ANGAE_AI_BASE_URL", "미설정"))
        print("대화 문맥:", values.get("ANGAE_AI_MEMORY_ENABLED", "1"))
        print("API 키:", "설정됨" if values.get("ANGAE_AI_API_KEY") else "없음")
        return
    if args.disable:
        patch_env({"ANGAE_AI_ENABLED": "0"})
        return
    print("\n=== AngaeBot AI v0.3.0 (키/토큰은 채팅이나 GitHub에 올리지 마세요) ===")
    provider = prompt("제공자(openai / ollama)", values.get("ANGAE_AI_PROVIDER", "openai")).lower()
    if provider not in ("openai", "ollama"):
        raise ValueError("제공자는 openai 또는 ollama입니다.")
    default_base = "https://api.openai.com/v1" if provider == "openai" else "http://10.1.1.100:11434/v1"
    default_model = "gpt-6-luna" if provider == "openai" else "llama3.2:3b"
    base = prompt("AI 서버 주소 (Ollama라면 실제 미니PC IP로 변경)", values.get("ANGAE_AI_BASE_URL", default_base))
    model = prompt("AI 모델명", values.get("ANGAE_AI_MODEL", default_model))
    timeout = prompt("AI 최대 응답 대기(초; 3~23)", values.get("ANGAE_AI_TIMEOUT", "15"))
    memory = prompt("최근 대화 문맥 저장 (1=ON,0=OFF)", values.get("ANGAE_AI_MEMORY_ENABLED", "1"))
    turns = prompt("문맥 반영 대화 횟수 (0~10)", values.get("ANGAE_AI_CONTEXT_TURNS", "6"))
    updates = {"ANGAE_AI_ENABLED": "1", "ANGAE_AI_PROVIDER": provider,
               "ANGAE_AI_BASE_URL": base, "ANGAE_AI_MODEL": model,
               "ANGAE_AI_TIMEOUT": timeout, "ANGAE_AI_MEMORY_ENABLED": memory,
               "ANGAE_AI_CONTEXT_TURNS": turns}
    if provider == "openai":
        from getpass import getpass
        new_key = getpass("OpenAI API 키 입력 (기존 키 유지하려면 Enter): ").strip()
        old_key = values.get("ANGAE_AI_API_KEY", "")
        if not (new_key or old_key):
            raise ValueError("OpenAI API 키를 입력해야 합니다. ChatGPT 구독과 API 결제는 별개입니다.")
        updates["ANGAE_AI_API_KEY"] = new_key or old_key
    # 저장하기 전에 AISettings의 모든 URL/형식 검사를 통과해야 한다.
    sys.path.insert(0, str(ROOT))
    from app.ai_engine import AISettings
    check = AISettings(enabled=True, provider=provider, base_url=base, model=model,
                       api_key=updates.get("ANGAE_AI_API_KEY", values.get("ANGAE_AI_API_KEY", "")),
                       timeout=int(timeout), memory_enabled=memory == "1", context_turns=int(turns))
    if memory not in ("0", "1"):
        raise ValueError("문맥 설정은 0 또는 1이어야 합니다.")
    check.endpoint()
    patch_env(updates)


if __name__ == "__main__":
    try:
        run()
    except (ValueError, RuntimeError, KeyboardInterrupt) as error:
        print("[ERROR]", str(error), file=sys.stderr)
        sys.exit(1)
