# 앙개봇 통합 설치·업그레이드 가이드

> 최신 운영 절차를 먼저 기록하고, 이전 버전별 업그레이드 문서의 전문을 아래 최신순으로 보존합니다.
> 설치·업그레이드 절차는 앞으로 `docs/UPGRADE.md`만 수정합니다.

## 현재 기능 브랜치 배포 (Android Bridge v0.4.9 / Core v0.6.1)

- 프로젝트: `D:\stockproj\AngaeBotBridge` / 원격 저장소 `nfwscho/AngaeBotBridge`
- 테스트용 기능 브랜치: `feature/global-shortcut-menus-20261106` (사용자 승인 전 main 병합 금지)
- S20+ USB 디버깅을 허용하고, 기존 Android 앱을 **삭제하지 않고** `-InstallAndroid`로 덮어쓰기 설치합니다.
- 배포는 GitHub Actions 동일 SHA 전체 성공을 검사한 뒤 staged Python 모듈을 업로드하고 Core를 재시작한 후, APK 설치/검증을 수행합니다.
- `.env`, 기존 SQLite DB/메시지·명령 로그, 사용자 설정, 기존 앱 허용목록, watchdog/sshd를 보존합니다.
- **배포 스크립트를 수정한 릴리스**이므로 새 소스를 먼저 `git pull --ff-only`로 갱신해야 실행 중인 PowerShell이 이전 스크립트를 읽지 않습니다.
- 인증된 Core health `상`과 운영 조회 `설 2`에서 실제 S20+에 적용된 브랜치·커밋 확인이 가능합니다.
- GitHub main HEAD는 S20+ 실제 배포 기록과 다를 수 있습니다. 배포 성공 여부를 추측하지 않습니다.

```powershell
cd D:\stockproj\AngaeBotBridge
git pull --ff-only origin feature/global-shortcut-menus-20261106
if ($LASTEXITCODE -ne 0) { throw 'Git update failed; deployment stopped' }
.\deploy-angaebot.ps1 -Branch "feature/global-shortcut-menus-20261106" -InstallAndroid
```

## 구버전 업그레이드 지침 전문 (최신순)



---

## 기존 업그레이드 원문: docs/UPGRADE_v0.5.10.md

# AngaeBot 미국 시세 복구 v0.5.10 설치·검증

Windows CMD에서 실행:

```bat
cd /d D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.10.ps1"
```

`[OK] AngaeBot Python Core v0.5.10 installed successfully`와 `deployment completed`를 확인하세요. 이전 앱이나 DB를 삭제하지 마세요. Android APK는 v0.4.5 그대로 사용합니다.

카카오톡에서 `주 반도체`, `주 메모리7` 실행; 미국 시세가 재개되면 가격·등락률이 표시되며 출처 하단에 `나스닥 확정 종가` 또는 `네이버 해외 확정 종가`가 나올 수 있습니다. **이 수치는 실시간 호가가 아니라 확정 정규장 종가입니다.**

모든 미국 제공처가 실패하면 다음 명령으로 서버 진단을 확인하세요. 원본 응답/토큰은 로그에 기록하지 않습니다.

```bat
ssh -p 8022 u0_a435@10.1.1.202 "grep 'US_QUOTE_' ~/angaebot/core/logs/server.log | tail -12"
```

기존 서버 소스 백업은 `~/angaebot/backups/core_pre_v0510_*`에 보관되며 오류가 나면 자동 복원합니다. `.env`, 데이터베이스, jobs/events, Android 앱의 허용목록과 로그는 수정하지 않습니다.

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.5.9.md

# AngaeBot Python Core v0.5.9 — Windows CMD 설치

```bat
cd /d D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.9.ps1"
```

성공 시 `[OK] AngaeBot Python Core v0.5.9 installed successfully`를 확인하세요. 실패한 경우 이전 소스를 복원하며, 오류 메시지를 보존해 진단합니다.

**APK 재설치 금지/불필요.** Galaxy S20+ Termux의 기존 Python Core만 갱신합니다. 기존 SQLite/로그/.env/Android 설정은 삭제하지 마세요.

카카오톡 시험: `주 반도체`, `주 메모리7`, `3`(번호로 분석) / `앙개야 서버상태`.
시세 목록 마지막에 `시세 출처 · 기준시각` 다음 `국내 / 미국 / 일본`이 한 번씩 표시되고, 각 종목마다 출처 줄이 반복되지 않는지 확인합니다.

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.5.8.md

# 앙개봇 미국 주식 시세 장애 보완 v0.5.8 — 설치 및 점검

## 1. Windows CMD 실행
```bat
cd /d D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.8.ps1"
```
배포 성공: `[OK] AngaeBot Python Core v0.5.8 installed successfully` / `deployment completed`.
기존 Termux 서버·.env·DB·로그/Android APK는 유지된다. **APK 재빌드/삭제/재설치는 금지**.

## 2. 카카오톡 시험
- `주 메모리7` → 미국 5종목 중 적어도 일부의 가격 및 공급자 확인
- `주 반도체` → 마이크론·샌디스크·웬디·씨게이트 확인
- `주 메모리7` → `3` → 마이크론 분석(단 과거 시세 공급자도 별도 장애 가능)
- `앙개야 상태`, `주`, `주 분 삼성전자` → 기존 기능 정상 여부
- `🔋 S20+` 잔량 표시 유지

미국 Yahoo가 정상인 경우 종전 미국 시세 한 줄을 유지한다. Yahoo가 실패하고 나스닥 웹 시세가 검증을 통과한 경우 다음과 같은 별도 정보를 표시한다.
```text
3. 마이크론 : $... (...%)
   └ 미국 11/04 16:00 ET · 나스닥 공개 시세(지연 여부 미확인)
```
이 문구가 보이면 Nasdaq 보조 데이터가 사용된 것이다. 실제 숫자·시각은 공급자가 제공해야 하며, 임의로 보충하지 않는다.

## 3. 계속 조회 불가일 때
Yahoo와 Nasdaq 웹이 모두 S20+ Termux에서 HTTP 403/429를 반환하거나 데이터 형식/거래시각이 불완전하면 안전하게 `조회 불가`가 유지된다.
이때 Termux 서버 콘솔/로그의 `US_QUOTE_FAILED` 진단 행에서 미국 티커별 `Yahoo HTTP 429`, `나스닥 HTTP 403` 등 응답 분류를 확인해 추가 공급자를 선택한다. 해당 로그에는 계정 인증키가 없다.
개인 테스트 이외의 재배포/상업적 사용 시 각 공급자의 시세 라이선스를 확인해야 한다.

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.5.7.md

# AngaeBot v0.5.7 설치 안내 — Android APK 재설치 불필요

Windows CMD(`D:\stockproj\AngaeBotBridge`)에서 다음 순서로 실행하세요.

```bat
cd /d D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.7.ps1"
```

정상 설치되면 `[OK] AngaeBot Python Core v0.5.7 installed successfully`를 확인합니다.

카카오톡에서 `앙개야 서버상태` (0.5.7), `주 메모리7` (한국 KRX 시각/지연·장전/장후), `3` (마이크론 기존 분석 유지), `주 분 삼성전자`를 시험하세요.

기존 Android Bridge v0.4.5/배터리 표시/숫자 선택에는 변화가 없습니다. APK 삭제·재설치·데이터 초기화 금지.
실제 한국 본장 장중에 KRX 체결시각과 시세 갱신 여부를 확인해야 '실시간표시(지연 0분)'가 표시됩니다.
마감 후에는 `장마감 종가`가 정상이며, 시간외 세션은 API 응답에 시세가 있을 때만 별도 표시됩니다.
네이버 폴링 API의 문서화·서비스 수준 보장은 없습니다.

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.5.6.md

# 앙개봇 v0.5.6 / Android v0.4.5 설치·검증

현재 Core v0.5.5, Android Bridge v0.4.4 환경에 적용하는 증분 업데이트입니다.

## 1. Core 먼저 배포 (Windows CMD)

```bat
cd /d D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.6.ps1"
```

`Ran 142 tests ... OK` 및 `[OK] AngaeBot Python Core v0.5.6 installed successfully.` 확인. 실패하면 배포기가 백업 소스로 복원하며 기존 운영 DB·로그는 수정하지 않음.

## 2. Android Bridge 덮어쓰기 설치

```bat
gradlew.bat :app:clean :app:testDebugUnitTest :app:assembleDebug
"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" devices
"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" install -r "app\build\outputs\apk\debug\app-debug.apk"
"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" shell dumpsys package kr.co.angaebot.bridge | findstr /C:"versionCode=" /C:"versionName="
```

**주의:** Gradle 출력에 `BUILD SUCCESSFUL`이 보일 때에만 `adb install -r` 실행. `versionCode=9` 및 `versionName=0.4.5` 확인. 기존 앱 삭제/데이터 초기화 금지. 서명 충돌 시에도 삭제하지 말고 오류를 먼저 확인.

## 3. 카카오톡 동작 확인

- `주 메모리7` → `1. 삼성전자`, `2. 하이닉스`, `3. 마이크론`, ... `8. 웬디` 포함.
- 해당 답장에서 숫자 `3`만 전송 → 마이크론(MU) 과거 5거래일·1개월·3개월 분석 및 S20+ 배터리 줄.
- 다시 `주 메모리7` → `8` → 웬디(WDC) 분석.
- `주` → `2`(메모리7 현재 시세) → `1`(삼성전자 분석)도 동작.
- `주 반도체` 또는 `주 미국시총10`(등록된 사용자 그룹만) → 표시된 번호로 해당 종목 분석. 10종목 그룹의 `10`도 지원.
- 5분 후, 메뉴가 열리지 않았을 때, 다른 방·발신자가 보내는 숫자 `1`은 무시. `10개`, `1만원`, `123`은 항상 숫자 메뉴가 아님.
- `앙개야 상태`, `주 분 하이닉스`, `주 목록`, `주` 등 기존 명령과 배터리 표시 확인.

## 운영 안전성

업데이트는 기존 FastAPI jobs/events, stock_groups/items, AI 데이터, 운영 토큰, Android 앱 설정, 로그 및 Watchdog·SSH를 보존합니다. AI API를 켜거나 가격 알림·매매를 실행하지 않습니다.

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.5.5.md

# AngaeBot 주식 숫자 메뉴 v0.5.5 설치 안내

Windows CMD에서:

```bat
cd /d D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.5.ps1"
```

`[OK] ... Core v0.5.5 installed successfully`와 전체 Python unittest OK를 먼저 확인하세요.

다음 단계로 Android APK를 다시 빌드하고 기존 앱에 설치합니다.

```bat
gradlew.bat :app:testDebugUnitTest :app:assembleDebug
"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" devices
"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" install -r "app\build\outputs\apk\debug\app-debug.apk"
"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" shell dumpsys package kr.co.angaebot.bridge | findstr /C:"versionCode=" /C:"versionName="
```

설치된 Android Bridge의 `versionCode=7`, `versionName=0.4.3`을 확인하세요.
기존 APK를 삭제하거나 Android 앱 데이터를 초기화하면 기존 설정·로그가 소실될 수 있으므로 **절대 삭제하지 마세요.** 이전 디버그 APK와 인증서가 다르면 오류만 확인하고 삭제하지 마세요.

카카오톡 테스트:
1. `주`로 숫자 메뉴 표시
2. `1`로 내 최근 주식 조회 목록 표시(있을 때)
3. 목록에서 `1`로 최근 명령 재실행
4. `주` → `6` → `1`로 삼성전자 분석
5. 메뉴 바깥에서 입력한 숫자 `1`은 무시되는지 확인
6. `주 분 마이크론`, `앙개야 상태`, `주 목록` 등 기존 명령 작동 확인

`반도체`와 `미국시총10`은 해당 사용자에게 그룹이 실제 등록되어 있어야 시세 조회가 가능합니다. 메뉴 명령은 그룹을 자동으로 생성하거나 삭제하지 않습니다.

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.5.4.md

# AngaeBot Python Core v0.5.4 배포 안내

Windows PowerShell:
1. cd D:\stockproj\AngaeBotBridge
2. git status
3. git pull --ff-only origin main
4. git log -1 --oneline
5. powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.4.ps1"

성공 기준: Ran 129 tests / OK / AngaeBot Python Core v0.5.4 installed successfully.
배포 전 시간대 데이터 검증, 원본 백업, 전체 회귀 테스트 및 인증된 /v1/health의 버전 확인.
오류 시 안전 복원. Android APK, 모든 서버 로그, SQLite 작업 기록, stock_groups, 사용자 그룹과 AI OFF 유지.
카카오톡 확인: 앙개야 서버상태 / 앙개야 주식 목록 / 앙개야 주식 분석 마이크론 / 앙개야 주식 분석 하이닉스.
가격 알림·자동 발신·자동 매매·OpenAI API 추가 없음.

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.5.3.md

# AngaeBot v0.5.3 — 한글 종목명 분석 업데이트

1. Windows PowerShell: `cd D:\stockproj\AngaeBotBridge`.
2. `git status`로 변경 사항을 확인하고 깨끗한 상태이면 `git pull --ff-only origin main`.
3. `powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.3.ps1"` 실행.
4. Termux가 시장 시간대를 확인하고 누락 시에만 tzdata를 설치. 실패하면 Core 소스 적용/재시작 전에 중단.
5. Python 전체 128건 회귀 테스트와 API health v0.5.3 확인. 문제 생기면 이전 소스 자동 복원.
6. 카카오톡: `앙개야 서버상태`, `앙개야 주식 분석 마이크론`, `앙개야 주식 분석 삼성전자`, `앙개야 주식 분석 하이닉스`.
7. 미국 이름도 가능: `앙개야 주식 분석 엔비디아`, `앙개야 주식 분석 애플`, `앙개야 주식 분석 구글`.
8. 등록 별칭 `앙개야 주식 추가 투자 NVDA 내GPU`는 `앙개야 주식 분석 내GPU`로 조회 가능.
9. 원래 티커 입력·메모리7/반도체/미국시총10은 그대로 지원하며 Android APK를 다시 설치할 필요 없음.
10. DB·로그·토큰·AI OFF는 유지. 주식 알림·자동 발송·스케줄러는 생성하지 않음.

## v0.5.3 배포 검증 핫픽스
- 2026-11-05 재시작 직후 구버전 `0.5.2`를 요구하던 검사를 `0.5.3`으로 수정했다.
- Windows에서 `git pull --ff-only origin main`으로 핫픽스를 받고 기존 `scripts/deploy-v0.5.3.ps1`을 다시 실행한다.
- Python 회귀 테스트 통과 후 `[OK] AngaeBot Python Core v0.5.3 installed successfully`가 출력되는지 확인한다.
- 기존 DB·로그·고객별 그룹은 삭제하지 않는다. `ResourceWarning`만 발생할 때는 별도 정리 대상으로 분류한다.

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.5.2.md

# AngaeBot v0.5.2 업데이트 가이드

1. Windows PowerShell에서 `cd D:\stockproj\AngaeBotBridge`.
2. `git status`로 기존 미커밋 변경 확인. 변경이 없으면 `git pull --ff-only origin main`.
3. `git log -1 --oneline` 출력에서 v0.5.2 커밋 확인.
4. `powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.2.ps1"` 실행.
5. 성공 시 Python 전체 회귀 테스트 `OK`, `AngaeBot Python Core v0.5.2 installed successfully` 확인.
6. 카카오톡에서 `앙개야 서버상태`, `앙개야 주식 메모리7`, `앙개야 주식 분석 MU`, `앙개야 주식 분석 005930`, `앙개야 주식 분석 메모리7`, `앙개야 주식 분석 미국시총10` 테스트.
7. Android APK는 그대로 사용, OpenAI API OFF 유지. 과거 시세는 장마감 기준/5분 캐시/무료 지연 정보.
8. 실패 시 배포기가 이전 소스 자동 복원. 기존 .env/SQLite/logs/그룹 데이터는 변경하지 않음.
9. 1개월/3개월 지표는 21/63거래일의 수익률과 연율화 실현변동성으로 구성. 데이터를 확보하지 못한 기간은 `데이터 부족`.
10. 임의 알림·스케줄러·카카오톡 자동 선제 발송·주식 거래 기능은 구현하지 않음.

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.5.1.md

# AngaeBot v0.5.1 — Galaxy S20+ update instructions

Existing v0.5.0 server and app must be operational. Python Core update only; no new APK, pip packages, OpenAI key or paid quote subscription.

On Windows PowerShell:

```powershell
cd D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.5.1.ps1"
```

The deployer uses SSH `u0_a435@10.1.1.202` port `8022`; it uploads selected source/test files, backs up originals on Termux, runs syntax and complete unittest, restarts only the FastAPI runit service after successful tests and checks authenticated health `version=0.5.1`. Source changes are rolled back when validation fails. Existing `.env`, `.venv`, SQLite DB, all logs, boot script, SSH, watchdog and Android data remain intact.

In KakaoTalk send:

```
앙개야 서버상태
앙개야 주식 프리셋 미국시총10
앙개야 주식 미국시총10
앙개야 주식 목록
```

This preset registers **ten US-incorporated companies** as of the November 4, 2026 ranking snapshot. Alphabet is a single issuer represented by GOOGL. It includes the publicly listed SpaceX ticker `SPCX`; no foreign ADR such as TSM. The group is an editable static snapshot, not a daily auto-rebalanced market-cap ranking. Each quote is still from a public, potentially delayed and unofficial service; unavailable stocks remain `조회 불가`, never invented.

A previously created group named `미국시총10` will **not** be overwritten: delete it deliberately (only if desired), or use manual add/remove. The built-in original `메모리7` always retains exactly 8 positions. Existing `반도체` and other groups persist.

For manual registration, use `앙개야 주식 그룹생성 미국시총10` followed by ten separate `앙개야 주식 추가 미국시총10 TICKER 별칭` messages **instead of** running the preset. This is not necessary when using the one-command preset.

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.5.0.md

# AngaeBot Python Core v0.5.0 설치/테스트 가이드

## 1. Windows Git 동기화

```powershell
cd D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
```

## 2. 기존 S20+에 Python Core 자동 적용 (Android 재설치 없음)

```powershell
cd D:\stockproj\AngaeBotBridge
powershell -NoProfile -ExecutionPolicy Bypass -File '.\scripts\deploy-v0.5.0.ps1'
```

- 기존 SSH: `u0_a435@10.1.1.202:8022`.
- 업데이트 스크립트는 정확히 7개 Python 소스/테스트와 설치 스크립트 1개만 전송.
- 전송 → 기존 소스 날짜별 백업 → py_compile → 전체 unittest → Core만 runit 재시작 → 인증 Health `0.5.0` 확인.
- 배포/테스트 실패 시 기존 소스를 복원하며 SQLite/로그/인증키/Android/SSH/watchdog은 보존.
- `httpx`는 이전 FastAPI 테스트 환경에 이미 설치돼 있어야 함; 신규 Python 의존성 설치는 필요 없음.
- Windows PowerShell의 `git pull`이 실패하면 소스를 강제 덮어쓰지 말고 변경 파일부터 점검.

## 3. 카카오톡 실제 실행

```text
앙개야 서버상태
앙개야 주식 메모리7
앙개야 주식 목록
앙개야 주식 그룹생성 반도체
앙개야 주식 추가 반도체 MU 마이크론
앙개야 주식 추가 반도체 005930 삼성전자
앙개야 주식 추가 반도체 285A.T 키오시아
앙개야 주식 반도체
앙개야 주식 삭제 반도체 MU
앙개야 주식 목록
```

그룹 삭제는 반드시 `앙개야 주식 그룹삭제 반도체 확인`이라고 입력해야 합니다. 메모리7은 삭제·편집할 수 없습니다.

## 4. 장애 확인

```powershell
ssh -p 8022 u0_a435@10.1.1.202 'cd ~/angaebot/core && bash scripts/status-autostart.sh'
ssh -p 8022 u0_a435@10.1.1.202 'cd ~/angaebot/core && .venv/bin/python scripts/diagnose-autostart.py'
```

Health 버전이 `0.5.0`인지 확인합니다. 그룹 시세 일부가 조회 불가여도 계산·시간·서버상태는 유지되어야 합니다.

## 개인정보 및 시세 참고

- 사용자별 분리는 카카오톡 알림에 표시된 발신자/방 이름을 기준으로 하므로 고신뢰 인증이 아닙니다.
- 신규 그룹 종목은 서버 SQLite에 저장됩니다. `주식 그룹삭제 ... 확인`은 해당 그룹 및 등록 종목만 삭제하고 과거 명령 로그는 보존합니다.
- 네이버 금융·Yahoo 등 무료 시세는 지연되거나 접근이 제한될 수 있으며 실제 매매용 호가가 아닙니다.
- OpenAI API/예약 메시지 발송/주식 주문을 자동 실행하지 않습니다.



---

## 기존 업그레이드 원문: docs/UPGRADE_android_v0.4.4.md

# 앙개봇 Android Bridge v0.4.4 업데이트

Python Core를 다시 배포하지 않고 Android APK만 업데이트합니다.

Windows CMD:

```bat
cd /d D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline

gradlew.bat :app:clean :app:testDebugUnitTest :app:assembleDebug

"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" devices
"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" install -r "app\build\outputs\apk\debug\app-debug.apk"
"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" shell dumpsys package kr.co.angaebot.bridge | findstr /C:"versionCode=" /C:"versionName="
```

- `BUILD SUCCESSFUL` 확인 후에만 `adb install -r`을 실행합니다.
- 설치 후 `versionCode=8`, `versionName=0.4.4`인지 확인합니다.
- 앱을 삭제하거나 데이터 초기화하지 마세요. 기존 Android 서명 인증서가 동일해야 덮어쓰기됩니다.
- 카카오톡에서 `주`, `1`, `주 분 삼성전자`, `앙개야 상태`를 순서대로 시험하고 답장 맨 아래 배터리 수치를 확인하세요.
- `REPLY_ATTEMPT`, `REPLY_REQUESTED` 등 기존 로그는 그대로 유지하며 별도 전원 권한은 요구하지 않습니다.
- 배터리 잔량(%)과 충전 여부만 표시합니다. 배터리 실제 수명/성능 건강도(SOH)는 이 수치로 판단할 수 없습니다.

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.4.3.md

# 앙개봇 v0.4.3 업그레이드 (Python Core만)

1. Windows PowerShell: `cd D:\stockproj\AngaeBotBridge`
2. `git status` 후 미커밋 변경 사항이 없으면 `git pull --ff-only origin main`
3. `powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.4.3.ps1"`
4. 기대 결과: Python 전체 테스트 `OK`, `[OK] AngaeBot Python Core v0.4.3 installed successfully`.
5. S25+ 카카오톡: `앙개야 서버상태` → Python `v0.4.3`; `앙개야 주식 메모리7` → 8종목 출력.
6. 키오시아만 여전히 조회 불가라면 S20+에서 `cd ~/angaebot/core && .venv/bin/python scripts/diagnose-market.py`로 Yahoo Global/Yahoo Japan/Rakuten 원인을 구분하여 확인.

본 업데이트는 Android APK 수정 없이 SSH/S20+ Python Core만 수정합니다. 기존 `.env`, `.venv`, data/SQLite, logs, Android 앱·UI·로그·허용목록, SSH/watchdog 서비스는 보존됩니다.

무료 제공처의 접속·파싱 문제는 실기기 네트워크에서만 최종 확인할 수 있습니다. 가격을 임의로 채우지 않습니다. OpenAI API는 OFF를 유지합니다.

---

## 기존 업그레이드 원문: docs/UPGRADE_android_v0.4.2.md

# Android Bridge v0.4.2 단축어 설치 안내

1. Windows PowerShell에서 `cd D:\stockproj\AngaeBotBridge` 실행.
2. `git status` 확인 후 `git pull --ff-only origin main` 실행.
3. `git log -1 --oneline`으로 Android Bridge v0.4.2 단축어 커밋 확인.
4. Gradle Wrapper가 없을 때만 `powershell -ExecutionPolicy Bypass -File .\scripts\prepare-wrapper.ps1` 실행.
5. `.\gradlew.bat :app:testDebugUnitTest`로 기존+단축어 파서 테스트 검증.
6. `.\gradlew.bat :app:assembleDebug`로 새로운 `app\build\outputs\apk\debug\app-debug.apk` 생성.
7. S20+에서 USB 디버깅을 허용하고 `adb devices`로 장치 인식 확인.
8. **기존 앱을 삭제하지 말고**, 이전 디버그 앱과 동일한 서명인 경우 `adb install -r .\app\build\outputs\apk\debug\app-debug.apk`로 덮어쓰기 설치.
9. 알림 접근 권한, 자동응답 ON/OFF, 허용 방/발신자, Python 연결 및 로그가 그대로인지 확인.
10. `앙개야 테스트`(기존 기능), `주`, `주 분 마이크론`, `주 분 삼성전자`, `주 목록` 순으로 점검.
11. 설치 중 인증서 충돌이나 빌드 오류가 발생하면 앱 삭제/데이터 초기화를 하지 말고 오류부터 확인.
12. **Python Core 재배포는 불필요**하며 기존 로그·그룹·메모리7·AI 설정은 변경하지 않음.

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.4.1.md

# 앙개봇 v0.4.1 메모리7 주식 시세 설치 가이드

## 적용 범위
- 기존 Android v0.4.0 + Termux Python Core v0.4.0 기반의 추가 업데이트.
- OpenAI API는 OFF인 상태를 그대로 보존. 무료 비공식 Yahoo Finance 시세만 별도 요청.
- 기존 .env, DB, 모든 로그, Android 앱 데이터와 허용목록, SSH·Watchdog·부팅 스크립트 유지.

## 1. Windows Git Pull
```powershell
cd D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
```

## 2. Python Core 자동 업그레이드
```powershell
cd D:\stockproj\AngaeBotBridge
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.4.1.ps1"
```
- 전송한 소스만 백업·갱신, 전체 Python 테스트 성공 후 runit core만 재시작.
- SSH 연결이 끊어지면 `ssh -p 8022 u0_a435@10.1.1.202`로 복귀한 뒤 `bash ~/angaebot/core/scripts/status-autostart.sh`를 확인.
- 테스트에 실패하면 배포 스크립트가 이전 소스를 복구하며 기존 DB/로그/인증키는 보존.

## 3. Windows Android 빌드/설치 (USB S20+)
```powershell
cd D:\stockproj\AngaeBotBridge
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug
$adb="$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb devices -l
& $adb install -r ".\app\build\outputs\apk\debug\app-debug.apk"
```
- Android 기존 앱을 삭제하지 마세요. `install -r`로 설정과 앱 DB 유지.

## 4. 카카오톡 테스트
- `앙개야 서버상태` → Python v0.4.1
- `앙개야 계산 344*454` → 156,176
- `앙개야 통계` / `앙개야 최근오류` / `앙개야 가동시간` → 기존 기능 유지
- `앙개야 주식 메모리7` → 8개 종목 시세와 등락률 및 현지 거래일 표시
- `앙개야 메모리7` → 같은 결과
- `앙개야 주식 마이크론` → 사용법 안내(아직 임의 종목 조회 미지원)

## 시세 제공 정책
- Yahoo Finance 비공식 chart API이며 지연/장중 변동/접속 제한/중단 가능.
- **KRW(한국), USD(미국), JPY(일본) 각 시장 최근 정규 거래일** 기준으로 표시. 미국 장은 한국 시각으로 전날 거래일일 수 있음.
- 시세 실패 시 값은 임의 계산하거나 과거 값을 '오늘' 값으로 보이지 않음.
- 종목: 005930.KS / 000660.KS / MU / SKHY / SNDK / 285A.T / STX / WDC.
- 유료 OpenAI API와 무관하며 .env 설정을 변경할 필요가 없음.

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.4.0.md

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

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.3.1.md

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

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.3.0.md

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
git add app core/app core/scripts/configure-ai.py core/tests/test_ai.py core/tests/test_ai_api.py core/tests/test_ai_config.py core/.env.example docs/UPGRADE.md docs/TEST_PLAN_v0.3.0.md CHANGELOG_v0.3.0.md scripts/apply-v0.3.0.ps1
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

---

## 기존 업그레이드 원문: docs/UPGRADE_v0.2.0.md

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

git add app/src/main core docs/UPGRADE.md docs/TEST_PLAN_v0.2.0.md CHANGELOG_v0.2.0.md scripts/apply-v0.2.0.ps1
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
