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
// 18. 통합 콘텐츠 단축어/홈 메뉴 업데이트는 v0.4.7(versionCode 11)로 덮어쓰기 설치하며 데이터·권한·서명을 유지한다.
// 19. 날씨·운영 메뉴, 연속 번호 메뉴 점프 v0.4.8(versionCode 12), 기존 앱 ID·권한·SQLite 로그/설정·동작 보존.
// 20. 응답별 담당 소스 및 실배포 브랜치 표시 v0.4.9(versionCode 13), 기존 앱 데이터·권한·서명·UI/로그 보존.
// 21. v0.4.10(versionCode 14)은 사용자 요청 명령 정리, 설정 1 통합상태, 설정 8 간결 도움말을 추가한다.
// 22. 기존 패키지명·서명·관리화면·토큰/SQLite·알림 RemoteInput·배터리 및 앱 업그레이드 보존.
// 23. v0.4.11(versionCode 15)은 홈 8~10번과 메모/일정/부동산/금융투자 명령을 추가한다.
// 24. 기존 앱 ID·서명·허용 목록·AI 설정·알림/RemoteInput·SQLite 로그/배터리·기존 명령은 보존한다.
// 25. v0.4.12(versionCode 16)는 홈 메뉴 순서 조정, 단축 금·개 추가, 도움말 동기화만 수행한다.
// 26. 기존 단축 투·메/기존 UI·권한·설정·DB·로그·5분 세션 및 카카오톡 응답 흐름을 보존한다.
// 27. 날씨 조회/지역 설정 단축어는 Android Bridge v0.4.13(versionCode 17)로 배포하며 앱 ID·서명·설정·로그를 유지한다.
// 28. 부동산 실거래가 단축 조회 v0.4.14(versionCode 18)는 같은 앱 ID·서명·데이터·UI·로그·배터리를 보존한다.
// 29. 이미지 MIME 진단 및 안전한 테스트 사진 전송 v0.4.15(versionCode 19): 별도 권한 추가 없이 기존 앱 데이터/명령/텍스트 ReplyManager/로그를 보존한다.
// 30. 카카오톡 이미지 실제 수신은 S20+ 현장 검증에 맡기며 미지원 알림은 기존 텍스트 경로로 안내한다.
// 31. v0.4.16(versionCode 20) 접근성 공유 실험은 별도 사용자 승인/기본 OFF, 일치 방·사진 확인 실패 시 전송 차단을 추가한다.
// 32. 기존 텍스트 알림 답장·기존 이미지 MIME 진단·전체 DB/메뉴/배터리/Android UI 요소·Core API를 보존한다.
// 33. v0.4.17(versionCode 21)은 확인된 대상 방의 사진 보내기 버튼까지 자동 클릭하고 화면 차이 대기 로깅을 추가한다.
// 34. 기존 설치 데이터/알림·접근성 권한/메뉴/로그/토큰/배터리/API를 보존하며 잠긴 화면에선 전송하지 않는다.
// 35. v0.4.18(versionCode 22)은 인증 불필요 잠금/꺼진 화면의 Android 공식 화면 깨우기와 잠금 정책 테스트를 추가한다.
// 36. 인증 필요한 PIN/패턴/비밀번호는 우회하지 않으며 기존 설치 DB/.env/텍스트 알림/UI·로그/배터리를 유지한다.
// 37. v0.4.19(versionCode 23)은 S20+ 카카오톡 '1 보내기' 숫자 포함 단일 수신 버튼 인식을 보완한다.
// 38. 기존 Python Core/DB/.env/Android UI·설정/알림 응답/로그·배터리/잠금 정책은 모두 유지한다.
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
        versionCode = 23
        versionName = "0.4.19"
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
