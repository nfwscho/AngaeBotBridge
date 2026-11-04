# 앙개봇 Bridge v0.1 — 생성 및 검증 기록

- 작성 날짜: 2026-11-03
- 소스: Kotlin Android Studio 프로젝트의 MainActivity, NotificationListenerService, Parser, ReplyManager, SQLite LogRepository, BotConfig 등 전체 소스 포함
- 사용 기술: Android Gradle Plugin 8.11.1 / Gradle 8.14.3 / Kotlin Gradle Plugin 2.2.20 / compileSdk 36
- 기본 설정: 자동응답 OFF, 허용 채팅방·발신자 없음
- 순수 Kotlin CommandParser/LocalCommandExecutor 스모크 검사: **7/7 통과** (`kotlinc 1.9` 환경)
- XML 파싱 확인: **4/4 통과**
- Kotlin 파일 첫 줄 기능 주석, 소스 중괄호 개수 정합성: **확인 완료**
- Android APK 빌드: **미수행** (이 실행 환경에 Android SDK와 Gradle 바이너리 없음)
- Galaxy S20+ 실기기/카카오톡 통신 테스트: **미수행** (실제 기기 접근 불가)
- 최종 Android Studio 컴파일 성공 여부: **미확인** (Windows 사용자의 Android Studio에서 첫 컴파일 필요)
- Gradle wrapper JAR: **미포함**. Windows `scripts/prepare-wrapper.ps1`가 공식 서버에서 수신 및 SHA-256 검증.
- 최종 설치용 APK: **미포함** (사용자 PC에서 `:app:assembleDebug` 후 생성)
- 그룹 채팅방 파싱과 빠른 답장 액션은 카카오톡 버전/안드로이드 알림 상황에 따라 다름.

## 중요한 보안 제약

알림에서 표시되는 채팅방/발신자 이름만으로는 계정 신원을 강력하게 검증할 수 없습니다.
개인용 1:1 시험에만 사용하고 주식 거래, 파일 삭제, PC 원격 명령 등의 고위험 기능을 연결하지 마세요.

## 2026-11-04 Git 문서 보강 (패키지 v0.1.1)

- 추가: `GIT_GUIDE.md`, `.gitattributes`
- 갱신: `.gitignore`의 비밀키·로컬 데이터·빌드 결과 제외 규칙, `README.md` 안내
- Kotlin 소스, AndroidManifest, Gradle 빌드 설정, 기존 설치 가이드, 실행·로그 동작: **변경 없음**
- GitHub로 실제 push하거나 APK를 컴파일하지는 않았습니다.

## 2026-11-04 Wrapper 404 복구 (패키지 v0.1.2)

- 사용자 실환경에서 `services.gradle.org/distributions/gradle-8.14.3-wrapper.jar` 다운로드가 HTTP 404를 반환함.
- 기존 `scripts/prepare-wrapper.ps1`에서 1차 직접 배포 서버, 2차 Gradle GitHub 태그를 사용하도록 개선.
- Gradle 8.14.3 공식 Wrapper JAR SHA-256 검증 유지; 임시 파일 검증 후 설치.
- 문서 갱신: `INSTALL.md`, `README.md`, `GRADLE_WRAPPER_FIX.md`.
- **Kotlin 앱 소스·Gradle 빌드 버전·관리 UI·기존 로그 관련 파일 변경 없음.**
- 실제 Gradle Wrapper 다운로드/Android 빌드/S20+ 검증은 사용자의 환경에서 시행해야 함.

## 2026-11-04 Kotlin 컴파일 오류 수정 (패키지 v0.1.3)

- 사용자 Gradle 로그에서 `MainActivity.kt:72`의 `Unresolved reference: fillViewport` 확인.
- Android `ScrollView#setFillViewport(true)` 호출로 1줄 교체.
- 기존 Kotlin 나머지 파일, UI 화면 구성, 명령 기능, SQLite 로그 로직, 기타 설정은 그대로 유지.
- 단일 라인 diff 검사 통과, Android APK 빌드 결과는 사용자 PC에서 확인 필요.

---

## v0.2.0 변경·검증 현황 (2026-11-04)

- v0.1.3 Android APK는 **사용자 기기에서 빌드/ADB 설치 성공, S25+에 실제 카톡 답장 수신 성공**.
- v0.2.0 Kotlin 통신 연동, 관리 UI ②-A, AndroidKeyStore 토큰 암호화, 로컬 HTTP 네트워크 정책 작성.
- v0.2.0 Python FastAPI/Core: 요청 인증, 계산/시간/서버상태, SQLite 중복 저장/로그 작성.
- Python `unittest` 14건 통과, Kotlin `CommandParser` 회귀 검사 5건 통과.
- Android XML 5개 파싱 검사 통과, Termux 셸 스크립트 구문 검사 통과.
- 이 실행 환경에 Android SDK가 없으므로 v0.2.0 Android APK 빌드 및 S20+ 동작은 **미검증**.
- 추가 실기기 검증: `docs/TEST_PLAN_v0.2.0.md`.
