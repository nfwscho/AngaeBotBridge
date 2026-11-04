#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 v0.4.1 Termux Python Core 배포기 — 전체 기능 상세 설명
# 1. 기존 FastAPI v0.4.0 계산/시간/상세상태/통계/최근오류/가동시간/AI 명령을 보존한다.
# 2. 8종목 메모리7 무료 시세 모듈, 새 테스트, 현재 버전 로그 마커만 추가한다.
# 3. 기존 .env 인증키/.venv/data SQLite/Android 앱/알림/RemoteInput/모든 로그를 유지한다.
# 4. Windows에서 scp 전송한 9개의 지정 파일만 검증하여 소스 및 테스트에 반영한다.
# 5. 변경되는 기존 파일은 날짜별 backups 폴더에 복사하며 실패 시 이전 파일을 복원한다.
# 6. 문법 검증 및 전체 unittest는 임시 DB와 테스트용 토큰으로 실시한다.
# 7. 성공 시 Python Core만 runit으로 재시작하고 watchdog/SSH를 중지·수정하지 않는다.
# 8. 인증된 health API 응답을 읽고 0.4.1 아닌 경우 소스 백업을 복원 후 Core만 재시작한다.
# 9. 소스 오류/연결 오류/테스트 실패는 진행을 중단하며 기존 SQLite/로그 파일은 삭제하지 않는다.
# 10. 의존성 재설치/OpenAI 호출/비밀키 출력/시장 데이터 임의 생성은 수행하지 않는다.
set -euo pipefail
CORE="$HOME/angaebot/core"
UPDATE="$HOME/angaebot/update_v041"
cd "$CORE"
FILES=(main.py commands.py ops.py market.py run_core.py test_market.py test_market_api.py test_ops.py)
for name in "${FILES[@]}"; do
    test -f "$UPDATE/$name" || { echo "[ERROR] 누락된 파일: $name" >&2; exit 2; }
done
[ -f .env ] && [ -x .venv/bin/python ] && [ -f scripts/restart-autostart.sh ] || {
    echo '[ERROR] 기존 환경 / .env / .venv / runit 구성을 먼저 확인하세요' >&2; exit 2;
}
STAMP="$(date +%Y%m%d_%H%M%S_%N)"
BACKUP="$HOME/angaebot/backups/core_pre_v041_${STAMP}"
umask 077
mkdir -p "$BACKUP/app" "$BACKUP/scripts" "$BACKUP/tests"
for p in app/main.py app/commands.py app/ops.py app/market.py scripts/run_core.py tests/test_market.py tests/test_market_api.py tests/test_ops.py; do
    if [ -f "$p" ]; then
        mkdir -p "$BACKUP/$(dirname "$p")"
        cp -p "$p" "$BACKUP/$p"
    fi
done
APPLIED=0
restore_source() {
    [ "$APPLIED" -eq 1 ] || return 0
    echo "[WARN] 업데이트 검증 실패: 기존 소스 복원 / 백업 $BACKUP" >&2
    for p in app/main.py app/commands.py app/ops.py app/market.py scripts/run_core.py tests/test_market.py tests/test_market_api.py tests/test_ops.py; do
        if [ -f "$BACKUP/$p" ]; then
            cp -p "$BACKUP/$p" "$p"
        else
            # 신규 모듈만 정리, 기존 로그/DB/설정에는 영향 없음
            case "$p" in app/market.py|tests/test_market.py|tests/test_market_api.py) rm -f "$p";; esac
        fi
    done
}
trap restore_source ERR
APPLIED=1
cp -p "$UPDATE/main.py" "$UPDATE/commands.py" "$UPDATE/ops.py" "$UPDATE/market.py" app/
cp -p "$UPDATE/run_core.py" scripts/
cp -p "$UPDATE/test_market.py" "$UPDATE/test_market_api.py" "$UPDATE/test_ops.py" tests/
.venv/bin/python -m py_compile app/main.py app/commands.py app/ops.py app/market.py scripts/run_core.py
ANGAE_TOKEN='TEST_ONLY_abcdefghijklmnopqrstuvwxyz1234567890' \
ANGAE_DB="$UPDATE/unit_test_${STAMP}.db" \
.venv/bin/python -m unittest discover -s tests -v
# 기존 서버는 테스트 성공 이전에 손대지 않는다.
trap - ERR
bash scripts/restart-autostart.sh
sleep 3
bash scripts/status-autostart.sh
# 테스트용 토큰을 운영환경에 덮어쓰지 않는다. 상태는 로컬 인증된 앱 endpoint로 확인.
VERSION=$(.venv/bin/python - <<'PY'
import sys
sys.path.insert(0,'scripts')
from health_watchdog import token_from_env
from urllib.request import Request,urlopen
import json
req=Request('http://127.0.0.1:8765/v1/health',headers={'X-AngaeBot-Token':token_from_env()})
try:
    with urlopen(req,timeout=4) as response:
        print(json.load(response).get('version',''))
except OSError:
    print('')
PY
)
if [ "$VERSION" != '0.4.1' ]; then
    echo '[ERROR] 업데이트 후 Health 버전 불일치; 소스 복원 후 core를 재시작합니다.' >&2
    restore_source
    bash scripts/restart-autostart.sh || :
    exit 1
fi
printf '[OK] Python Core v0.4.1 정상 설치. 백업: %s\n' "$BACKUP"
