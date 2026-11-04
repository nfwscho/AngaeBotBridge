#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# AngaeBot Python Core v0.2.2 — Termux 설치 및 복구 기능 전체 설명
# 1. Galaxy S20+ Termux에서 기존 FastAPI Python Core 실행환경을 설치/복구한다.
# 2. 기존 core/app/*.py 명령 처리, 토큰 인증, SQLite 중복실행 방지 기능은 변경하지 않는다.
# 3. 기존 Android Bridge UI, 카톡 수신/답장, Kotlin 로그 처리 기능은 변경하지 않는다.
# 4. 기존 .venv는 재사용한다. 기존 .env 인증키, data/*.db 및 logs/*를 삭제하지 않는다.
# 5. Android/Termux에는 일반 PyPI의 pydantic-core wheel이 없을 수 있으므로
#    Termux User Repository PyPI의 Android용 사전 빌드 wheel을 우선 설치한다.
# 6. Python 3.13 / Android ARM64에서 확인된 호환 버전
#    pydantic==2.12.5, pydantic-core==2.41.5를 constraints-termux.txt에 고정한다.
# 7. --only-binary=:all:로 Rust/maturin의 예기치 않은 소스 빌드를 방지한다.
# 8. FastAPI/Uvicorn 및 기타 Python 의존성을 설치하고 pip check/import로 검증한다.
# 9. .env 파일이 없을 때에만 안전한 랜덤 인증키를 생성하여 0600 권한으로 저장한다.
# 10. SQLite 데이터 및 서버 로그 폴더를 유지하며 기존 수동/자동 시작 스크립트와 호환된다.
# 11. 설치 실패 시 원인별 설명을 표시하고 서버 자체나 기존 설정은 삭제하지 않는다.
# ============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v pkg >/dev/null 2>&1; then
    echo '[ERROR] Termux 내부에서 실행해야 합니다.' >&2
    exit 1
fi

pkg update
pkg install -y python python-pip

if [ ! -x .venv/bin/python ]; then
    if [ -e .venv ]; then
        echo '[ERROR] .venv가 존재하지만 실행 가능한 Python이 없습니다. 기존 파일은 보존했습니다.' >&2
        exit 1
    fi
    python -m venv .venv
fi

# Pydantic 2.12.5는 pydantic-core 2.41.5를 요구한다.
# Android 아키텍처용 wheel이 없으면 실패시키며 자동 Rust 빌드를 하지 않는다.
CORE_INDEX='https://termux-user-repository.github.io/pypi/'
if ! .venv/bin/python -m pip install \
    --no-deps \
    --only-binary=:all: \
    --index-url "$CORE_INDEX" \
    'pydantic-core==2.41.5'; then
    echo '[ERROR] Android용 pydantic-core==2.41.5 wheel을 찾지 못했습니다.' >&2
    echo '[INFO] Python 버전/아키텍처 확인: .venv/bin/python --version; uname -m' >&2
    echo '[INFO] Termux용 wheel 저장소와 Python 버전 호환성을 확인하세요.' >&2
    exit 1
fi

if ! .venv/bin/python -m pip install \
    --only-binary=:all: \
    -c constraints-termux.txt \
    -r requirements.txt; then
    echo '[ERROR] FastAPI/Pydantic/Uvicorn 패키지 설치 실패.' >&2
    echo '[INFO] 기존 .env, SQLite, 로그, Android 앱은 보존되었습니다.' >&2
    exit 1
fi

if ! .venv/bin/python -m pip check; then
    echo '[ERROR] Python 패키지 의존성 검증 실패.' >&2
    exit 1
fi

if ! .venv/bin/python -c 'import fastapi, uvicorn, pydantic, pydantic_core; assert pydantic.__version__ == "2.12.5"; assert pydantic_core.__version__ == "2.41.5"; print("[OK] FastAPI:", fastapi.__version__, "Pydantic:", pydantic.__version__, "pydantic-core:", pydantic_core.__version__)'; then
    echo '[ERROR] 모듈 import/버전 확인 실패; Android용 바이너리 호환성을 확인하세요.' >&2
    exit 1
fi

if [ ! -f .env ]; then
    umask 077
    ANGAE_TOKEN="$(.venv/bin/python -c 'import secrets; print(secrets.token_hex(32))')"
    printf 'ANGAE_TOKEN=%s\n' "$ANGAE_TOKEN" > .env
    chmod 600 .env
    unset ANGAE_TOKEN
fi

mkdir -p data logs
chmod 700 data logs
printf '\n[OK] AngaeBot Python Core Termux dependencies installed (v0.2.2).\n'
echo 'Run: bash scripts/start-termux.sh'
echo 'Autostart (if v0.2.1 service installed): bash scripts/status-autostart.sh'
echo 'Never upload .env or paste the token into chats/logs.'
