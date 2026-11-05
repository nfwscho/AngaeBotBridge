// 앙개봇 Android Bridge v0.4.2 — 전체 Android 빌드 기능 상세 설명
// 1. 기존 applicationId, namespace, Android SDK 버전, min/target SDK, JDK17/Kotlin 옵션을 유지한다.
// 2. 기존 KakaoTalk NotificationListenerService, 채팅방·발신자 허용목록과 RemoteInput 자동응답을 포함한다.
// 3. SHA-256 중복 방지·SQLite 영구 로그·로그 내보내기·Android 관리 UI·긴급 OFF를 유지한다.
// 4. Termux Python FastAPI 127.0.0.1:8765 연동, 기존 명령/AI OFF·AndroidKeyStore 인증키를 유지한다.
// 5. 현재가/그룹/과거 5일·1개월·3개월 주식 분석 등 기존 Python 기능을 변경하지 않는다.
// 6. '주' 및 '주 분 삼성전자' 단축 명령을 인식하는 Android 순수 Kotlin 파서를 포함한다.
// 7. 기존 장문 '앙개야' 호출어, 테스트/상태/도움말, 운영 및 계산 명령을 그대로 사용할 수 있다.
// 8. 기존 Gradle 플러그인, junit 테스트, release 옵션, 앱 식별자 및 앱 저장 데이터 호환을 보존한다.
// 9. versionCode를 5 -> 6으로, Android Bridge versionName을 0.4.1 -> 0.4.2로 올려 삭제 없는 업그레이드를 지원한다.
// 10. 주식 주문, 예약, 자동 알림, 앱 권한 확대, 추가 서버·유료 API는 새로 넣지 않는다.
// 11. v0.4.3 숫자 선택/5분 제한을 추가하며 같은 패키지명과 기존 설정/로그/서명 호환을 유지한다.
// 12. v0.4.4에서는 모든 명령의 카카오톡 응답 맨 아래에 S20+ 배터리 잔량/충전 상태를 표시한다.
// 13. 기존 권한/SQLite/설정/AI OFF/주식 분석/Python Core·로그 및 모든 UI를 유지하고 versionCode를 8로 증가한다.
// 14. v0.4.5 메모리7·관심그룹의 번호 선택/최대 10번 지원, RemoteInput 성공 시에만 메뉴 활성화한다.
// 15. 배터리 표시/주식 분석/기존 5분 메뉴/채팅방·발신자/앱 설정과 전체 로그를 보존하고 새 권한은 없다.
// 16. 기존 서명/패키지명으로 덮어쓰기 설치할 수 있도록 versionCode 9, versionName 0.4.5로 올린다.
// 17. 0 이전 메뉴 선택을 위한 v0.4.6 업데이트로 versionCode 10을 사용하며 기존 applicationId/데이터는 유지한다.
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "kr.co.angaebot.bridge"
    compileSdk = 36

    defaultConfig {
        applicationId = "kr.co.angaebot.bridge"
        minSdk = 26
        targetSdk = 35
        versionCode = 10
        versionName = "0.4.6"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
    testOptions { unitTests.isReturnDefaultValues = true }
}

dependencies {
    testImplementation("junit:junit:4.13.2")
}
