#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 v0.3.1 선택형 부팅 안정화 설치기 — 모든 기능 상세 설명
# 1. 기존 카카오톡/Android 앱, 자동응답 설정, SQLite와 인증 토큰을 변경하지 않는다.
# 2. v0.2.1의 Termux/Google Play 부팅 경로 ~/.termux/boot/10-angaebot-services를 유지한다.
# 3. 설치 전 기존 부팅 스크립트를 날짜 이름으로 전체 백업하며 자동 삭제하지 않는다.
# 4. 기존 termux-wake-lock 요청과 runit start-services.sh 호출을 보존한다.
# 5. 실행 시각/SSH 상태/각 runit 서비스를 logs/boot.log에 누적 기록한다.
# 6. 부팅 시 runit sshd 서비스가 있다면 그것만 활성화해 직접 sshd와의 중복을 차단한다.
# 7. runit sshd 서비스가 없는 경우에만 기존 직접 sshd 실행 방식으로 돌아간다.
# 8. 중지된 core/watchdog의 down 파일을 존중하고 부팅 시 임의로 켜지 않는다.
# 9. 설치 즉시 SSH/서버를 재시작하지 않아 현재 원격 SSH 연결을 끊지 않는다.
# 10. 부팅 앱이 시스템에 의해 시작되지 않는 경우를 우회한다고 보장하지 않는다.
set -euo pipefail
CORE="$(cd "$(dirname "$0")/.." && pwd)"
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
if [ ! -d "$PREFIX/var/service" ]; then
    echo '[ERROR] Termux runit service directory not found' >&2
    exit 1
fi
if [ ! -f "$CORE/.env" ]; then
    echo '[ERROR] Existing core .env missing; install v0.2 core first' >&2
    exit 1
fi
umask 077
BOOTDIR="$HOME/.termux/boot"
BACKUPDIR="$HOME/.termux/boot-legacy-backup"
mkdir -p "$BOOTDIR" "$BACKUPDIR" "$CORE/logs"
chmod 700 "$BOOTDIR" "$BACKUPDIR"
BOOT="$BOOTDIR/10-angaebot-services"
if [ -f "$BOOT" ]; then
    cp -p "$BOOT" "$BACKUPDIR/10-angaebot-services.before-v031.$(date +%Y%m%d_%H%M%S_%N)"
fi
cat > "$BOOT" <<'BOOT_SCRIPT'
#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 v0.3.1 부팅 스크립트 — Wake Lock, SSH, Core/Watchdog, 로그 기능 상세
# 1. 기존 runit 서비스/부팅 경로 사용. 2. 동일 SSH 서비스 두 번 실행하지 않음.
# 3. core/watchdog의 사용자 비활성화 상태 존중. 4. boot.log 누적 기록.
# 5. .env/SQLite/과거 로그 보존. 6. Android 실행 여부는 실제 재부팅 검증 필요.
export PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export HOME="${HOME:-/data/data/com.termux/files/home}"
export PATH="$PREFIX/bin:$PATH"
export SVDIR="$PREFIX/var/service" LOGDIR="$PREFIX/var/log"
export CORE="$HOME/angaebot/core"
umask 077
mkdir -p "$CORE/logs"
exec >> "$CORE/logs/boot.log" 2>&1
echo "BOOT_STARTED $(date -Iseconds)"
if command -v termux-wake-lock >/dev/null 2>&1; then
    termux-wake-lock || echo 'BOOT_WAKE_LOCK_UNAVAILABLE'
fi
if [ -f "$PREFIX/etc/profile.d/start-services.sh" ]; then
    . "$PREFIX/etc/profile.d/start-services.sh" || echo 'BOOT_RUNSVDIR_INIT_FAILED'
else
    echo 'BOOT_RUNSVDIR_INIT_SCRIPT_MISSING'
fi
sleep 2
if [ -f "$SVDIR/sshd/run" ]; then
    # 수동 실행 sshd 대신 runit 단독 관리: 기존 수동 daemon과 포트 충돌 방지.
    if command -v sv-enable >/dev/null 2>&1; then
        sv-enable sshd || echo 'BOOT_SSHD_ENABLE_FAILED'
    fi
    if command -v sv >/dev/null 2>&1; then
        sv -w 5 up "$SVDIR/sshd" || echo 'BOOT_SSHD_UP_FAILED'
        sv status "$SVDIR/sshd" || :
    fi
elif command -v sshd >/dev/null 2>&1; then
    if ! pgrep -x sshd >/dev/null 2>&1; then
        sshd || echo 'BOOT_SSHD_MANUAL_FAILED'
    fi
else
    echo 'BOOT_SSHD_BINARY_MISSING'
fi
for service in angaebot-core angaebot-watchdog; do
    if [ -f "$SVDIR/$service/run" ]; then
        if [ ! -e "$SVDIR/$service/down" ]; then
            sv -w 5 up "$SVDIR/$service" || echo "BOOT_SERVICE_UP_FAILED name=$service"
        else
            echo "BOOT_SERVICE_DISABLED name=$service"
        fi
        sv status "$SVDIR/$service" || :
    else
        echo "BOOT_SERVICE_NOT_INSTALLED name=$service"
    fi
done
echo "BOOT_FINISHED $(date -Iseconds)"
BOOT_SCRIPT
chmod 700 "$BOOT"
echo '[OK] v0.3.1 부팅 스크립트 설치 완료. 기존 스크립트는 백업.'
echo '[INFO] 현재 SSH/서버는 재시작하지 않았습니다.'
echo '[INFO] 진단: .venv/bin/python scripts/diagnose-autostart.py'
echo '[INFO] 실제 부팅 성공 여부는 다음 재부팅에서 확인할 수 있습니다.'
