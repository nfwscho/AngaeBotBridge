#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 Python Core v0.5.6 Termux 안전 배포 — 전체 기능·UI·동작·로그 보존 상세 설명
# 1. 기존 KakaoTalk NotificationListener/RemoteInput/Android UI·허용 채팅방/발신자 설정을 변경하지 않는다.
# 2. 계산·시간·서버상태·AI상태(OFF)·상세상태·통계·최근오류·가동시간·대화초기화의 동작을 유지한다.
# 3. 기존 메모리7 8종목 시세/한국·미국·일본 공급자와 30초 캐시·주식 관심그룹/미국시총10을 유지한다.
# 4. '주식 분석 한글이름/티커/그룹명/메모리7' 역사적 종가·5일/21일/63일 수익률·실현변동성 기능을 보존·확장한다.
# 5. 기존 기능 보존을 위해 변경된 Python Core 12개 소스/테스트 파일만 백업/적용하며 DB/로그는 변경하지 않는다.
# 6. SSH, runit watchdog, Android APK, 기존 부팅 자동시작 설정을 중단하거나 덮어쓰지 않는다.
# 7. 원격 SCP로 업로드한 파일 전부를 확인한 후 수정 대상 원본을 별도 backups 폴더에 백업한다.
# 8. 문법 검사 및 Python 전체 회귀 테스트가 통과하기 전에는 운영 Core 프로세스를 재시작하지 않는다.
# 9. 단위 테스트는 고정 시험 토큰·분리된 임시 SQLite 파일을 사용하며 실제 운영 DB/기존 명령 기록을 보존한다.
# 10. 오류 시 수정한 모든 파일을 이전 버전으로 자동 복원하고, 재시작했을 때만 기존 FastAPI를 다시 실행한다.
# 11. 성공 시 인증된 /v1/health가 정확히 v0.5.6인지 확인하고 ASCII 로그로 결과와 백업 경로를 남긴다.
# 12. OpenAI/유료 API·주식 주문·가격알림·예약 발송·보이지 않는 주기 감시는 실행하거나 설치하지 않는다.
# 13. 사용자 소유 stock_groups/stock_items, 과거 events/jobs/ai_sessions/ai_turns는 변경·삭제하지 않는다.
# 14. 로그 삭제/테이블 리셋/불필요한 의존성 업데이트·다른 서비스 강제종료 없이 최소 변경만 적용한다.
# 15. Termux에 없을 수 있는 IANA 시간대 DB(Asia/Seoul, Asia/Tokyo, America/New_York)를 사전에 확인한다.
# 16. DB가 누락된 경우에만 순수 Python tzdata wheel을 해당 .venv에 한정 설치하고 3개 시장 시간대를 재검사한다.
# 17. 시간대 설치/검증 실패 시 기존 운영 소스를 수정하거나 Core를 재시작하기 전에 중단한다.
# 18. 기존 및 신규 회귀 테스트와 모든 SQLite/로그/메모리7/사용자그룹/미국시총10/AI OFF를 보존한다.
# 19. 한글 종목명·회사 동의어·채팅방/발신자 전용 별칭 조회·동명 다종목 충돌 검사를 추가한다.
# 20. v0.5.5 이후의 소규모 증분 업데이트이며 기존 과거시세·시간대 핫픽스 파일을 변경하지 않는다.
# 21. 종목 목표가 알림·주기적 감시·자동 발신·주식 거래는 추가하지 않는다.
# 22. v0.5.6 테스트에서는 모든 sqlite3.connect 조회 연결을 closing으로 닫고 SQL/DB/로그/운영 API 동작은 변경하지 않는다.
# 23. 신규 SQLite 연결 추적 회귀 테스트를 포함하고 전체 테스트 통과 이후에만 서버를 재시작한다.
# 24. v0.5.6은 기존 주식 메뉴/최근 성공한 명령을 보존하면서 메모리7·관심그룹 가격표에 번호 선택을 추가한다.
# 25. Android Bridge v0.4.5에서 숫자 1~10을 인식하며 메뉴는 5분 후 자동 만료, 방/발신자 격리한다.
# 26. 테스트 및 인증된 /v1/health 버전 검사 0.5.6이 통과한 경우에만 적용하고 백업/롤백을 보장한다.
# 27. SQLite 스키마/로그/AI 설정·가격 알림·예약/주식 주문/앱 권한은 수정하지 않는다.
# 28. 메모리7·관심그룹 시세요약에 종목 원래 순서대로 1~10 번호를 표기하고 정확한 티커의 5일/21일/63일 분석으로 연결한다.
# 29. 숫자 선택은 5분/허용 채팅방·발신자/기존 Android v0.4.5 게이트를 거쳐야 하며 다른 일반 대화 숫자는 무시한다.
# 30. 기존 시세 공급자/캐시, 주식 메뉴, 한국어 종목명, SQLite jobs/events, RemoteInput·배터리 상태 표시를 보존한다.
set -Eeuo pipefail
CORE="$HOME/angaebot/core"
UPDATE="$HOME/angaebot/update_v056"
cd "$CORE"
ITEMS=(
  'app/main.py:main.py'
  'app/selection_menu.py:selection_menu.py'
  'app/commands.py:commands.py'
  'app/watchlists.py:watchlists.py'
  'app/market.py:market.py'
  'scripts/run_core.py:run_core.py'
  'tests/test_market.py:test_market.py'
  'tests/test_watchlists.py:test_watchlists.py'
  'tests/test_selection_menu.py:test_selection_menu.py'
  'tests/test_history_api.py:test_history_api.py'
  'tests/test_ops.py:test_ops.py'
  'tests/test_watchlist_api.py:test_watchlist_api.py'
)
for item in "${ITEMS[@]}"; do
  file="${item#*:}"
  if [ ! -f "$UPDATE/$file" ]; then printf '[ERROR] Missing upload: %s\n' "$file" >&2; exit 2; fi
done
if [ ! -f .env ] || [ ! -x .venv/bin/python ] || [ ! -f scripts/restart-autostart.sh ]; then
  echo '[ERROR] Missing existing .env/.venv/auto-start environment' >&2
  exit 2
fi
umask 077
BACKUP="$HOME/angaebot/backups/core_pre_v056_$(date +%Y%m%d_%H%M%S_%N)"
mkdir -p "$BACKUP"
for row in "${ITEMS[@]}"; do
  target="${row%%:*}"
  if [ -f "$target" ]; then
    mkdir -p "$BACKUP/$(dirname "$target")"
    cp -p "$target" "$BACKUP/$target"
  fi
done
# Android/Termux는 /usr/share/zoneinfo가 없는 경우가 있다. Python의 순수 데이터 휠만 보충한다.
# 실행 중인 서비스를 건드리기 전에 검사하므로 온라인 설치 실패 시 기존 Core/DB는 그대로이다.
check_market_timezones() {
    .venv/bin/python - <<'PYCODE'
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
try:
    for name in ('Asia/Seoul', 'Asia/Tokyo', 'America/New_York'):
        ZoneInfo(name)
except ZoneInfoNotFoundError:
    raise SystemExit(1)
PYCODE
}
if ! check_market_timezones; then
    echo '[INFO] Python market time zones missing. Installing tzdata (pure-Python package only).'
    if ! .venv/bin/python -m pip install --disable-pip-version-check --only-binary=:all: 'tzdata>=2025.2,<2028'; then
        echo '[ERROR] tzdata installation failed; existing Core source and service unchanged.' >&2
        exit 3
    fi
    if ! check_market_timezones; then
        echo '[ERROR] Missing IANA market time zones even after tzdata install.' >&2
        exit 3
    fi
fi
printf '[OK] IANA market time zones available: Seoul / Tokyo / New York\n'
APPLIED=0
RESTARTED=0
ROLLED_BACK=0
EXPECTED_VERSION='0.5.6'
rollback() {
  if [ "$ROLLED_BACK" -eq 1 ] || [ "$APPLIED" -ne 1 ]; then return 0; fi
  ROLLED_BACK=1
  trap - ERR
  printf '[WARN] v0.5.6 validation failed: restoring previous source from %s\n' "$BACKUP" >&2
  for row in "${ITEMS[@]}"; do
    target="${row%%:*}"
    if [ -f "$BACKUP/$target" ]; then
      cp -p "$BACKUP/$target" "$target" || :
    else
      case "$target" in
        app/selection_menu.py|tests/test_selection_menu.py) rm -f "$target" || : ;;
      esac
    fi
  done
  if [ "$RESTARTED" -eq 1 ]; then bash scripts/restart-autostart.sh || :; fi
}
trap rollback ERR
APPLIED=1
for row in "${ITEMS[@]}"; do
  target="${row%%:*}"
  source="${row#*:}"
  cp -p "$UPDATE/$source" "$target"
done
.venv/bin/python -m py_compile \
  app/main.py app/selection_menu.py app/commands.py app/watchlists.py app/market.py scripts/run_core.py \
  tests/test_market.py tests/test_watchlists.py tests/test_selection_menu.py \
  tests/test_history_api.py tests/test_ops.py tests/test_watchlist_api.py
ANGAE_TOKEN='TEST_ONLY_TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT' \
ANGAE_DB="$UPDATE/isolated_test_$(date +%s%N).db" \
.venv/bin/python -m unittest discover -s tests -q
# Regression checks passed: only now restart the existing FastAPI process.
RESTARTED=1
bash scripts/restart-autostart.sh
VERSION=''
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12; do
  sleep 1
  VERSION=$(.venv/bin/python - <<'PY'
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
PY
  )
  if [ "$VERSION" = "$EXPECTED_VERSION" ]; then break; fi
done
if [ "$VERSION" != "$EXPECTED_VERSION" ]; then
  printf '[ERROR] Health version expected %s, got %s\n' "$EXPECTED_VERSION" "${VERSION:-none}" >&2
  rollback
  exit 1
fi
trap - ERR
printf '[OK] AngaeBot Python Core v0.5.6 installed successfully. Backup: %s\n' "$BACKUP"
echo '[INFO] No Android APK/.env/SQLite/jobs/events/logs/watchdog/SSH/AI settings were modified.'
