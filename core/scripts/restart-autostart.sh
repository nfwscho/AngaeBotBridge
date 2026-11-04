#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 v0.2.1 FastAPI 수동 재시작: 기능 상세 주석
# 1. termux-services/runit가 관리하는 angaebot-core에만 재시작을 요청한다.
# 2. watchdog 관리 서비스와 SSH, Android 앱/UI/로그를 건드리지 않는다.
# 3. 기존 .env, SQLite DB, 모든 로그는 그대로 유지된다.
set -euo pipefail
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export SVDIR="$PREFIX/var/service" LOGDIR="$PREFIX/var/log"
sv restart "$SVDIR/angaebot-core"
echo '[OK] Restart requested. bash scripts/status-autostart.sh 로 확인'
