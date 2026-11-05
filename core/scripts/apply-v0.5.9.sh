#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 Python Core v0.5.9 Termux 안전 배포 — 모든 기존 기능·로그·데이터 보존 상세 설명
# 1. 기존 카카오톡 NotificationListener/RemoteInput, Android 관리 UI와 배터리 상태 접미사는 변경하지 않는다.
# 2. 기존 명령어 '주', '주 메모리7', '주 반도체', '주 분 종목' 및 5분 유효 숫자 선택을 그대로 유지한다.
# 3. 메모리7/사용자 그룹·미국시총10의 종목 순서·가격·통화·등락률·조회불가·기존 SQLite 저장 및 사용자 접근 범위를 유지한다.
# 4. 각 시장별 공급자·최신 거래시각·지연/장마감 정보를 종목 옆이 아닌 보고서 맨 아래 한 번으로 통합한다.
# 5. KRX/NXT 장전·장후 별도 가격과 시장별 체결시각 차이·다른 공급자 혼용 정보를 보존한다.
# 6. 네이버 폴링/모바일/Yahoo 폴백, Yahoo Finance/Nasdaq 미국 시세, 키오시아 Yahoo Japan/라쿠텐 보조 공급자를 유지한다.
# 7. 미국 403/429 제한 처리, 무료 공개 API/HTTPS/엄격한 가격·거래일·통화 검증 및 로깅은 변경하지 않는다.
# 8. 5거래일·21·63일 분석, 운영상태/AI OFF·계산, jobs/events/AI 사용자 데이터 및 모든 기존 로그를 유지한다.
# 9. 기존 .env, SQLite DB, Android APK/설정/권한, Termux SSH, runit watchdog 및 부팅 자동시작을 변경하지 않는다.
# 10. Windows에서 전달한 수정 파일의 존재 여부를 확인하고, 서비스 수정 전에 각각 이전 파일을 백업한다.
# 11. 기존 Python 가상환경과 시간대 데이터만 사용하고 별도 설치/유료 API/자동 주문/상시 감시는 도입하지 않는다.
# 12. Python 문법 검사와 전체 회귀 테스트가 통과한 후에만 기존 서비스 재시작을 실행한다.
# 13. 실패 시 이전 소스를 자동 복원하고 필요한 경우 기존 서버를 재시작하며 기존 DB/로그는 삭제하지 않는다.
# 14. 인증된 /v1/health가 Core 0.5.9로 응답할 때만 배포 성공을 출력한다.
set -Eeuo pipefail
CORE="$HOME/angaebot/core"
UPDATE="$HOME/angaebot/update_v059"
cd "$CORE"
ITEMS=(
  'app/market.py:market.py'
  'app/watchlists.py:watchlists.py'
  'app/main.py:main.py'
  'app/commands.py:commands.py'
  'scripts/run_core.py:run_core.py'
  'tests/test_market_source_summary.py:test_market_source_summary.py'
  'tests/test_naver_realtime.py:test_naver_realtime.py'
  'tests/test_ops.py:test_ops.py'
  'tests/test_history_api.py:test_history_api.py'
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
BACKUP="$HOME/angaebot/backups/core_pre_v059_$(date +%Y%m%d_%H%M%S_%N)"
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
EXPECTED_VERSION='0.5.9'
rollback() {
  if [ "$ROLLED_BACK" -eq 1 ] || [ "$APPLIED" -ne 1 ]; then return 0; fi
  ROLLED_BACK=1
  trap - ERR
  printf '[WARN] v0.5.9 validation failed; restoring previous source: %s\n' "$BACKUP" >&2
  for row in "${ITEMS[@]}"; do
    dest="${row%%:*}"
    if [ -f "$BACKUP/$dest" ]; then
      cp -p "$BACKUP/$dest" "$dest" || :
    elif [ "$dest" = 'tests/test_market_source_summary.py' ]; then
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
  app/market.py app/watchlists.py app/main.py app/commands.py \
  scripts/run_core.py tests/test_market_source_summary.py tests/test_naver_realtime.py tests/test_ops.py \
  tests/test_history_api.py tests/test_watchlist_api.py
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
printf '[OK] AngaeBot Python Core v0.5.9 installed successfully. Backup: %s\n' "$BACKUP"
echo '[INFO] Existing Android APK, SQLite, jobs, events, logs, secrets, AI, watchdog and SSH settings untouched.'
