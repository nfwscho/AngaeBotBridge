// AngaeBot Bridge v0.1: 카카오톡 알림 수신/명령 필터/응답/로그/관리 UI.
// 런타임 외부 SDK와 INTERNET 권한 없이 앱 단독으로 테스트한다.
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
        versionCode = 1
        versionName = "0.1.0"
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
