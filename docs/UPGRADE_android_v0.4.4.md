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
