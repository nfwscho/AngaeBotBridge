#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 Python Core v0.5.7 Termux 안전 배포 — 모든 기능/로그·데이터 보존 설명
# 1. Android KakaoTalk NotificationListener/RemoteInput/기존 UI·숫자 선택/배터리 보고 기능은 변경하지 않는다.
# 2. 명령어 단축어 '주', '주 분 삼성전자', '주식 메모리7' 및 해당 채팅방/발신자별 5분 번호 선택을 유지한다.
# 3. 삼성전자·하이닉스는 네이버 폴링 우선, 모바일 API 보조, Yahoo Finance 최후 폴백으로 시세를 조회한다.
# 4. KRX 본장 시세/체결시각/OPEN·CLOSE/네이버 지연시간 메타를 검증 후 표시한다.
# 5. NXT 직접 식별 정보가 없으면 거래소를 추정하지 않고 시간외 시세를 별도로 출력한다.
# 6. 서버시각·체결시각이 오래되거나 종료된 장은 실시간 표기가 아닌 지연/마감 상태로 제공한다.
# 7. 미국·일본 6종목, 메모리7 8종목, 관심그룹 10종목, 프리셋, 최근 5일/1·3개월 분석을 그대로 유지한다.
# 8. Python 인증 토큰(.env), 기존 jobs/events/ai_sessions/ai_turns/stock_groups/stock_items와 로그를 삭제·수정하지 않는다.
# 9. 기존 앱 권한/모바일 APK·SQLite 데이터베이스·watchdog/SSH/Termux 부팅/자동시작 구성은 변경하지 않는다.
# 10. 소스 적용 전에 9개 수정 파일을 검증하고, 운영 중인 파일은 동일 경로 backups에 원형 백업한다.
# 11. Python 문법 검사와 임시 SQLite 분리 테스트가 모두 성공한 뒤에만 runit FastAPI 서버를 재시작한다.
# 12. 실패 시 기존 소스로 되돌리고 서버를 재시작했으면 기존 프로그램을 복원·재시작한다.
# 13. 인증된 /v1/health에서 정확히 0.5.7을 확인해야 성공 메시지를 출력한다.
# 14. 기존 UI·동작·COMMAND_DONE/REJECTED·이벤트 기록 및 모든 로그 흐름을 유지한다.
# 15. 외부 AI API/실시간 유료 키, 가격 알림/자동매매/자동발송/상시 WebSocket/주기적 호출을 추가하지 않는다.
# 16. 시간대 IANA 자료가 없으면 사전 검사에서 중지하며 이미 설정된 Python 패키지/버전을 변경하지 않는다.
set -Eeuo pipefail
CORE="$HOME/angaebot/core"
UPDATE="$HOME/angaebot/update_v057"
cd "$CORE"
ITEMS=(
  'app/market.py:market.py'
  'app/main.py:main.py'
  'app/commands.py:commands.py'
  'scripts/run_core.py:run_core.py'
  'tests/test_naver_realtime.py:test_naver_realtime.py'
  'tests/test_market_fallback.py:test_market_fallback.py'
  'tests/test_history_api.py:test_history_api.py'
  'tests/test_ops.py:test_ops.py'
  'tests/test_watchlist_api.py:test_watchlist_api.py'
)
for row in "${ITEMS[@]}"; do
  if [ ! -f "$UPDATE/${row#*:}" ]; then
    printf '[ERROR] Missing uploaded file: %s\n' "${row#*:}" >&2
    exit 2
  fi
done
if [ ! -f .env ] || [ ! -x .venv/bin/python ] || [ ! -f scripts/restart-autostart.sh ]; then
  echo '[ERROR] Missing existing .env/.venv/restart script; existing service unchanged.' >&2
  exit 2
fi
.venv/bin/python - <<'PYTIME'
from zoneinfo import ZoneInfo
for name in ('Asia/Seoul','Asia/Tokyo','America/New_York'):
    ZoneInfo(name)
PYTIME
printf '[OK] IANA market time zones available: Seoul / Tokyo / New York\n'
umask 077
BACKUP="$HOME/angaebot/backups/core_pre_v057_$(date +%Y%m%d_%H%M%S_%N)"
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
EXPECTED_VERSION='0.5.7'
rollback() {
  if [ "$ROLLED_BACK" -eq 1 ] || [ "$APPLIED" -ne 1 ]; then return 0; fi
  ROLLED_BACK=1
  trap - ERR
  printf '[WARN] v0.5.7 validation failed; restoring previous source: %s\n' "$BACKUP" >&2
  for row in "${ITEMS[@]}"; do
    dest="${row%%:*}"
    if [ -f "$BACKUP/$dest" ]; then
      cp -p "$BACKUP/$dest" "$dest" || :
    elif [ "$dest" = 'tests/test_naver_realtime.py' ]; then
      rm -f "$dest" || :
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
.venv/bin/python -m py_compile \
  app/market.py app/main.py app/commands.py scripts/run_core.py \
  tests/test_naver_realtime.py tests/test_market_fallback.py \
  tests/test_history_api.py tests/test_ops.py tests/test_watchlist_api.py
ANGAE_TOKEN='TEST_ONLY_TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT' \
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
except (OSError, ValueError, TypeError, KeyError):
    print('')
PYHEALTH
  )
  if [ "$VERSION" = "$EXPECTED_VERSION" ]; then break; fi
done
if [ "$VERSION" != "$EXPECTED_VERSION" ]; then
  printf '[ERROR] Health version expected %s, got %s\n' "$EXPECTED_VERSION" "${VERSION:-none}" >&2
  rollback
  exit 1
fi
trap - ERR
printf '[OK] AngaeBot Python Core v0.5.7 installed successfully. Backup: %s\n' "$BACKUP"
echo '[INFO] Existing Android APK, SQLite, jobs, events, logs, secrets, AI, watchdog and SSH settings untouched.'
