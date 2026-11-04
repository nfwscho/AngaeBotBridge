#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 v0.2.1 자동 시작 설치: 전체 기능 상세 설명
# 1. 기존 Android 앱/UI/알림/SQLite 로그는 전혀 변경하지 않는다.
# 2. 기존 core/.env, .venv, data/, logs/ 파일을 읽거나 재사용하며 삭제·덮어쓰지 않는다.
# 3. termux-services/runit로 FastAPI 프로세스 자동 재시작을 구성한다.
# 4. 별도 runit watchdog으로 인증된 health API 응답을 30초마다 검사한다.
# 5. 응답이 3회 연속 실패하면 서비스를 재시작한다(비정상 종료 외 멈춤 대응).
# 6. Google Play Termux 내장 부팅 기능용 ~/.termux/boot 스크립트를 생성한다.
# 7. 부팅 후 SSH와 runit 서비스를 다시 시작하며 로그를 유지한다.
# 8. 설치를 반복해도 기존 token/DB/logs를 보존하고 이전 run 스크립트는 백업한다.
set -euo pipefail
CORE="$(cd "$(dirname "$0")/.." && pwd)"
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export PREFIX
SERVICES="$PREFIX/var/service"
export SVDIR="$SERVICES" LOGDIR="$PREFIX/var/log"

if [ ! -f "$CORE/.env" ] || [ ! -x "$CORE/.venv/bin/python" ]; then
    echo '[ERROR] Python Core가 준비되지 않았습니다: core에서 bash scripts/install-termux.sh 먼저 실행'
    exit 1
fi
if [ ! -f "$CORE/app/main.py" ]; then
    echo '[ERROR] core/app/main.py가 없습니다. 기존 Python Core 파일을 먼저 설치하세요.'
    exit 1
fi
if ! "$CORE/.venv/bin/python" -c 'import fastapi, uvicorn' >/dev/null 2>&1; then
    echo '[ERROR] FastAPI/Uvicorn이 설치되지 않았습니다. core에서 bash scripts/install-termux.sh 실행'
    exit 1
fi
if ! command -v pkg >/dev/null 2>&1; then
    echo '[ERROR] Termux 내부에서 실행하세요.'; exit 1
fi
pkg install -y termux-services openssh
if ! command -v sv >/dev/null 2>&1; then
    echo '[ERROR] runit/termux-services 설치를 확인하세요.'; exit 1
fi
mkdir -p "$SERVICES/angaebot-core" "$SERVICES/angaebot-watchdog" "$CORE/logs" "$HOME/.termux/boot" "$HOME/.termux/boot-legacy-backup"
chmod 700 "$HOME/.termux/boot" "$HOME/.termux/boot-legacy-backup"
# v0.2.0의 직접 실행 boot 스크립트가 있으면 새 서비스와 충돌한다.
# 삭제하지 않고 부팅 디렉터리 밖으로 이동해 보존한다.
LEGACY="$HOME/.termux/boot/angaebot-core"
if [ -f "$LEGACY" ]; then
    mv "$LEGACY" "$HOME/.termux/boot-legacy-backup/angaebot-core.$(date +%Y%m%d%H%M%S)"
    echo '[INFO] v0.2.0 boot script saved to ~/.termux/boot-legacy-backup/'
fi
# 신규 서비스가 설정 중 실행되는 것을 방지한다.
for name in angaebot-core angaebot-watchdog; do
    dir="$SERVICES/$name"
    if [ -f "$dir/run" ]; then
        cp -p "$dir/run" "$dir/run.backup.$(date +%Y%m%d%H%M%S)"
    fi
done
# 단일 프로세스 감시: core 실행 래퍼는 최종적으로 exec uvicorn을 수행한다.
{
    echo '#!/data/data/com.termux/files/usr/bin/bash'
    echo '# AngaeBot core runit service. 기존 DB/로그 유지.'
    printf 'exec /data/data/com.termux/files/usr/bin/bash %q\n' "$CORE/scripts/start-termux.sh"
} > "$SERVICES/angaebot-core/run"
{
    echo '#!/data/data/com.termux/files/usr/bin/bash'
    echo '# AngaeBot authenticated health watchdog; logs/watchdog.log 누적.'
    printf 'exec %q %q\n' "$CORE/.venv/bin/python" "$CORE/scripts/health_watchdog.py"
} > "$SERVICES/angaebot-watchdog/run"
chmod 700 "$SERVICES/angaebot-core/run" "$SERVICES/angaebot-watchdog/run"

BOOT="$HOME/.termux/boot/10-angaebot-services"
if [ -f "$BOOT" ]; then
    cp -p "$BOOT" "$HOME/.termux/boot-legacy-backup/10-angaebot-services.$(date +%Y%m%d%H%M%S)"
fi
# 모든 장치에서 동일한 Termux 표준 경로를 사용한다.
cat > "$BOOT" <<'SCRIPT'
#!/data/data/com.termux/files/usr/bin/bash
# AngaeBot boot script: Wake Lock, SSH and runit supervisor; .env/SQLite/logs 보존.
export PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export HOME="${HOME:-/data/data/com.termux/files/home}"
export PATH="$PREFIX/bin:$PATH"
export SVDIR="$PREFIX/var/service" LOGDIR="$PREFIX/var/log"
if command -v termux-wake-lock >/dev/null 2>&1; then termux-wake-lock || :; fi
if command -v sshd >/dev/null 2>&1 && ! pgrep -x sshd >/dev/null 2>&1; then sshd || :; fi
if [ -f "$PREFIX/etc/profile.d/start-services.sh" ]; then
    . "$PREFIX/etc/profile.d/start-services.sh"
fi
SCRIPT
chmod 700 "$BOOT"
# 기존 터미널 세션의 서비스 데몬이 아직 작동하지 않을 수 있어 즉시 시작한다.
if [ -f "$PREFIX/etc/profile.d/start-services.sh" ]; then
    . "$PREFIX/etc/profile.d/start-services.sh"
fi
sleep 2
sv-enable angaebot-core
sv-enable angaebot-watchdog
printf '\n[OK] AngaeBot Core 자동 복구 서비스 등록 완료\n'
printf '  Service: %s\n' "$SERVICES/angaebot-core"
printf '  Watchdog: %s\n' "$SERVICES/angaebot-watchdog"
printf '  Boot: %s\n' "$BOOT"
echo '  확인: bash scripts/status-autostart.sh'
echo '  Google Play Termux는 부팅 지원 내장. 재부팅 후 실제 실행 여부는 반드시 검증하세요.'
