// 앙개봇 Android Bridge v0.4.0 전체 빌드 기능 상세 설명
// 1. 기존 applicationId, 패키지, targetSdk/compileSdk/minSdk, JDK17/Kotlin 빌드 옵션을 보존한다.
// 2. 기존 KakaoTalk NotificationListenerService, RemoteInput, SQLite/UI 기능을 포함한다.
// 3. 기존 Termux Python FastAPI loopback 연결과 추가 AI 명령을 지원한다.
// 4. AndroidKeyStore 기반 Python 인증키 암호화 및 자연어 모드 선택 설정을 지원한다.
// 5. 기존 unit test 설정과 release buildType, Gradle 플러그인을 유지한다.
// 6. versionCode 5, versionName 0.4.1로 기존 앱 삭제 없는 APK 업그레이드를 가능하게 한다.
// 7. 무료 주식 시세 메모리7을 지원하며 기존 Gradle/Android SDK/로그/UI 옵션은 유지한다.
// 7. v0.4.0에서 새 운영 관리 명령을 지원하며 Android UI·로그·기존 권한은 유지한다.
// 8. Android Bridge v0.4.2는 '주'/'주 분' 명령을 추가하되 기존 모든 UI/로그/권한/인증·주식·AI 기능을 보존한다.
// 9. 기존 동일 applicationId로 APK 덮어쓰기 업데이트가 가능하도록 versionCode를 5에서 6으로 늘린다.
// 10. 주식 자동매매, 가격 알림, 추가 권한·유료 API는 넣지 않는다.
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
        versionCode = 6
        versionName = "0.4.2"
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
