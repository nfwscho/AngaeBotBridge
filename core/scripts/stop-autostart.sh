#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 v0.2.1 서비스 중지: 기능 상세 주석
# 1. 재시작 루프를 피하기 위해 watchdog부터 중지한다.
# 2. 이어 FastAPI 서비스를 중지하고 자동 실행도 일시 비활성화한다.
# 3. SSH 및 Android 앱은 중지하지 않는다.
# 4. 토큰/SQLite DB/로그/서비스 스크립트를 보존한다.
set -euo pipefail
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export SVDIR="$PREFIX/var/service" LOGDIR="$PREFIX/var/log"
sv-disable angaebot-watchdog
sv-disable angaebot-core
echo '[OK] Both services stopped; bash scripts/resume-autostart.sh 로 재시작'
