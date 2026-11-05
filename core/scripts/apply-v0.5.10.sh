#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 Python Core v0.5.10 Termux 안전 배포 — 전체 기능·원본 로그 보존 상세 설명
# 1. v0.5.9 기존 Android 알림 리스너/RemoteInput/UI/배터리 접미사/알림 접근권한을 변경하지 않는다.
# 2. 기존 '주', '주 반도체', '주 메모리7', 1~10번 5분간 숫자 선택/방·발신자 분리 기능을 유지한다.
# 3. 기존 국내 네이버 KRX/NXT 시세·시간외 구분, 키오시아 일본 시세, 미국 Yahoo/Nasdaq 현재가를 보존한다.
# 4. 미국 현재가가 차단될 때 나스닥 확정 일봉 2개 또는 네이버 해외 확정 일봉 2개로 종가·전일비를 조회한다.
# 5. 확정 일봉은 실시간으로 표시하지 않고 실제 시장 거래일·데이터 제공자를 하단 출처에 표기한다.
# 6. 이 기능은 사용자별 10개 그룹·메모리7 8종목·미국시총10·종목 분석(5일/1개월/3개월)을 그대로 보존한다.
# 7. 모든 기존 jobs/events/ai_sessions/ai_turns/stock_groups/stock_items/SQLite 스키마·인증키·환경설정을 변경/삭제하지 않는다.
# 8. 기존 미국 실패 진단 로그를 유지하고 공급자별 제한·응답 검증 실패 원인만 추가한다. 개인정보·토큰 기록 금지.
# 9. 전송된 변경 9개 파일의 존재를 확인하고 운영 파일을 백업한 후 최소 소스만 복사한다.
# 10. 기존 Termux .venv/시간대 데이터/SSH·runit/watchdog/자동실행을 유지하고 별도의 의존성 설치는 하지 않는다.
# 11. Python 문법 검사·전체 독립 회귀 테스트가 통과하기 전에는 운영 Core를 재시작하지 않는다.
# 12. 실패 시 소스 파일을 원본으로 복구하고 필요하면 종전 서버를 재기동하며 별도 데이터/로그는 그대로 유지한다.
# 13. 인증된 /v1/health가 v0.5.10을 반환해야만 최종 성공 메시지를 출력한다.
# 14. 미국 종목 조회에서 실제 원격 HTTP 접근 결과는 운영 장비에서 최종 확인한다.
# 15. 자동매매·가격 감시·유료 API·새 Android 권한·지속적인 배터리 소모 작업을 도입하지 않는다.
set -Eeuo pipefail
CORE="$HOME/angaebot/core"
UPDATE="$HOME/angaebot/update_v0510"
cd "$CORE"
ITEMS=(
  'app/market.py:market.py'
  'app/main.py:main.py'
  'app/commands.py:commands.py'
  'scripts/run_core.py:run_core.py'
  'tests/test_ops.py:test_ops.py'
  'tests/test_history_api.py:test_history_api.py'
  'tests/test_watchlist_api.py:test_watchlist_api.py'
  'tests/test_us_fallback.py:test_us_fallback.py'
  'tests/test_us_daily_recovery.py:test_us_daily_recovery.py'
)
for row in "${ITEMS[@]}"; do
  if [ ! -f "$UPDATE/${row#*:}" ]; then
    printf '[ERROR] Missing upload: %s\n' "${row#*:}" >&2
    exit 2
  fi
done
if [ ! -f .env ] || [ ! -x .venv/bin/python ] || [ ! -f scripts/restart-autostart.sh ]; then
  echo '[ERROR] Missing existing environment. Current server unchanged.' >&2
  exit 2
fi
.venv/bin/python - <<'PYTIME'
from zoneinfo import ZoneInfo
for name in ('Asia/Seoul','Asia/Tokyo','America/New_York'):
    ZoneInfo(name)
PYTIME
printf '[OK] IANA market time zones available\n'
umask 077
BACKUP="$HOME/angaebot/backups/core_pre_v0510_$(date +%Y%m%d_%H%M%S_%N)"
mkdir -p "$BACKUP"
for row in "${ITEMS[@]}"; do
  dest="${row%%:*}"
  if [ -f "$dest" ]; then
    mkdir -p "$BACKUP/$(dirname "$dest")"
    cp -p "$dest" "$BACKUP/$dest"
  fi
done
APPLIED=0
RESTARTED=0
ROLLED_BACK=0
rollback() {
  if [ "$APPLIED" -ne 1 ] || [ "$ROLLED_BACK" -eq 1 ]; then return 0; fi
  ROLLED_BACK=1
  trap - ERR
  printf '[WARN] Restore previous Python Core files from %s\n' "$BACKUP" >&2
  for row in "${ITEMS[@]}"; do
    target="${row%%:*}"
    if [ -f "$BACKUP/$target" ]; then
      cp -p "$BACKUP/$target" "$target" || :
    elif [ "$target" = 'tests/test_us_daily_recovery.py' ]; then
      rm -f "$target" || :
    fi
  done
  if [ "$RESTARTED" -eq 1 ]; then
    bash scripts/restart-autostart.sh || :
  fi
}
trap rollback ERR
APPLIED=1
for row in "${ITEMS[@]}"; do
  cp -p "$UPDATE/${row#*:}" "${row%%:*}"
done
.venv/bin/python -m py_compile app/market.py app/main.py app/commands.py scripts/run_core.py \
  tests/test_ops.py tests/test_history_api.py tests/test_watchlist_api.py \
  tests/test_us_fallback.py tests/test_us_daily_recovery.py
ANGAE_TOKEN='TEST_ONLY_TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT' \
ANGAE_DB="$UPDATE/isolated_test_$(date +%s%N).db" \
.venv/bin/python -W error::ResourceWarning -m unittest discover -s tests -q
RESTARTED=1
bash scripts/restart-autostart.sh
VERSION=''
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
  sleep 1
  VERSION=$(.venv/bin/python - <<'PYHEALTH'
import json,sys
sys.path.insert(0,'scripts')
from health_watchdog import token_from_env
from urllib.request import Request,urlopen
try:
    req=Request('http://127.0.0.1:8765/v1/health',headers={'X-AngaeBot-Token':token_from_env()})
    with urlopen(req,timeout=2) as response:
        obj=json.load(response)
    print(obj.get('version','') if obj.get('ok') is True else '')
except (OSError,ValueError,TypeError,KeyError):
    print('')
PYHEALTH
  )
  if [ "$VERSION" = '0.5.10' ]; then break; fi
done
if [ "$VERSION" != '0.5.10' ]; then
  printf '[ERROR] Health version expected 0.5.10, got %s\n' "${VERSION:-none}" >&2
  rollback
  exit 1
fi
trap - ERR
printf '[OK] AngaeBot Python Core v0.5.10 installed successfully. Backup: %s\n' "$BACKUP"
echo '[INFO] Existing Android APK, SQLite, jobs, events, logs, .env, AI, watchdog and SSH unchanged.'
