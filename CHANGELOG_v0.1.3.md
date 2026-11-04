# 앙개봇 Android Bridge — 빌드 오류 수정 v0.1.3

- 일자: 2026-11-04
- 원인: Kotlin `:app:compileDebugKotlin`에서 `MainActivity.kt` 72행의 `fillViewport` 참조가 확인되지 않음.
- 변경: `ScrollView(this).apply { fillViewport = true }` → `ScrollView(this).apply { setFillViewport(true) }`.
- 영향 범위: `MainActivity.kt` 단 한 줄. 기존 UI 배치/명령 처리/자동응답/설정/SQLite 로그 코드 변경 없음.
- Java 환경: JDK 17 확인 완료(사용자 로그). Android SDK 경로: 오류 단계 통과(사용자 로그).
- 검증: 기존 v0.1.2와 Kotlin 소스 diff 검증(단일 라인 변경). Android SDK 없는 환경이므로 APK 컴파일 미수행.
- 설치: 기존 프로젝트에서 `app/src/main/java/kr/co/angaebot/bridge/MainActivity.kt` 한 파일만 덮어쓰거나 아래 한 줄만 수정.
- 프로젝트의 Wrapper JAR, `local.properties`, Git 설정 등 로컬 변경 파일을 교체하지 마세요.
- 권장 커밋: `fix(android): correct ScrollView fillViewport call (v0.1.3)`

빌드:

```powershell
cd D:\stockproj\AngaeBotBridge
.\gradlew.bat :app:assembleDebug
```
