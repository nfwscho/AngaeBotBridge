# 앙개봇 Android Bridge + Termux Python Core v0.2.0 설치·업그레이드

기준: Windows `D:\stockproj\AngaeBotBridge`, GitHub `https://github.com/nfwscho/AngaeBotBridge` / `main`, 메인 S25+·보조 S20+.

## 0. 현재 확인된 사실과 제한

- **v0.1.3은 실제 S20+에서 설치되고 S25+로 카톡 답장이 도착함**. 이 성공 상태를 기준으로 기존 구조를 보존함.
- v0.2.0에는 `Python 연결 기본 OFF`와 `기존 로컬 명령 유지` 원칙을 적용함.
- 별도 인증키 없이는 FastAPI 호출 불가. Python 서버는 `127.0.0.1:8765` 외부 접근 차단.
- 본 산출물의 Python 테스트는 수행했지만, **Android SDK가 없는 작성 환경에서 v0.2.0 APK 컴파일과 S20+ 실기기 재시험은 미완료**.
- 장시간 작업 결과를 카카오톡에 임의로 발송할 수 있다는 보장은 없음. 이번 버전은 빠른 계산·상태 확인 명령만 제공.

## 1. Windows 소스 안전 업데이트

### 1-A. 권장: 안전 반영 스크립트

1. v0.2.0 전체 ZIP을 임시 폴더에 압축 해제합니다. (내부 `AngaeBotBridge` 폴더가 들어 있습니다.)
2. Windows PowerShell에서 스크립트 경로만 자신의 압축 해제 경로로 변경해 실행합니다.

```powershell
cd D:\stockproj\AngaeBotBridge
git status
git diff

# 아래 C:\Temp\AngaeBot-v0.2.0 부분을 압축 해제한 실제 경로로 변경
powershell -ExecutionPolicy Bypass -File "C:\Temp\AngaeBot-v0.2.0\AngaeBotBridge\scripts\apply-v0.2.0.ps1" -TargetRoot "D:\stockproj\AngaeBotBridge"

git diff --stat
git diff
```

스크립트는 변경 대상 원본을 **프로젝트 바깥 `D:\stockproj\AngaeBotBridge_backup_날짜시각`**에 백업합니다. `.git`, `local.properties`, Android 앱 내부의 실제 SQLite 로그/설정, 기존 APK 등은 건드리지 않습니다.

### 1-B. 수동 복사

전체 ZIP을 기존 Git 폴더에 무작정 덮어쓰지 마세요. 현재 저장소의 변경점을 먼저 비교하고 `app/src/main/`의 변경 코드와 새 `core/`, 새 `docs/` 문서만 병합하세요. 실제 1차 성공 버전은 Git 커밋·태그로 보존해 두세요.

## 2. v0.2.0 APK 빌드 및 설치

기존과 동일한 JDK 17, Android SDK 36, Gradle 8.14.3을 이용합니다.

```powershell
cd D:\stockproj\AngaeBotBridge
$jdk17 = Get-ChildItem "C:\Program Files\Eclipse Adoptium\jdk-17*" -Directory |
    Select-Object -First 1 -ExpandProperty FullName
$env:JAVA_HOME = $jdk17
$env:Path = "$jdk17\bin;$env:Path"
java -version
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug --stacktrace

$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb devices -l
& $adb install -r ".\app\build\outputs\apk\debug\app-debug.apk"
```

- `Success`가 나오면 기존 앱 위에 **업데이트 설치**됩니다. 같은 `applicationId`이고 정상적인 동일 디버그 서명으로 빌드하면 Android 앱 데이터가 유지됩니다.
- Android Studio 디버그 키를 재생성/교체했다면 `INSTALL_FAILED_UPDATE_INCOMPATIBLE`가 발생할 수 있습니다. **기존 앱을 삭제하면 내부 DB/설정이 사라질 수 있으니, 삭제하지 말고 먼저 해결**하세요.
- 기존 설치 앱에서 TXT 로그 내보내기를 사전에 권장합니다.

## 3. S20+에 Termux 설치

- F-Droid의 Termux 앱: https://f-droid.org/en/packages/com.termux/
- Termux:Boot은 선택 기능이며 **Termux와 동일한 출처**에서 설치해야 합니다.
- S20+에서 Termux를 실행하고 아래 명령을 한 번 실행하세요.

```bash
pkg update && pkg upgrade -y
pkg install python python-pip unzip curl -y
termux-setup-storage
```

`termux-setup-storage` 실행 후 저장소 접근을 허용합니다. 이 권한은 ZIP 복사에만 사용하고 서버 자체는 `~/angaebot/core`에서 구동합니다.

### Python Core ZIP을 Windows에서 휴대폰으로 보내기

먼저 별도로 제공한 `GPT_20261104_앙개봇_PythonCore_v0.2.0.zip`을 Windows Downloads 폴더에 저장합니다.

```powershell
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb push "$env:USERPROFILE\Downloads\GPT_20261104_앙개봇_PythonCore_v0.2.0.zip" /sdcard/Download/
```

S20+ Termux에서:

```bash
mkdir -p ~/angaebot
cd ~/angaebot
unzip ~/storage/downloads/GPT_20261104_앙개봇_PythonCore_v0.2.0.zip
cd ~/angaebot/core
bash scripts/install-termux.sh
```

설치 스크립트는 `.venv`에 FastAPI 및 Uvicorn을 설치하고 **32바이트 난수 기반 64자리 인증 토큰**을 `core/.env`에 생성합니다. `.env`를 GitHub에 업로드하지 마세요.

**Termux의 Python 버전에 따라 `pydantic-core` 패키지의 Rust 빌드가 필요할 수 있습니다.** 설치가 실패하면 Termux에서 `pkg install rust binutils clang -y`를 실행하고 `bash scripts/install-termux.sh`를 다시 실행합니다. `uvicorn[standard]`는 Termux에서 추가 네이티브 의존성을 끌어올 수 있어 사용하지 않습니다.

## 4. S20+에서 Python 서버 구동 및 로컬 점검

첫 번째 Termux 세션:

```bash
cd ~/angaebot/core
bash scripts/start-termux.sh
```

- `Uvicorn running on http://127.0.0.1:8765`가 나오면 서버가 실행된 것입니다.
- 이 세션을 실행 상태로 둡니다. 창을 닫거나 Termux 프로세스가 종료되면 서버가 중지됩니다.

두 번째 Termux 세션(왼쪽 가장자리에서 드로어 열고 새 세션 선택 또는 별도 탭):

```bash
cd ~/angaebot/core
. ./.env
.venv/bin/python scripts/test-api.py
```

정상 예:

```text
/v1/health {"ok":true,"version":"0.2.0",...}
/v1/commands {"ok":true,"reply":"🧮 계산 결과: 56,088",...}
```

토큰 확인(본인 기기에서만):

```bash
cd ~/angaebot/core
grep '^ANGAE_TOKEN=' .env
```

`ANGAE_TOKEN=` 오른쪽 값만 복사하여 Android Bridge에 입력합니다. 공개 대화방과 GitHub, 오류 스크린샷에는 토큰을 노출하지 마세요.

## 5. 앙개봇 관리 UI의 ②-A Python 설정

1. S20+에서 기존 **앙개봇 Bridge**를 실행하세요.
2. 기존 알림 접근 권한·허용 채팅방·발신자·호출어·로그 섹션은 그대로 있습니다.
3. 기존 ② 작동 설정 다음의 **②-A Python 명령 엔진 (Termux)**에서 `Python 연결 활성화`를 ON으로 바꿉니다.
4. Termux `.env`의 `ANGAE_TOKEN`을 **토큰 입력란**에 붙여넣습니다.
5. **Python 연결 설정 저장**을 누르고 **Python 서버 연결 테스트**를 실행합니다.
6. `🐍 Python 연결 정상 (v0.2.0)`가 표시되어야 합니다.

`PYTHON_HEALTH_OK` / `PYTHON_HEALTH_FAILED` 로그가 기존 SQLite 이벤트 목록에 추가됩니다. 토큰 값은 로그에 저장하지 않습니다.

## 6. S25+에서 실행할 시험 명령

먼저 기존 기능을 확인합니다.

```text
앙개야 테스트
앙개야 상태
앙개야 도움말
```

그다음 Python 새 기능을 확인합니다.

```text
앙개야 계산 123*456
앙개야 계산 (10+2)*3
앙개야 시간
앙개야 서버상태
앙개야 계산 1/0
```

Python 오류 예: Termux 서버를 꺼두고 `앙개야 계산 12*3`을 전송하면 `⚠️ 앙개봇 Python 연결 실패` 응답과 `PYTHON_FAILED` 로그가 남고 기존 `앙개야 상태`는 계속 정상 작동해야 합니다.

## 7. GitHub 업로드

Windows에서 **실기기 검증에 성공한 후** 다음 명령으로 소스와 문서를 추가합니다.

```powershell
cd D:\stockproj\AngaeBotBridge
git status
git diff

git add app/src/main core docs/UPGRADE_v0.2.0.md docs/TEST_PLAN_v0.2.0.md CHANGELOG_v0.2.0.md scripts/apply-v0.2.0.ps1
git diff --cached --stat
git diff --cached
git commit -m "feat: integrate Termux FastAPI command engine v0.2.0"
git push origin main
```

**토큰, `.env`, `*.db`, 실행 로그, 디버그 APK를 커밋하지 마세요.** `.gitignore`는 기존 규칙을 유지합니다.

배포 태그는 실기기 검증 완료 후에만:

```powershell
git tag -a v0.2.0 -m "AngaeBot Bridge and Termux Python Core v0.2.0"
git push origin v0.2.0
```

## 8. 선택: Termux:Boot 자동 시작

S20+에 Termux:Boot를 **같은 출처**에서 설치 후 앱을 한 번 실행합니다.

```bash
cd ~/angaebot/core
bash scripts/setup-boot.sh
```

재부팅 후 Python 서버가 시작되는지 반드시 확인하세요. 절전 정책과 제조사 백그라운드 제한으로 지속 실행은 보장되지 않습니다. 자동으로 장시간 실행할 필요가 없다면 이 단계를 생략하세요.

## 9. 문제 해결

| 증상 | 확인 |
|---|---|
| Android APK가 빌드되지 않음 | JDK17, SDK36, 오류 첫 줄, `--stacktrace` |
| Python 연결 실패 | Termux에서 `bash scripts/start-termux.sh`, loopback 8765 포트 |
| 인증 실패 401 | `ANGAE_TOKEN`과 UI 입력한 토큰이 일치하는지 |
| Python 모듈 설치 실패 | Termux Python 버전 및 Rust/pydantic-core 빌드 로그 |
| Python 명령만 답이 없음 | `PYTHON_REQUEST`, `PYTHON_FAILED`, `REPLY_UNAVAILABLE` |
| 이전 명령도 안 됨 | 알림 접근 권한, 승인된 채팅방/발신자, 자동응답 ON |
| 기존 데이터가 사라짐 | 앱 제거 여부, package ID/디버그 서명, 보존 여부를 확인 |

## 보안 참고

현재 허용 사용자 판정은 **카카오톡 알림의 표시 이름**만 활용합니다. 채팅방/발신자 ID를 인증한 것은 아닙니다. v0.2.0은 계산·시간·서버상태 같은 안전한 명령만 구현하며, 파일 삭제·주식 주문·임의 시스템 명령은 의도적으로 제공하지 않습니다.
