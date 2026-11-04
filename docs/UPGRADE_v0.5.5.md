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
