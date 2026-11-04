#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 v0.4.3 Termux Python Core 안전 배포기 — 기존 프로그램 기능 전체 안내
# 1. 기존 카톡 수신/답장, Android UI/토큰/알림/로그, 8종목 시세 목록과 기존 주식·계산·시간·운영·AI 명령을 유지한다.
# 2. 키오시아 285A.T만 Yahoo Japan 본장 날짜 표시 변화와 라쿠텐 증권 공개 정규장 시세로 보완한다.
# 3. 기존 7종목의 공급자·출력, 30초 캐시, 서울/시장별 거래일, 기존 FastAPI 엔드포인트는 변경하지 않는다.
# 4. .env, .venv, data/*.db, SQLite jobs/events/AI 기록, logs/*, SSH, watchdog, boot/runit 설정을 절대 수정·삭제하지 않는다.
# 5. 전송된 정확한 파일 6개만 설치하며 변경되는 파일은 고유한 외부 backups 폴더에 원본대로 보관한다.
# 6. 배포 전 모든 파일이 있는지 확인하고, 운영 코어를 중단하기 전에 문법 검사 및 전체 Python unittest를 실행한다.
# 7. 테스트/배포 오류가 발생하면 기존 소스를 자동 복원하고, 서버가 재시작됐을 때만 이전 버전을 다시 실행한다.
# 8. 서비스 재시작 후 비밀키를 노출하지 않는 인증 Health API를 반복 확인하여 version=0.4.3을 검증한다.
# 9. Android APK, OpenAI API, 유료 시세 API, 주식 주문 및 외부 시스템 제어는 전혀 수행하지 않는다.
# 10. 확인 전·후 모든 기존 로그와 복구용 백업을 보존하며 운영 오류를 소스 수정 성공으로 가장하지 않는다.
set -Eeuo pipefail
CORE="$HOME/angaebot/core"
UPDATE="$HOME/angaebot/update_v043"
cd "$CORE"
FILES=(
    'app/market.py:market.py'
    'app/main.py:main.py'
    'app/commands.py:commands.py'
    'scripts/diagnose-market.py:diagnose-market.py'
    'tests/test_ops.py:test_ops.py'
    'tests/test_market_japan_v043.py:test_market_japan_v043.py'
)
for item in "${FILES[@]}"; do
    name="${item#*:}"
    if [ ! -f "$UPDATE/$name" ]; then
        printf '[ERROR] Missing source file: %s\n' "$name" >&2
        exit 2
    fi
done
if [ ! -f .env ] || [ ! -x .venv/bin/python ] || [ ! -f scripts/restart-autostart.sh ]; then
    echo '[ERROR] Existing Termux Core environment is incomplete' >&2
    exit 2
fi
umask 077
BACKUP="$HOME/angaebot/backups/core_pre_v043_$(date +%Y%m%d_%H%M%S_%N)"
mkdir -p "$BACKUP"
for item in "${FILES[@]}"; do
    target="${item%%:*}"
    if [ -f "$target" ]; then
        mkdir -p "$BACKUP/$(dirname "$target")"
        cp -p "$target" "$BACKUP/$target"
    fi
done
APPLIED=0
RESTARTED=0
ROLLBACK_DONE=0
rollback() {
    if [ "$ROLLBACK_DONE" -eq 1 ] || [ "$APPLIED" -ne 1 ]; then
        return 0
    fi
    ROLLBACK_DONE=1
    trap - ERR
    echo "[WARN] Update failed; restoring backup $BACKUP" >&2
    for item in "${FILES[@]}"; do
        target="${item%%:*}"
        if [ -f "$BACKUP/$target" ]; then
            cp -p "$BACKUP/$target" "$target" || :
        else
            case "$target" in
                tests/test_market_japan_v043.py) rm -f "$target" || : ;;
            esac
        fi
    done
    if [ "$RESTARTED" -eq 1 ]; then
        bash scripts/restart-autostart.sh || :
    fi
}
trap rollback ERR
APPLIED=1
for item in "${FILES[@]}"; do
    target="${item%%:*}"
    name="${item#*:}"
    cp -p "$UPDATE/$name" "$target"
done
.venv/bin/python -m py_compile app/market.py app/main.py app/commands.py scripts/diagnose-market.py tests/test_market_japan_v043.py
.venv/bin/python -m unittest discover -s tests -v
RESTARTED=1
bash scripts/restart-autostart.sh
VERSION=''
for attempt in 1 2 3 4 5 6 7 8 9 10; do
    sleep 1
    VERSION=$(.venv/bin/python - <<'PY'
import json, sys
sys.path.insert(0, 'scripts')
from health_watchdog import token_from_env
from urllib.request import Request, urlopen
try:
    request = Request('http://127.0.0.1:8765/v1/health', headers={'X-AngaeBot-Token':token_from_env()})
    with urlopen(request, timeout=2) as response:
        data = json.load(response)
    if data.get('ok') is True:
        print(data.get('version', ''))
except (OSError, ValueError, KeyError, TypeError):
    print('')
PY
    )
    if [ "$VERSION" = '0.4.3' ]; then break; fi
done
if [ "$VERSION" != '0.4.3' ]; then
    echo "[ERROR] Health check mismatch: expected 0.4.3, found '${VERSION:-unavailable}'" >&2
    rollback
    exit 1
fi
trap - ERR
printf '[OK] AngaeBot Python Core v0.4.3 installed successfully. Backup: %s\n' "$BACKUP"
echo '[INFO] No changes to Android, SSH, watchdog, .env, databases, or logs'
