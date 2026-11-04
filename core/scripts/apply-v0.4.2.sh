#!/data/data/com.termux/files/usr/bin/bash
# 앙개봇 v0.4.2 Termux Python Core 안전 배포기 — 현재 프로그램 전체 기능 상세 설명
# 1. 기존 v0.4.1의 카카오톡 수신/답장/Android UI/설정/SQLite/로그·모든 명령을 변경하지 않는다.
# 2. '주식 메모리7'의 한국(네이버), 일본(Yahoo Japan) 보조 공급자를 추가하며 미국 Yahoo 조회를 유지한다.
# 3. 운영 프로그램 main/commands/ops/market/run_core와 신규 테스트를 지정된 경로에만 설치한다.
# 4. 환경변수 ANGAE_TOKEN 및 .env, .venv, data/*.db, logs/*, runit SSH/watchdog, Android 앱은 보호한다.
# 5. 전송된 파일 전부를 확인한 후 기존 운영/테스트 소스를 외부 backups 디렉터리에 시각별로 보존한다.
# 6. 문법 검사와 전체 Python unittest를 통과해야만 기존 FastAPI runit Core만 재시작한다.
# 7. 실패 시 모든 변경된 소스를 기존 백업으로 복구하고, 서버가 재시작된 경우 구 버전을 재시작한다.
# 8. 정상 업그레이드 후 인증된 Health API version=0.4.2를 확인한다(비밀키 출력 없음).
# 9. Android/SSH/watchdog/부팅서비스를 재시작하지 않으며 주식 자동 매매·AI 호출은 지원하지 않는다.
# 10. 이미 존재하는 로그, 과거 시세/DB, 기존 백업은 절대 삭제하지 않는다.
set -Eeuo pipefail
CORE="$HOME/angaebot/core"
UPDATE="$HOME/angaebot/update_v042"
cd "$CORE"
ITEMS=(
  'app/main.py:main.py'
  'app/commands.py:commands.py'
  'app/ops.py:ops.py'
  'app/market.py:market.py'
  'scripts/run_core.py:run_core.py'
  'tests/test_ops.py:test_ops.py'
  'tests/test_market_fallback.py:test_market_fallback.py'
  'scripts/diagnose-market.py:diagnose-market.py'
)
for row in "${ITEMS[@]}"; do
  file="${row#*:}"
  if [ ! -f "$UPDATE/$file" ]; then echo "[ERROR] 전송된 파일 누락: $file" >&2; exit 2; fi
done
if [ ! -f .env ] || [ ! -x .venv/bin/python ] || [ ! -f scripts/restart-autostart.sh ]; then
  echo '[ERROR] 기존 .env/venv/runit 준비 상태를 확인하세요' >&2; exit 2
fi
umask 077
STAMP="$(date +%Y%m%d_%H%M%S_%N)"
BACKUP="$HOME/angaebot/backups/core_pre_v042_${STAMP}"
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
rollback() {
  trap - ERR
  echo "[WARN] 검증 실패: 기존 소스 복원, 백업=$BACKUP" >&2
  if [ "$APPLIED" -eq 1 ]; then
    for row in "${ITEMS[@]}"; do
      target="${row%%:*}"
      if [ -f "$BACKUP/$target" ]; then
        cp -p "$BACKUP/$target" "$target"
      else
        # 신규로 추가된 유닛 테스트 파일만 되돌린다.
        case "$target" in tests/test_market_fallback.py|scripts/diagnose-market.py) rm -f "$target";; esac
      fi
    done
    if [ "$RESTARTED" -eq 1 ]; then
      bash scripts/restart-autostart.sh || :
    fi
  fi
}
trap rollback ERR
APPLIED=1
for row in "${ITEMS[@]}"; do
  target="${row%%:*}"
  file="${row#*:}"
  cp -p "$UPDATE/$file" "$target"
done
.venv/bin/python -m py_compile app/main.py app/commands.py app/ops.py app/market.py scripts/run_core.py tests/test_market_fallback.py scripts/diagnose-market.py
.venv/bin/python -m unittest discover -s tests -v
# 기존 서비스는 테스트 완료 전까지 중단하지 않는다.
RESTARTED=1
bash scripts/restart-autostart.sh
sleep 3
VERSION=$(.venv/bin/python - <<'PY'
import json,sys
sys.path.insert(0,'scripts')
from health_watchdog import token_from_env
from urllib.request import Request,urlopen
req=Request('http://127.0.0.1:8765/v1/health',headers={'X-AngaeBot-Token':token_from_env()})
try:
    with urlopen(req,timeout=4) as response:
        value=json.load(response)
    print(value.get('version','') if value.get('ok') is True else '')
except OSError:
    print('')
PY
)
if [ "$VERSION" != '0.4.2' ]; then
  echo "[ERROR] 서버 버전이 0.4.2가 아닙니다: $VERSION" >&2
  rollback
  exit 1
fi
trap - ERR
printf '[OK] AngaeBot Python Core 0.4.2 배포 성공. 백업: %s\n' "$BACKUP"
