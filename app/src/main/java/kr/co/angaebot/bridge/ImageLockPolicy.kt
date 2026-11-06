/*
 * 앙개봇 이미지 전송 잠금 화면 상태 판단 — 전체 기능
 * 1. 기존 알림 텍스트 빠른답장·이미지 공유·메뉴·Python Core·배터리/로그 동작을 유지한다.
 * 2. 인증이 필요한 보안 잠금은 자동 해제하지 않고 안전하게 거부한다.
 * 3. 인증이 필요 없는 밀어서 해제/화면 꺼짐은 Android 공식 깨우기 절차로만 진행한다.
 * 4. 이미 화면이 켜지고 잠금 해제되어 있으면 원래 사진 공유 절차를 그대로 사용한다.
 * 5. 순수 Kotlin 정책으로 사용자 인증 정보·개인 데이터에 접근하지 않는다.
 */
package kr.co.angaebot.bridge

internal enum class ImageLockAction { READY, WAKE, AUTH_REQUIRED }

internal object ImageLockPolicy {
    fun evaluate(keyguardShowing: Boolean, deviceLocked: Boolean, interactive: Boolean): ImageLockAction = when {
        deviceLocked -> ImageLockAction.AUTH_REQUIRED
        keyguardShowing || !interactive -> ImageLockAction.WAKE
        else -> ImageLockAction.READY
    }
}
