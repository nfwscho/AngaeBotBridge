#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 v0.2.1 서비스 재개: 기능 상세 주석
# 1. runit 서비스 데몬을 활성화하고 FastAPI 서비스를 재개한다.
# 2. watchdog 서비스를 함께 재개해 자동 복구 기능을 살린다.
# 3. 기존 .env/SQLite DB/로그와 Android 앱 설정은 유지한다.
set -euo pipefail
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export SVDIR="$PREFIX/var/service" LOGDIR="$PREFIX/var/log"
if [ -f "$PREFIX/etc/profile.d/start-services.sh" ]; then
    . "$PREFIX/etc/profile.d/start-services.sh"
fi
sleep 2
sv-enable angaebot-core
sv-enable angaebot-watchdog
echo '[OK] Services enabled'
