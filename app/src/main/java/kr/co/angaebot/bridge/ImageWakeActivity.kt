/*
 * 앙개봇 이미지 자동 전송용 인증 불필요 잠금 깨우기 Activity — 전체 기능
 * 1. 사용자 승인된 이미지 공유 작업에서만 내부 앱 서비스가 호출한다(외부 공개 안 함).
 * 2. 공식 Android setTurnScreenOn/setShowWhenLocked와 requestDismissKeyguard만 사용한다.
 * 3. PIN/패턴/비밀번호 등 인증이 필요한 사용자 잠금은 절대 자동 해제하지 않는다.
 * 4. 일회용 작업 토큰을 사용해 다른 이미지 작업에 영향을 주지 않는다.
 * 5. 작업 결과만 접근성 서비스에 되돌리고 즉시 종료한다. 계정/인증 정보는 기록하지 않는다.
 * 6. 기존 텍스트 알림·이미지 전송·Python Core·Android UI·DB·로그/배터리는 모두 보존한다.
 */
package kr.co.angaebot.bridge

import android.app.Activity
import android.app.KeyguardManager
import android.content.Context
import android.os.Bundle
import android.os.Handler
import android.os.Looper

class ImageWakeActivity : Activity() {
    private var token: String = ""
    private var started = false
    private var reported = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setShowWhenLocked(true)
        setTurnScreenOn(true)
        token = intent?.getStringExtra(EXTRA_TOKEN).orEmpty()
        if (token.length < 16) finish()
    }

    override fun onResume() {
        super.onResume()
        if (started || token.length < 16) return
        started = true
        Handler(Looper.getMainLooper()).postDelayed({
            if (reported || isFinishing) return@postDelayed
            val guard = getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager
            if (guard.isDeviceLocked) {
                report(false, "사용자 인증이 필요한 보안 잠금")
            } else if (!guard.isKeyguardLocked) {
                report(true, "인증 불필요 · 잠금 화면 없음")
            } else {
                try {
                    guard.requestDismissKeyguard(this, object : KeyguardManager.KeyguardDismissCallback() {
                        override fun onDismissSucceeded() { report(true, "Android 잠금 해제 요청 완료") }
                        override fun onDismissCancelled() { report(false, "Android 잠금 해제 요청 취소") }
                        override fun onDismissError() { report(false, "Android 잠금 해제 API 거부") }
                    })
                } catch (e: Exception) {
                    report(false, "잠금 해제 API 오류: ${e.javaClass.simpleName}")
                }
            }
        }, 150L)
    }

    private fun report(success: Boolean, reason: String) {
        if (reported) return
        reported = true
        KakaoImageAccessibilityService.wakeResult(token, success, reason)
        finish()
    }

    override fun onDestroy() {
        if (!reported && token.length >= 16) {
            reported = true
            KakaoImageAccessibilityService.wakeResult(token, false, "화면 깨우기 Activity 중단")
        }
        super.onDestroy()
    }

    companion object {
        const val EXTRA_TOKEN = "angaebot_image_wake_token"
    }
}
