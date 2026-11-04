#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 Python Core v0.3.1 — 모든 실행·보안·로그 기능 상세 안내
# 1. 기존 .env의 ANGAE_TOKEN/AI 설정을 읽고 변경하거나 로그에 출력하지 않는다.
# 2. 기존 .venv Python을 그대로 사용해 FastAPI 서버를 127.0.0.1:8765에서 실행한다.
# 3. 기존 계산/시간/서버상태/AI 명령, JSON 응답, SQLite DB/로그를 유지한다.
# 4. logs/server.log의 stdout/stderr 보존, 8 MiB 이상이면 서버 시작 직전에 아카이브한다.
# 5. run_core.py의 POSIX flock으로 단일 프로세스 실행, 중복 포트 실행을 차단한다.
# 6. exec로 runit이 프로세스를 감시하게 하며 수동 실행 호환성을 유지한다.
# 7. Android Bridge UI, 카톡 알림, RemoteInput 답장, SSH/부팅 서비스는 변경하지 않는다.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then echo 'ERROR: bash scripts/install-termux.sh first'; exit 1; fi
if [ ! -x .venv/bin/python ]; then echo 'ERROR: .venv/bin/python not found; run scripts/install-termux.sh'; exit 1; fi
if [ ! -f scripts/run_core.py ]; then echo 'ERROR: scripts/run_core.py missing'; exit 1; fi
set -a
# 기존 설치기 .env 형식 유지. 비밀키는 stdout에 출력하지 않는다.
. ./.env
set +a
mkdir -p logs data
umask 077
exec .venv/bin/python scripts/run_core.py
