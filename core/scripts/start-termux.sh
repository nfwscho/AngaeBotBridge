#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 Python Core v0.2.1: 전체 기능 안내
# 1. 기존 .env 인증키와 data/*.db, logs/server.log를 변경·삭제하지 않는다.
# 2. FastAPI 앱의 계산/시간/서버상태 API와 로컬 토큰 인증을 그대로 사용한다.
# 3. 서버는 오직 127.0.0.1:8765에만 바인딩한다(외부 포트 개방 없음).
# 4. stdout/stderr는 기존 logs/server.log 파일에 누적 기록한다.
# 5. uvicorn을 exec로 직접 실행하여 runit이 정확한 프로세스를 감시·재시작하도록 한다.
# 6. 기존 수동 실행(bash scripts/start-termux.sh)도 계속 지원한다.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then echo 'ERROR: bash scripts/install-termux.sh first'; exit 1; fi
if [ ! -x .venv/bin/python ]; then echo 'ERROR: .venv/bin/python not found; run scripts/install-termux.sh'; exit 1; fi
set -a
# .env는 기존 설치 스크립트에서 발급한 형식. 비밀키를 로그에 출력하지 않는다.
. ./.env
set +a
mkdir -p logs data
umask 077
exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --no-access-log >> logs/server.log 2>&1
