// AngaeBot Bridge v0.2: 기존 카카오톡 알림 수신/명령 필터/응답/SQLite 로그/관리 UI 보존.
// 기존 3개 명령은 로컬, 새 3개 명령만 Termux FastAPI로 loopback 인증 요청; SMS/접근성은 불필요.
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
        versionCode = 2
        versionName = "0.2.0"
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
