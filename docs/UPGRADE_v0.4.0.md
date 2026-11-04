# AngaeBot v0.4.0 — Git Pull 및 S20+ 배포 안내

v0.3.1에서 안정화한 Termux FastAPI/SSH/watchdog과 기존 Android 카카오톡 답장 기능을 모두 유지하며 운영 조회 명령만 추가합니다. **OpenAI API는 설정하지 않고 OFF로 유지**합니다.

## 1. Windows GitHub 소스 갱신

```powershell
cd D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
```

기존 변경사항이 있으면 덮어쓰지 말고 먼저 확인하세요.

## 2. Android 앱 빌드 및 설치

```powershell
cd D:\stockproj\AngaeBotBridge
$jdk17 = Get-ChildItem "C:\Program Files\Eclipse Adoptium\jdk-17*" -Directory | Select-Object -First 1 -ExpandProperty FullName
$env:JAVA_HOME = $jdk17
$env:Path = "$jdk17\bin;$env:Path"
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb devices -l
& $adb install -r ".\app\build\outputs\apk\debug\app-debug.apk"
```

`Success`여야 합니다. **기존 앱을 삭제하거나 데이터를 초기화하지 마세요.** 기존 Android 인증키·허용목록·SQLite 로그 유지.

## 3. PowerShell 한 번으로 Python Core 배포 (권장)

`git pull`로 받은 저장소에는 새 배포기가 포함되어 있습니다. **ZIP 불필요**. S20+의 기존 .env, DB, 로그, runit/SSH는 유지합니다.

```powershell
cd D:\stockproj\AngaeBotBridge
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy-v0.4.0.ps1
```

이 명령은 원격 `~/angaebot/update_v040`에 필요한 Python 파일 4개와 설치기만 전송하고, 백업→문법 검사→전체 unittest→FastAPI 재시작→`HEALTH_OK`/진단까지 수행합니다. 테스트 실패 시 서버를 재시작하지 않고 기존 Python 소스 파일을 복원합니다.

IP가 달라졌다면:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy-v0.4.0.ps1 -Target 'u0_a435@<S20_IP>' -SshPort 8022
```

자동 배포가 SSH 접속 오류로 실패하면 `ssh -p 8022 u0_a435@10.1.1.202`로 연결 상태를 먼저 확인하세요. 이전에 직접 수정했던 Termux 데이터베이스·토큰·로그를 삭제할 필요는 없습니다.

## 4. 설치 후 확인

```powershell
ssh -p 8022 u0_a435@10.1.1.202
```

S20+ Termux에서:

```bash
cd ~/angaebot/core
bash scripts/status-autostart.sh
.venv/bin/python scripts/diagnose-autostart.py
```

`HEALTH_OK version=0.4.0`을 확인합니다. 진단기 자신의 제목에는 안정화 도구 버전 `0.3.1`이 남아 있을 수 있지만 `FastAPI:` 행은 실제 엔진 버전입니다.

> PowerShell 배포기는 별도 SSH 명령으로 설치를 진행하므로, 테스트 오류가 발생해도 사용자가 별도로 열어 놓은 SSH 터미널을 `set -e`로 종료시키지 않습니다.

## 5. 카카오톡 실제 명령 검증

S25+에서 S20+ 앙개봇으로 아래 메시지를 차례로 보내세요.

```text
앙개야 테스트
앙개야 도움말
앙개야 계산 344*454
앙개야 서버상태
앙개야 상세상태
앙개야 통계
앙개야 최근오류
앙개야 가동시간
앙개야 AI상태
```

- 계산: 156,176.
- 서버상태: Python v0.4.0.
- 상세상태: core/watchdog/sshd와 포트, 가동시간.
- 통계: 이 대화의 Python 명령 실행/성공/실패 건수 (현재 명령 이전까지의 기록).
- 최근오류: 이 대화·발신자 명령의 실패 이력만 출력.
- AI상태: OFF 유지.

## 보안/한계

- 기존 Android 허용목록의 표시 이름은 암호학적 신원 인증이 아닙니다. 개인 용도만 권장합니다.
- 운영 조회는 같은 채팅·발신자의 Python 명령 이력만 조회하지만 로컬 인증 토큰과 Android 허용목록을 계속 보호해야 합니다.
- Python jobs/events/ai_turns 및 Android 로그는 변경·삭제되지 않습니다.
- `최근오류`는 Python Core jobs의 실패 내역만 조회합니다. runit SSH 부팅 오류/Android 로그까지 통합한 것이 아닙니다.
- `가동시간`은 FastAPI 프로세스 가동시간입니다. 휴대폰 전체 가동시간이 아닙니다.
- 실제 부팅 후 자동 복귀는 별도 재부팅 검증이 필요합니다.
