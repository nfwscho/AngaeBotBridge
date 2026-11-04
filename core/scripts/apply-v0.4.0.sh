#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 v0.4.0 Termux Python Core 배포기 — 전체 구현 기능 상세 설명
# 1. 기존 v0.3.1 FastAPI/watchdog/SSH/부팅 스크립트와 Android UI 및 로그 흐름을 유지한다.
# 2. GitHub에서 Windows가 전달한 main.py, commands.py, ops.py, test_ops.py 파일을 검증한다.
# 3. 기존 소스와 테스트가 있을 때 날짜별 백업을 만들고 파일을 삭제하지 않는다.
# 4. 기존 .env 인증키, SQLite jobs/events/ai_turns, logs, .venv 및 runit 서비스 정의를 보존한다.
# 5. 서버에 적용하기 전 Python 문법 검사와 기존+신규 unittest 회귀 검사를 수행한다.
# 6. 자동 테스트는 임시 DB와 가짜 테스트 토큰만 사용하고 실제 운영 DB를 테스트에 전달하지 않는다.
# 7. 테스트 실패 시 소스만 원래 상태로 복원하고 서버를 재시작하지 않는다.
# 8. 성공 후 기존 restart-autostart.sh로 core만 재시작, watchdog 및 SSH에는 영향이 없다.
# 9. 재시작 후 인증된 health API와 진단 명령으로 운영 상태를 조회한다.
# 10. 모든 실패를 유의미하게 출력하고 기존 로그 및 파일을 자동 삭제하지 않는다.
# 11. Android APK 재설치는 별도로 Windows ADB에서 수행해야 한다.
set -euo pipefail
CORE="${HOME}/angaebot/core"
UPDATE="${HOME}/angaebot/update_v040"
cd "$CORE"

for filename in main.py commands.py ops.py test_ops.py; do
    if [ ! -f "$UPDATE/$filename" ]; then
        echo "[ERROR] update file missing: $filename" >&2
        exit 2
    fi
done
if [ ! -x .venv/bin/python ] || [ ! -f .env ] || [ ! -f scripts/restart-autostart.sh ]; then
    echo '[ERROR] v0.3.1 core/.env/.venv/autostart not ready' >&2
    exit 2
fi

umask 077
STAMP="$(date +%Y%m%d_%H%M%S_%N)"
BACKUP="$HOME/angaebot/backups/core_pre_v040_${STAMP}"
mkdir -p "$BACKUP/app" "$BACKUP/tests"
cp -p app/main.py app/commands.py "$BACKUP/app/"
if [ -f app/ops.py ]; then cp -p app/ops.py "$BACKUP/app/"; fi
if [ -f tests/test_ops.py ]; then cp -p tests/test_ops.py "$BACKUP/tests/"; fi

auto_restore() {
    echo '[ERROR] v0.4.0 검증 실패. 이전 소스 복원 중; 운영 서버/SQLite/로그는 보존됩니다.' >&2
    cp -p "$BACKUP/app/main.py" "$BACKUP/app/commands.py" app/
    if [ -f "$BACKUP/app/ops.py" ]; then cp -p "$BACKUP/app/ops.py" app/; else rm -f app/ops.py; fi
    if [ -f "$BACKUP/tests/test_ops.py" ]; then cp -p "$BACKUP/tests/test_ops.py" tests/; else rm -f tests/test_ops.py; fi
    echo "[ERROR] 백업: $BACKUP" >&2
}
trap auto_restore ERR

cp -p "$UPDATE/main.py" "$UPDATE/commands.py" "$UPDATE/ops.py" app/
cp -p "$UPDATE/test_ops.py" tests/

.venv/bin/python -m py_compile app/main.py app/commands.py app/ops.py
# 테스트용 비밀키/DB를 사용한다. 운영 토큰/DB는 읽거나 변경하지 않는다.
TEST_DB="$UPDATE/test_v040_${STAMP}.db"
ANGAE_TOKEN='TEST_TOKEN_NOT_REAL_abcdefghijklmnopqrstuvwxyz0123456789' \
ANGAE_DB="$TEST_DB" \
.venv/bin/python -m unittest discover -s tests -v

trap - ERR
# 기존 서비스만 재시작한다. SSH/Watchdog는 중지하지 않는다.
bash scripts/restart-autostart.sh
sleep 3
bash scripts/status-autostart.sh
.venv/bin/python scripts/diagnose-autostart.py
printf '[OK] Python Core v0.4.0 배포 완료 (백업: %s)\n' "$BACKUP"
