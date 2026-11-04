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
