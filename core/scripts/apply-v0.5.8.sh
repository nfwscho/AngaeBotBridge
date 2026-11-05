#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 Python Core v0.5.8 Termux 안전 배포 — 모든 기능/로그·데이터 보존 설명
# 1. 카카오톡 알림 수신/사용자·채팅방 허용 목록/숫자 5분 메뉴/배터리 보고/Android 앱 UI는 변경하지 않는다.
# 2. 고정 메모리7/사용자 관심그룹/전 종목 등록·삭제·조회·미국시총10과 정확한 티커/별칭 매핑을 보존한다.
# 3. 한국 두 종목은 네이버 폴링/모바일/기존 Yahoo 폴백 및 KRX/NXT 분리·체결시간 지연 검증을 유지한다.
# 4. 일본 키오시아 Yahoo Japan/증권사 폴백과 미국·일본·한국 현지통화·전일 대비 형식을 유지한다.
# 5. 미국 Yahoo 차트는 브라우저 HTTP 헤더를 보내고 403/429 차단 시 반복 요청 없이 다른 제공처를 조회한다.
# 6. 미국 Yahoo 실패 시 미국 종목에만 공개 Nasdaq 웹 API를 1회 조회하며 종목/날짜/가격/등락률을 검증한다.
# 7. Nasdaq 웹의 성공 시 지연 여부 미확인으로 표시하고 오류 시 기존 조회 불가 처리·부분실패 격리를 보존한다.
# 8. 과거 5거래일·21거래일·63거래일 분석, 선택 번호, 운영 상태·AI OFF·요약·계산·로그 동작을 유지한다.
# 9. 기존 .env/SQLite jobs/events/stock_groups/stock_items/ai_sessions/ai_turns/logs 데이터·토큰은 삭제하지 않는다.
# 10. 운영 FastAPI 127.0.0.1:8765/runit/SSH/watchdog/Termux 부팅 설정과 인증 헤더·명령 중복 방지를 보존한다.
# 11. 업로드 파일 존재 여부·시각대 자료·설정·가상환경을 확인한 후에만 기존 소스를 백업해 교체한다.
# 12. 임시 테스트 DB 및 전체 Python 단위 테스트를 통과한 이후에만 운영 Core를 재시작한다.
# 13. 적용 또는 재시작 검증 실패 시 기존 소스를 원상 복원하며 기존 서버/DB/로그는 유지한다.
# 14. 인증된 /v1/health v0.5.8을 확인한 뒤에만 설치 성공으로 보고한다.
# 15. OpenAI/유료 데이터/주식 주문/주기적인 가격 알림/예약 발송/상시 WebSocket/추가 권한은 도입하지 않는다.
set -Eeuo pipefail
CORE="$HOME/angaebot/core"
UPDATE="$HOME/angaebot/update_v058"
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
BACKUP="$HOME/angaebot/backups/core_pre_v058_$(date +%Y%m%d_%H%M%S_%N)"
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
EXPECTED_VERSION='0.5.8'
rollback() {
  if [ "$ROLLED_BACK" -eq 1 ] || [ "$APPLIED" -ne 1 ]; then return 0; fi
  ROLLED_BACK=1
  trap - ERR
  printf '[WARN] v0.5.8 validation failed; restoring previous source: %s\n' "$BACKUP" >&2
  for row in "${ITEMS[@]}"; do
    dest="${row%%:*}"
    if [ -f "$BACKUP/$dest" ]; then
      cp -p "$BACKUP/$dest" "$dest" || :
    elif [ "$dest" = 'tests/test_us_fallback.py' ]; then
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
  tests/test_ops.py tests/test_history_api.py tests/test_watchlist_api.py tests/test_us_fallback.py
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
printf '[OK] AngaeBot Python Core v0.5.8 installed successfully. Backup: %s\n' "$BACKUP"
echo '[INFO] Existing Android APK, SQLite, jobs, events, logs, secrets, AI, watchdog and SSH settings untouched.'
