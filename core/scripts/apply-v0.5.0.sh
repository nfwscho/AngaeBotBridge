#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 Python Core v0.5.0 Termux 안전 배포기 — 모든 기능과 기존 로그 보존 상세 설명
# 1. 카카오톡 자동응답/Android UI/알림 RemoteInput/허용 방/발신자 설정을 그대로 유지한다.
# 2. 기존 메모리7 한국·미국·일본 8종목 시세 제공자와 30초 캐시·주식 출력 형식을 변경하지 않는다.
# 3. 관심종목 그룹 CRUD/조회 모듈과 Python Core 버전·회귀 테스트만 배포한다.
# 4. 기존 계산·시간·상세상태·통계·최근오류·가동시간·AI OFF 및 FastAPI 인증을 보존한다.
# 5. .env 비밀키/.venv/Python 패키지/data/*.db/logs/*/서비스/SSH/watchdog/백업은 수정·삭제하지 않는다.
# 6. 파일 완전성 검증 후 기존 수정 대상 소스를 고유한 외부 backups 폴더에 원본대로 백업한다.
# 7. 전체 Python 문법·단위 테스트가 통과하기 전에는 운영 중인 FastAPI를 중지하거나 재시작하지 않는다.
# 8. 테스트 중 별도의 임시 SQLite 파일과 모의 토큰을 사용해 실제 운영 DB에 영향을 주지 않는다.
# 9. 실패 시 원본 소스를 복원하고, 이미 Core를 재시작한 경우에만 이전 버전을 재기동한다.
# 10. 정상 배포 후 X-AngaeBot-Token 인증된 /v1/health에서 정확히 v0.5.0을 검증한다.
# 11. OpenAI API, 유료 시세, 자동 매매, 예약 발송, Android APK 설치는 일절 수행하지 않는다.
# 12. 기존 오류/운영/가격 원문 로그는 보존하고 배포 결과와 백업 경로를 명확히 표시한다.
set -Eeuo pipefail
CORE="$HOME/angaebot/core"
UPDATE="$HOME/angaebot/update_v050"
cd "$CORE"
ITEMS=(
  'app/main.py:main.py'
  'app/commands.py:commands.py'
  'app/watchlists.py:watchlists.py'
  'scripts/run_core.py:run_core.py'
  'tests/test_ops.py:test_ops.py'
  'tests/test_watchlists.py:test_watchlists.py'
  'tests/test_watchlist_api.py:test_watchlist_api.py'
)
for row in "${ITEMS[@]}"; do
  item="${row#*:}"
  if [ ! -f "$UPDATE/$item" ]; then printf '[ERROR] Missing incoming file: %s\n' "$item" >&2; exit 2; fi
done
if [ ! -f .env ] || [ ! -x .venv/bin/python ] || [ ! -f scripts/restart-autostart.sh ]; then
  echo '[ERROR] Existing Termux v0.4.3 runtime is missing (.env / .venv / restart script)' >&2
  exit 2
fi
umask 077
BACKUP="$HOME/angaebot/backups/core_pre_v050_$(date +%Y%m%d_%H%M%S_%N)"
mkdir -p "$BACKUP"
for row in "${ITEMS[@]}"; do
  target="${row%%:*}"
  if [ -f "$target" ]; then
    mkdir -p "$BACKUP/$(dirname "$target")"
    cp -p "$target" "$BACKUP/$target"
  fi
done
APPLIED=0
RESTARTED=0
ROLLBACK_DONE=0
rollback() {
  if [ "$ROLLBACK_DONE" -eq 1 ] || [ "$APPLIED" -ne 1 ]; then return 0; fi
  ROLLBACK_DONE=1
  trap - ERR
  printf '[WARN] Validation/deployment failed. Restoring source from %s\n' "$BACKUP" >&2
  for row in "${ITEMS[@]}"; do
    target="${row%%:*}"
    if [ -f "$BACKUP/$target" ]; then
      cp -p "$BACKUP/$target" "$target" || :
    else
      case "$target" in
        app/watchlists.py|tests/test_watchlists.py|tests/test_watchlist_api.py)
          rm -f "$target" || : ;;
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
  app/main.py app/commands.py app/watchlists.py scripts/run_core.py \
  tests/test_ops.py tests/test_watchlists.py tests/test_watchlist_api.py
ANGAE_TOKEN='TEST_ONLY_TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT' \
ANGAE_DB="$UPDATE/isolated_test_$(date +%s%N).db" \
.venv/bin/python -m unittest discover -s tests -q
# 트랜잭션/회귀 검사 통과 이후에만 새 서버 프로세스 시작
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
  if [ "$VERSION" = '0.5.0' ]; then break; fi
done
if [ "$VERSION" != '0.5.0' ]; then
  printf '[ERROR] Health version verification failed: expected 0.5.0; actual %s\n' "${VERSION:-unavailable}" >&2
  rollback
  exit 1
fi
trap - ERR
printf '[OK] AngaeBot Python Core v0.5.0 installed. Backup: %s\n' "$BACKUP"
echo '[INFO] Android APK/SSH/watchdog/.env/SQLite/jobs/events/logs unchanged.'
