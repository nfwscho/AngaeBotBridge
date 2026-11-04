# 앙개봇 v0.3.1 Termux 안정화 업그레이드 (ZIP 불필요)

## 1. Windows Git Pull

```powershell
cd D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
```

Android 소스는 수정하지 않아 APK 재빌드/설치가 **필요 없습니다**. 기존 Android Bridge v0.3.0을 사용합니다.

## 2. Windows에서 S20+로 전송

**PowerShell에서** 현재 PC Git 파일을 *임시 폴더*로 전송합니다. 기존 Termux DB와 .env는 옮기지 않습니다.

```powershell
cd D:\stockproj\AngaeBotBridge
ssh -p 8022 u0_a435@10.1.1.202 'mkdir -p ~/angaebot/update_v031'
scp -P 8022 .\core\app\main.py .\core\app\commands.py 'u0_a435@10.1.1.202:~/angaebot/update_v031/'
scp -P 8022 .\core\scripts\start-termux.sh .\core\scripts\run_core.py .\core\scripts\health_watchdog.py .\core\scripts\diagnose-autostart.py .\core\scripts\install-stability.sh 'u0_a435@10.1.1.202:~/angaebot/update_v031/'
scp -P 8022 .\core\tests\test_stability.py 'u0_a435@10.1.1.202:~/angaebot/update_v031/'
ssh -p 8022 u0_a435@10.1.1.202 'ls -lh ~/angaebot/update_v031'
```

## 3. Termux에서 백업 및 설치

S20+ 자체 Termux 또는 `ssh -p 8022 u0_a435@10.1.1.202`로 접속해서 다음 명령을 실행합니다. **SSH 셸 안에서는 `exit`를 스크립트 중간에 사용하지 마세요.**

```bash
cd ~/angaebot/core
set -e
U="$HOME/angaebot/update_v031"
for file in main.py commands.py start-termux.sh run_core.py health_watchdog.py diagnose-autostart.py install-stability.sh test_stability.py; do
  test -f "$U/$file" || { echo "ERROR: missing $U/$file"; false; }
done
BACKUP="$HOME/angaebot/backups/core_pre_v031_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP/app" "$BACKUP/scripts"
cp -p app/main.py app/commands.py "$BACKUP/app/"
cp -p scripts/start-termux.sh scripts/health_watchdog.py "$BACKUP/scripts/"
cp "$U/main.py" "$U/commands.py" app/
cp "$U/start-termux.sh" "$U/run_core.py" "$U/health_watchdog.py" "$U/diagnose-autostart.py" "$U/install-stability.sh" scripts/
cp "$U/test_stability.py" tests/
.venv/bin/python -m py_compile app/main.py app/commands.py scripts/run_core.py scripts/health_watchdog.py scripts/diagnose-autostart.py
bash -n scripts/start-termux.sh scripts/install-stability.sh
.venv/bin/python -m unittest discover -s tests -v
# 기존 부팅 스크립트 백업 후 새 진단 스크립트 등록. 현재 SSH 연결은 건드리지 않음.
bash scripts/install-stability.sh
# runit이 관리하는 FastAPI + watchdog만 재시작 (SSH는 유지)
bash scripts/restart-autostart.sh
export SVDIR="${PREFIX:-/data/data/com.termux/files/usr}/var/service"
sv restart "$SVDIR/angaebot-watchdog"
sleep 3
bash scripts/status-autostart.sh
.venv/bin/python scripts/diagnose-autostart.py
```

`HEALTH_OK version=0.3.1` 또는 `앙개야 서버상태`에서 Python v0.3.1을 확인합니다.

## 4. 기존 기능 회귀 테스트

카톡: `앙개야 테스트`, `앙개야 계산 123*456`, `앙개야 시간`, `앙개야 서버상태`, `앙개야 AI상태`.

AI는 OFF 유지. OpenAI API 키 등록 및 사용료 발생 동작 없음.

## 5. 부팅 시험은 원할 때 진행

차후 실제 S20+ 재부팅 후 `logs/boot.log`의 BOOT_STARTED/BOOT_FINISHED 시각과 `sshd`, `angaebot-core`, `angaebot-watchdog` 상태를 확인합니다.

```bash
cd ~/angaebot/core
.venv/bin/python scripts/diagnose-autostart.py
tail -n 30 logs/boot.log
```

`boot.log=ABSENT`가 나오면 새 부팅 스크립트가 실행되지 않았음을 **의심**할 수 있지만, 최근 설치 직후 재부팅하지 않았으면 정상입니다. Google Play Termux의 자동 실행 자체는 Android의 앱 정책/권한에 좌우되므로 실기기에서 확인해야 합니다.

## 6. 복구 절차

이상 발생 시 먼저 오류 로그를 확인합니다.

```bash
cd ~/angaebot/core
.venv/bin/python scripts/diagnose-autostart.py
tail -n 30 logs/server.log
tail -n 30 logs/launcher.log
```

설치 전 앱/스크립트 백업은 `~/angaebot/backups/core_pre_v031_*`에 있습니다. SSH 실행 중에는 SSH 서비스를 중지하지 마세요. 수동으로 `bash scripts/start-termux.sh`를 실행하면 runit과의 중복 실행이 차단되도록 의도했습니다.
