# AngaeBot v0.3.0 — Galaxy S20+ AI 대화 엔진 설치 가이드

기존 v0.2.0(Android) + v0.2.1(runit/watchdog) + v0.2.2(Termux Python 패키지 수정) 기반에서 **기존 기능·UI·SQLite jobs/events·Android 로그·.env 토큰을 모두 보존**하는 추가 버전입니다.

## 0. 무엇이 추가됐나

- Python Core `/v1/commands`: `질문`, `요약`, `AI상태`, `대화초기화`
- 기존 `계산`, `시간`, `서버상태`, Android `테스트`, `상태`, `도움말` 유지
- OpenAI API 또는 Ollama(미니 PC) 호환 Chat Completions API 선택
- 대화 문맥: `(room,sender)`별 최근 6회만 전달. 새 `ai_sessions`, `ai_turns` 테이블 추가.
- 문맥 초기화는 세대 번호만 올려 기록을 보존합니다. 이전 로그/AI 질문 기록은 삭제하지 않습니다.
- AI 기본 OFF, Android 자유 자연어 스위치 별도 OFF(기존 모르는 명령 동작 유지).
- API 인증키는 Termux `.env`에만 저장. Android에는 기존 Python 내부 토큰만 암호화 저장.
- 모든 로그와 DB를 **보존**, 기존 Core runit + watchdog + 부팅 스크립트 유지.
- Android 로그 내보내기 파일명만 호환성 위해 영문으로 변경하며 내용/메뉴는 유지.

## 1. 현재 상태를 백업

Windows PowerShell:

```powershell
cd D:\stockproj\AngaeBotBridge
git status
# clean 상태를 권장. 수동 수정한 파일이 있으면 먼저 백업/커밋하세요.
```

S20+ SSH는 `ssh -p 8022 u0_a435@10.1.1.202`.

## 2. Windows 소스 패치 (패치 ZIP)

Downloads 폴더에 `GPT_20261105_AngaeBot_v0.3.0_UpdatePatch.zip`을 저장했다고 가정합니다.

```powershell
$zip = "$env:USERPROFILE\Downloads\GPT_20261105_AngaeBot_v0.3.0_UpdatePatch.zip"
$dest = "$env:TEMP\AngaeBotUpdate030"
Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force
powershell -ExecutionPolicy Bypass -File "$dest\AngaeBotBridge\scripts\apply-v0.3.0.ps1" -TargetRoot "D:\stockproj\AngaeBotBridge"
cd D:\stockproj\AngaeBotBridge
git diff --stat
git status
```

패치 스크립트가 기존 수정 대상 파일을 별도 백업 폴더에 저장합니다. `.env`, `.git`, DB, 로그, 터미널 서비스 설정은 복사·삭제하지 않습니다.

## 3. Android 앱 업데이트

```powershell
cd D:\stockproj\AngaeBotBridge
$jdk17=Get-ChildItem "C:\Program Files\Eclipse Adoptium\jdk-17*" -Directory | Select-Object -First 1 -ExpandProperty FullName
$env:JAVA_HOME=$jdk17
$env:Path="$jdk17\bin;$env:Path"
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug --stacktrace

$adb="$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb devices
& $adb install -r ".\app\build\outputs\apk\debug\app-debug.apk"
```

앱을 삭제/데이터 초기화하지 마세요. 기존 허용목록/로그/암호화 토큰이 유지되어야 합니다.

## 4. Python Core v0.3.0 업그레이드 — S20+ 데이터 보존

Windows Downloads의 `GPT_20261105_AngaeBot_PythonCoreUpdate_v0.3.0.zip` 전송:

```powershell
ssh -p 8022 u0_a435@10.1.1.202 "mkdir -p ~/angaebot"
scp -P 8022 "$env:USERPROFILE\Downloads\GPT_20261105_AngaeBot_PythonCoreUpdate_v0.3.0.zip" "u0_a435@10.1.1.202:~/angaebot/"
```

S20+ Termux SSH에서:

```bash
cd ~/angaebot/core
stamp=$(date +%Y%m%d_%H%M%S)
mkdir -p "$HOME/angaebot/backups/v030_$stamp"
cp -p app/main.py app/commands.py "$HOME/angaebot/backups/v030_$stamp/"
# 기존 명령/로그/토큰/DB 및 runit 구성은 유지합니다.
unzip -o "$HOME/angaebot/GPT_20261105_AngaeBot_PythonCoreUpdate_v0.3.0.zip" -d "$HOME/angaebot/core"

# 기존 Python 환경 그대로 사용, pip/Rust 재설치 불필요
.venv/bin/python -m unittest discover -s tests -v

# 실행 중인 runit 서비스 재시작 (watchdog 유지)
bash scripts/restart-autostart.sh
bash scripts/status-autostart.sh
```

`HEALTH_OK`와 `앙개야 서버상태` 정상 응답을 먼저 확인합니다.

## 5. AI 제공자 설정 (선택, 최초에는 OFF)

AI 기능을 처음 사용한다면 Termux에서:

```bash
cd ~/angaebot/core
.venv/bin/python scripts/configure-ai.py
```

제공자 `openai`를 고르면 모델 기본값은 `gpt-6-luna`이고 API 키는 숨겨서 입력합니다. **ChatGPT Plus/Pro 구독과 API 사용요금은 별개**입니다. 사용자 요청이 OpenAI API로 전달되며, 유료 호출이 발생할 수 있습니다.

`ollama`를 고르면 S20+가 아닌 **미니 PC에서 실행 중인 Ollama 서버의 실제 LAN IP**를 입력합니다. 예: `http://10.1.1.100:11434/v1`은 예시이며 실제 IP/모델명으로 교체해야 합니다. Ollama HTTP는 사설 IP/loopback에만 허용하며, 인터넷으로 포트를 포워딩하지 마세요.

설정 후 재시작:

```bash
bash scripts/restart-autostart.sh
bash scripts/status-autostart.sh
.venv/bin/python scripts/configure-ai.py --status
```

설정을 끄려면:

```bash
.venv/bin/python scripts/configure-ai.py --disable
bash scripts/restart-autostart.sh
```

`.env`와 `.env.backup.*`에는 민감한 키가 들어 있으니 외부에 올리거나 채팅에 붙여넣지 마세요. `.env` 갱신 시 기존 `ANGAE_TOKEN`은 유지되므로 Android 앱의 Python 토큰을 다시 입력할 필요는 없습니다.

## 6. 카카오톡 실기기 테스트

S20+의 Android Bridge v0.3.0 관리 화면 ②-A에서 기존 Python 연결은 ON으로 유지합니다. **자연어 자동 전달 스위치는 일단 OFF**로 유지하세요.

S25+에서 아래 순서대로 테스트합니다.

1. `앙개야 테스트` → 기존 Android 기능
2. `앙개야 계산 123*456` → `56,088` / 기존 FastAPI 기능
3. `앙개야 시간`, `앙개야 서버상태` → 기존 명령
4. `앙개야 AI상태` → AI ON/OFF, 제공자/모델 표시
5. AI 설정 ON인 경우 `앙개야 질문 안녕?`, `앙개야 요약 다음 글을 요약해줘 ...`
6. `앙개야 대화초기화` 후 후속 질문 → 이전 문맥 사용하지 않음
7. Android ②-A에서 자연어 스위치 ON+저장 → `앙개야 배드민턴 스매시 팁 알려줘` 시험

AI가 OFF이거나 공급자가 접속되지 않으면 오류 메시지가 나오지만, 기존 계산/시간/상태 명령은 계속 동작합니다. 최신 뉴스/주가 실시간 조회는 아직 연결하지 않았으므로 AI 답을 실제 데이터로 단정하지 마세요.

**주의**: 카카오톡 알림 기반 빠른 답장은 긴 답변이나 20초 이상 지연된 AI 응답에서 실패할 수 있습니다. 타임아웃은 Python 최대 23초, Android AI 25초이며 기존 명령은 Android 4초로 유지됩니다.

## 7. Git 반영 (실기기 검증 뒤)

```powershell
cd D:\stockproj\AngaeBotBridge
git status
git diff --check
git add app core/app core/scripts/configure-ai.py core/tests/test_ai.py core/tests/test_ai_api.py core/tests/test_ai_config.py core/.env.example docs/UPGRADE_v0.3.0.md docs/TEST_PLAN_v0.3.0.md CHANGELOG_v0.3.0.md scripts/apply-v0.3.0.ps1
git diff --cached --stat
git diff --cached --check
git commit -m "feat(ai): add opt-in OpenAI and Ollama conversation engine v0.3.0"
git push origin main
```

`.env` 인증키와 `data` SQLite 파일을 `git add -f`로 강제 추가하지 마세요.

## 보안/개인정보/한계

- 기존 카카오톡 알림 표시 이름으로만 발신자를 판별하므로 고신뢰 인증이 아닙니다.
- AI를 켜면 질문과 제한된 이전 문맥이 설정된 AI 제공자로 전송됩니다. 민감정보는 보내지 마세요.
- Python `jobs` 테이블에는 기존처럼 명령 인수가 저장됩니다. AI 문맥 ON 시 `ai_turns`에도 질문/응답이 별도로 남습니다. `대화초기화`는 기록 삭제 기능이 아닙니다.
- API 자체의 원격 최신정보 조회, 주식 주문, 웹 검색, 파일·기기 제어 기능은 추가하지 않았습니다.
- 서버 운영/서비스 재시작/로그 기록과 기존 Android UI/로그를 보존하는 추가 업데이트입니다.
