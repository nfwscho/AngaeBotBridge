#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 v0.2.1 서비스 진단: 기능 상세 주석
# 1. 기존 runit core/watchdog 상태를 각각 출력한다.
# 2. 로컬 FastAPI의 토큰 인증 health 조회를 수행하며 토큰 값을 출력하지 않는다.
# 3. 기존 server.log와 watchdog.log의 마지막 8줄만 출력한다.
# 4. 명령어 실행만으로 인증키, DB, 로그, 설정을 수정·삭제하지 않는다.
set -u
CORE="$(cd "$(dirname "$0")/.." && pwd)"
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export SVDIR="$PREFIX/var/service" LOGDIR="$PREFIX/var/log"
for service in angaebot-core angaebot-watchdog; do
    if [ -d "$SVDIR/$service" ]; then
        sv status "$SVDIR/$service" || :
    else
        echo "[NOT INSTALLED] $service"
    fi
done
if [ -x "$CORE/.venv/bin/python" ] && [ -f "$CORE/.env" ]; then
    "$CORE/.venv/bin/python" "$CORE/scripts/check-health.py"
fi
echo '최근 로그:'
tail -n 8 "$CORE/logs/server.log" 2>/dev/null || :
tail -n 8 "$CORE/logs/watchdog.log" 2>/dev/null || :
