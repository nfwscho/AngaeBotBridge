# 현재 앙개봇 운영 문서 안내

> 현재 작업 브랜치의 Android Bridge v0.4.9, Termux Python Core v0.6.1 개발 기준입니다.
> `main` 병합은 '앙개봇 메인' 채팅에서 별도 사용자 승인 후 처리합니다.
> 아래 초기 v0.1 설명은 역사 기록이며 현재 구현은 최신 문서를 기준으로 확인하세요.

- [앙개봇 2.0 통합 플랫폼 설계](docs/ARCHITECTURE.md)
- [통합 CHANGELOG (최신순)](CHANGELOG.md)
- [서버·GitHub·소스 운영](docs/OPERATIONS.md)
- [설치·업그레이드](docs/UPGRADE.md)
- [전체 테스트](docs/TEST_PLAN.md)

---

> **v0.1.3 (2026-11-04):** `MainActivity.kt`의 `fillViewport` 컴파일 오류를 `setFillViewport(true)`로 수정. 기존 기능/UI/로그 흐름 보존. `CHANGELOG.md` 참고.

> **2026-11-04 v0.1.2:** `scripts/prepare-wrapper.ps1`의 Gradle 8.14.3 Wrapper 다운로드 실패에 대한 대체 공식 URL과 SHA-256 검증 로직 추가. 자세한 내용은 `GRADLE_WRAPPER_FIX.md` 참고. Kotlin 앱 소스는 v0.1과 동일합니다.

# 앙개봇(AngaeBot) Android Bridge v0.1

> 2026-11-04 Git 관리 문서 보강 패키지 v0.1.1. Kotlin 앱 코드는 기존 v0.1과 동일합니다.

> Galaxy S20+ 보조 카카오톡 계정을 대상으로 하는 **1단계 프로토타입**. APK가 아니라 Android Studio에서 빌드할 수 있도록 준비한 전체 **Kotlin 소스 프로젝트**입니다.

## 구현된 기능

1. 공식 `NotificationListenerService` API로 **카카오톡 패키지 `com.kakao.talk`**의 새 알림과 제거 알림만 감지합니다.
2. **기본 OFF**. 허용할 **채팅방 이름 + 발신자 표시 이름**을 둘 다 설정해야 ON이 됩니다. 이름은 한 줄에 하나씩 정확하게 일치시킵니다.
3. `앙개야 테스트`, `앙개야 상태`, `앙개야 도움말`을 오프라인에서 실행합니다. 등록되지 않은 명령은 미지원 메시지로 응답합니다.
4. 알림에 `RemoteInput` 텍스트 답장 액션이 있을 때 카카오톡 답장을 **요청**합니다. 실제 배달 여부는 알 수 없습니다.
5. 같은 알림의 중복 메시지 실행을 **SQLite SHA-256 지문과 2분(일반 알림)/24시간(메시지 타임스탬프 확인 가능) 유효기간**으로 제한합니다.
6. **SQLite 영구 로그**: 수신, OFF 거부, 채팅방/발신자 차단, 호출어 무시, 중복, 실행, 답장 시도/요청/실패, 서비스 연결/해제를 기록합니다. 자동 로그 삭제는 하지 않습니다.
7. 관리 UI: 권한 설정 이동, 동작 상태, ON/OFF, 호출어, 허용 목록, 설정 저장, 즉시 OFF, 로컬 문법 시험, 최근 100개 로그, 전체 TXT 내보내기, 확인 후 로그/중복정보 삭제. 긴급 OFF는 입력란 값이 유효하지 않아도 즉시 적용합니다.
8. **인터넷·SMS·연락처·접근성·외부 저장소 권한 없음**. FastAPI/Windows PC 연동은 2~3단계에서 구현합니다.

## 실행 상태 및 제한

- 프로젝트 코드 생성: 완료.
- 현재 작업 환경에서 **Android SDK / Gradle / 실제 S20+가 없어 Android APK 빌드 및 실기기 테스트를 수행하지 못했습니다**. 빌드 성공·카카오톡 자동응답을 보증할 수 없습니다.
- 공식 Gradle wrapper JAR는 배포 바이너리이며 네트워크 접근 제약으로 ZIP에 동봉하지 못했습니다. Windows에서 `scripts/prepare-wrapper.ps1`을 실행하면 **공식 Gradle 배포 서버, 실패 시 Gradle 공식 GitHub 태그**에서 수신하여 SHA-256을 검증합니다. 그 후 Android Studio에서 프로젝트를 여세요.
- 1단계는 카카오톡 알림 기반 비공식 자동화입니다. 카카오톡 알림에서 메시지나 답장 액션이 제공되지 않으면 동작하지 않습니다.
- **발신자 표시 이름/채팅방 제목은 신원 인증이 아닙니다.** 1:1 개인 시험만 우선 실시하고 위험한 명령은 이 버전에 넣지 마세요.
- 누적 MessagingStyle 알림에서 가장 최신 메시지 하나만 처리합니다. 너무 빠르게 연속으로 보낸 명령은 누락될 수 있습니다.
- 동일 텍스트/발신자/알림 키/메시지 시각이 동일한 이벤트는 일반 알림 2분/구조화된 메시지 알림 24시간 동안 중복으로 취급합니다.
- 로그에는 카카오톡 메시지 내용이 포함됩니다. 앱 데이터 및 TXT 내보내기 파일을 안전하게 보관하세요.
- 그룹 알림 제목이나 발신자가 불명확하면 안전을 위해 차단하며 `EXTRACTION_SKIPPED`를 기록합니다.

## 개발 도구

- Android Studio와 Android SDK 36
- Android Gradle Plugin 8.11.1 / Gradle 8.14.3 / Kotlin Gradle Plugin 2.2.20
- JDK 17 이상(권장: Android Studio 내장 JDK)
- Android 8.0(API 26) 이상, 목표 API 35

## 파일 구성

- `app/src/main/java/kr/co/angaebot/bridge/MainActivity.kt` — 관리 UI / 설정 저장 / 로그 열람·내보내기·삭제
- `.../KakaoNotificationListener.kt` — 카카오톡 알림 수신, 필터, 명령 및 회신 워크플로
- `.../NotificationParser.kt` — 채팅방·발신자·메시지 추출
- `.../CommandParser.kt` — 호출어 및 명령 해석, 오프라인 실행
- `.../ReplyManager.kt` — RemoteInput 빠른 답장 요청
- `.../LogRepository.kt` — SQLite 로그, 중복 방지, TXT 내보내기
- `.../BotConfig.kt` — ON/OFF, 호출어, 정확한 허용 목록
- `app/src/test/` — 순수 명령 파서 단위 테스트
- `INSTALL.md` — Windows 및 S20+ 설치·실기기 시험 단계
- `docs/TEST_PLAN.md` — 자세한 검증 및 진단표

## 빌드

Windows PowerShell에서 프로젝트 루트에 진입한 뒤:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare-wrapper.ps1
.\gradlew.bat :app:testDebugUnitTest
.\gradlew.bat :app:assembleDebug
```

디버그 APK: `app\build\outputs\apk\debug\app-debug.apk`

또는 Android Studio > Open > 프로젝트 폴더 선택 > Gradle Sync > Run.

## 다음 단계

S20+에서 알림 파싱·자동응답 성공 후 Android Bridge → S20+ Termux의 Python FastAPI 서버(`127.0.0.1:8765`)를 연결할 계획입니다. v0.1에는 아직 네트워크 통신 기능이 없습니다.

## GitHub 업로드 및 개발 이력 관리

- `GIT_GUIDE.md` — Windows PowerShell에서 Git 초기화, Private 저장소 생성, 최초 push, 이후 commit/push, 브랜치/태그, 오류·보안 점검을 처음부터 설명합니다.
- `.gitignore` — Android 빌드 산출물, 로컬 설정, API 키, 실행 로그, SQLite DB, 서명 키 등 비공개 파일 제외 규칙.
- `.gitattributes` — 소스와 배치/스크립트 파일의 줄바꿈을 OS별로 관리합니다.
- 이 패키지는 **GitHub 업로드를 수행하지 않았습니다.** 사용자 PC에서 `GIT_GUIDE.md`의 절차에 따라 직접 업로드해야 합니다.

---

## v0.2.0 — Termux Python Core 통합 (2026-11-04)

**v0.1.3의 실제 카카오톡 송수신 성공을 기준으로 추가한 단계입니다.** 기존 Android 앱의 ①~④ UI, 수신·답장, 허용 방/발신자, SQLite 로그/중복 차단/내보내기/긴급 OFF 기능을 유지합니다.

- ②-A Python 연결 섹션은 기본 OFF이며, 토큰은 AndroidKeyStore AES-GCM으로 암호화합니다.
- 기존 `테스트/상태/도움말`은 항상 Android에서 처리합니다.
- 새로운 `계산/시간/서버상태`만 S20+ 내부 `127.0.0.1:8765` Python FastAPI로 전송합니다.
- Python 서버는 별도 64자리 랜덤 인증키, SQLite 중복 방지 및 로그를 사용합니다.
- 단체방/발신자 표시 이름은 강한 인증이 아니므로 위험한 명령은 구현하지 않았습니다.

**설치:** [`docs/UPGRADE.md`](docs/UPGRADE.md)  
**검증:** [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md)  
**변경 내역:** [`CHANGELOG.md`](CHANGELOG.md)

Android v0.2.0 APK는 현행 작업 환경에서 빌드하지 못했습니다. Windows의 JDK17/SDK36에서 `gradlew.bat :app:assembleDebug` 실행 후 S20+에서 실제 검증해야 합니다.


## v0.2.1 ??S20+ ?먮룞 ?쒖옉쨌?먮룞 蹂듦뎄

termux-services(runit) 湲곕컲 FastAPI ?먮룞 ?ъ떆??諛?30珥?媛꾧꺽 health watchdog, Google Play Termux ?댁옣 boot 吏?? 湲곗〈 湲곕뒫/?몄쬆??SQLite 濡쒓렇 蹂댁〈. docs/OPERATIONS.md 李멸퀬.
