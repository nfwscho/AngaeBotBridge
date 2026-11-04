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
