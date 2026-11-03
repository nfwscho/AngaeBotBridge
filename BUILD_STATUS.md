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
