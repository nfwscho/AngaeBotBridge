# 앙개봇 Bridge v0.1 — Windows 빌드 및 Galaxy S20+ 설치

## 0. 준비

- S25+ = 메인 카카오톡, S20+ = 별도 번호의 보조 카카오톡('앙개봇') 로그인 유지
- USB 데이터 케이블, Windows PC, Android Studio 최신 안정 버전, 인터넷 접속
- S20+에 충분한 저장 용량 확보. 알림에 개인 메시지가 노출되므로 타인과 공유하지 않는 기기 권장

## 1. 압축 풀기 / 프로젝트 위치

1. ZIP을 풀어 **`D:\AngaeBot\AngaeBotBridge`**와 같이 비교적 짧은 Windows 폴더에 둡니다(한글 이름도 가능하지만 도구 호환성에 유리).
2. ZIP 안의 `build.gradle.kts`, `settings.gradle.kts`, `app` 폴더가 같은 최상위 경로에 있어야 합니다.
3. Android Studio 설치: https://developer.android.com/studio
4. Android Studio **SDK Manager**에서 **Android API 36 SDK Platform** 설치. JDK는 Android Studio에 내장된 JDK를 사용합니다.

## 2. Gradle Wrapper 설치 및 공식 파일 검증 (v0.1.2 수정)

> 2026-11-04 수정: 기존 `services.gradle.org` 요청의 HTTP 404 문제에 대비해
> 직접 배포 서버와 Gradle 공식 GitHub v8.14.3 태그를 순차 시도합니다.
> 기존 Kotlin 앱 소스, UI, 설정 및 로그 로직은 변경하지 않았습니다.

```powershell
cd D:\stockproj\AngaeBotBridge
powershell -ExecutionPolicy Bypass -File .\scripts\prepare-wrapper.ps1
(Get-FileHash .\gradle\wrapper\gradle-wrapper.jar -Algorithm SHA256).Hash.ToLowerInvariant()
.\gradlew.bat --version
```

정상 SHA-256: `7d3a4ac4de1c32b59bc6a4eb8ecb8e612ccd0cf1ae1e99f66902da64df296172`  
공식 참조: https://gradle.org/release-checksums/

추가 안내: `GRADLE_WRAPPER_FIX.md`를 참고하세요. 기존 Git 저장소를 새로 초기화하지 마세요.

## 3. Android Studio 프로젝트 열기

1. Android Studio → **Open** → ZIP을 푼 프로젝트 루트(`settings.gradle.kts`가 있는 폴더)를 선택합니다.
2. **Trust Project** 확인 후 Gradle Sync를 수행합니다. SDK 라이선스 수락 및 의존 라이브러리 다운로드를 기다립니다.
3. `File > Settings > Build, Execution, Deployment > Build Tools > Gradle`에서 Gradle JDK가 JDK 17 이상인지 확인합니다.
4. `Build > Make Project`로 프로젝트를 빌드합니다.
5. `Build > Build Bundle(s) / APK(s) > Build APK(s)` 선택.
6. `app\build\outputs\apk\debug\app-debug.apk`가 생성되는지 확인합니다.

또는 PowerShell에서:

```powershell
.\gradlew.bat :app:testDebugUnitTest
.\gradlew.bat :app:assembleDebug
```

> 이 문서의 APK 위치는 **빌드 성공 시 생성되는 경로**입니다. ZIP 안에 APK가 동봉된 것은 아닙니다.

## 4. S20+ USB 디버깅 / 설치

1. S20+ → 설정 → 휴대전화 정보 → 소프트웨어 정보 → **빌드번호 7회** 탭해 개발자 옵션 활성화.
2. 설정 → 개발자 옵션 → **USB 디버깅** ON.
3. USB로 PC에 연결하고 S20+ 화면의 컴퓨터 신뢰/디버깅 허용 팝업 승인.
4. Android Studio 상단 기기 목록에서 S20+를 선택한 다음 Run(▶)을 클릭합니다.
5. 또는 SDK Platform Tools의 `adb`로 설치합니다.

```powershell
adb devices
adb install -r .\app\build\outputs\apk\debug\app-debug.apk
```

`adb`가 인식되지 않으면 Android Studio의 Run 버튼을 사용하거나 `platform-tools` 경로를 PATH에 추가합니다.

## 5. 카카오톡 알림 설정

1. S20+에서 보조 카카오톡 계정이 로그인되어 있는지 확인.
2. **카카오톡의 메시지 알림을 켜고, 알림 본문 표시가 허용되는지** 확인.
3. S25+에서 S20+와 1:1 채팅방을 열어 둡니다. 실기기 시험에서는 **1:1을 우선** 사용합니다.
4. S20+에서 앙개봇 Bridge를 열고 **알림 접근 권한 설정 열기** → 앙개봇 Bridge의 접근 허용.
5. Android 13 이후 일부 APK 설치 방식에서는 **제한된 설정(Restricted settings)** 안내로 알림 접근 권한을 막을 수 있습니다. 신뢰할 수 있는 본인이 직접 빌드한 APK인 경우에 한해 `설정 → 애플리케이션 → 앙개봇 Bridge → 우측 상단 ⋮ → 제한된 설정 허용` 메뉴를 확인합니다(기종/One UI 버전에 따라 다름).
6. 카카오톡 및 앙개봇 Bridge를 삼성 배터리 설정의 절전 예외/제한 없는 앱으로 설정(One UI 버전에 따라 메뉴명 상이).

## 6. 허용 채팅방·발신자 최초 등록

1. **자동응답 OFF** 상태에서 S25+의 카카오톡으로 S20+에 `앙개야 테스트`라고 보냅니다.
2. S20+ 앙개봇 Bridge의 **최근 처리 로그**에서 `RECEIVE` 이벤트를 확인합니다.
3. 로그에 표시되는 `room=...` 값을 **허용 채팅방 이름**에 그대로 입력합니다.
4. 로그의 `sender=...` 값을 **허용 발신자 표시 이름**에 그대로 입력합니다.
5. 정확한 값은 알림 형태에 따라 달라지므로 임의로 추측하지 마세요.
6. `자동응답 활성화`를 켠 다음 **설정 저장 / ON·OFF 적용**을 누릅니다.
7. S25+에서 다시 `앙개야 테스트`를 보냅니다. S20+의 `REPLY_REQUESTED` / `REPLY_UNAVAILABLE` 로그를 확인하고, S25+에 실제 회신이 왔는지 직접 확인합니다.

> 알림 리스너가 연결되지 않았거나 `EXTRACTION_SKIPPED`만 나올 경우, 카카오톡 알림의 메시지 본문 및 표시 방식부터 확인하세요. 필요한 경우 개인정보를 가리고 로그를 공유하여 분석할 수 있습니다.

## 7. 동작 확인 명령

```text
앙개야 테스트
앙개야 상태
앙개야 도움말
```

입력 내용이 정확한 호출어로 시작하지 않으면 무시합니다. `앙개야야 테스트`도 실행되지 않습니다.

## 8. 실패 상황별 진단

| 로그 | 해석 / 조치 |
| --- | --- |
| `LISTENER_CONNECTED` | 알림 서비스 정상 연결 |
| `RECEIVE` | 카카오톡 알림 본문/방/발신자 추출 성공 |
| `REJECT_DISABLED` | 설정 저장 후 ON인지 확인 |
| `REJECT_ROOM` | `room` 필드를 허용 목록에 정확히 등록 |
| `REJECT_SENDER` | `sender` 필드를 허용 목록에 정확히 등록 |
| `IGNORE_PREFIX` | 호출어 뒤에 공백과 명령어 입력 |
| `DUPLICATE` | 같은 알림 반복; 일반 2분 / 구조화된 메시지는 24시간 차단 |
| `EXTRACTION_SKIPPED` | 알림 형식/본문 숨김 때문에 추출 실패 |
| `REPLY_UNAVAILABLE` | 카카오톡 알림에 빠른 답장 액션이 없음 |
| `REPLY_REQUESTED` | 시스템에 전송 요청 성공. S25+에서 실제 수신 별도 확인 |
| `REPLY_FAILED` | 답장 액션 만료, 권한/기타 예외 |

## 9. 로그 백업과 안전성

- 로그는 S20+의 **앱 전용 SQLite**에 보관하며 자동으로 삭제하지 않습니다.
- 관리 화면의 **로그 전체 TXT 내보내기**를 누르면 원하는 저장 위치로 모든 로그를 기록합니다.
- 개인 채팅 내용이 포함될 수 있으므로 TXT 파일의 공유에 주의하세요.
- 앱의 데이터 지우기/삭제 또는 S20+ 초기화 시 SQLite 로그가 사라질 수 있습니다. 미리 내보내세요.
- `긴급 OFF`는 현재 앱의 자동응답을 비활성화할 뿐, 알림 리스너 권한을 삭제하지 않습니다.
- 표시 이름 허용 목록은 강한 본인 인증 수단이 아닙니다. 금융 거래·파일 삭제·시스템 변경 명령은 아직 구현하지 않았습니다.

## 10. 디버깅 시 유용한 명령

```powershell
adb logcat -s AngaeBotBridge:E
adb shell dumpsys notification
```

본인의 대화방 개인정보를 포함할 수 있으므로 로그를 외부에 올리기 전 검토해야 합니다.
