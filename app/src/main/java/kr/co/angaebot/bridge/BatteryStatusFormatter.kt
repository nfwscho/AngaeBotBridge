/*
 * 앙개봇 Android Bridge v0.4.4 배터리 응답 문구 — 전체 기능 및 기존 기능 보존
 * 1. 기존 카카오톡 알림 수신, 방/발신자 허용, 자동응답 ON/OFF, 호출어, 숫자 메뉴와 분석 명령을 유지한다.
 * 2. 원래 명령의 응답 본문을 변경하지 않고 하단에 S20+ 배터리 잔량과 충전 상태만 덧붙인다.
 * 3. 배터리 백분율은 level/scale 비율로 계산하고 음수/잘못된 값은 추정하지 않고 '확인 불가' 처리한다.
 * 4. 충전 중/충전 완료/방전 중/충전 안 함/알 수 없음을 구분하여 한국어로 표시한다.
 * 5. 잔량이 20% 이하이며 실제 충전 중 또는 충전 완료가 아닐 때에만 충전을 권고한다.
 * 6. 정상 답장, Python 연결 실패, 로컬 명령, 번호 메뉴 모두 동일한 배터리 문구 형식을 사용한다.
 * 7. 기존 로그, SQLite DB, 사용자 그룹, 인증 토큰, AI OFF, 앱 UI, 알림·RemoteInput 흐름은 변경하지 않는다.
 * 8. 숫자, 상태, 긴 원문 등을 외부 전송하지 않으며 기존 허용 채팅방/발신자 외에는 응답하지 않는다.
 * 9. 새 앱 권한이나 별도 네트워크 호출 없이 Android 기기의 현재 배터리 정보만 활용한다.
 * 10. 순수 Kotlin 코드이므로 단위 테스트로 응답 본문 보존, 퍼센트, 경고 경계를 검증한다.
 */
package kr.co.angaebot.bridge

enum class BatteryChargeState { CHARGING, FULL, DISCHARGING, NOT_CHARGING, UNKNOWN }

object BatteryStatusFormatter {
    private const val UNAVAILABLE = "🔋 S20+ 배터리 확인 불가"

    fun footer(level: Int, scale: Int, state: BatteryChargeState): String {
        if (level < 0 || scale <= 0 || level > scale) return UNAVAILABLE
        val percent = ((level.toLong() * 100L + scale / 2L) / scale.toLong()).toInt()
        val status = when (state) {
            BatteryChargeState.CHARGING -> "충전 중"
            BatteryChargeState.FULL -> "충전 완료"
            BatteryChargeState.DISCHARGING -> "방전 중"
            BatteryChargeState.NOT_CHARGING -> "충전 안 함"
            BatteryChargeState.UNKNOWN -> "충전 상태 미확인"
        }
        val warning = if (percent <= 20 && state != BatteryChargeState.CHARGING && state != BatteryChargeState.FULL) {
            " · ⚠️ 충전 권장"
        } else ""
        return "🔋 S20+ 배터리 ${percent}% · $status$warning"
    }

    fun append(reply: String, level: Int, scale: Int, state: BatteryChargeState): String =
        reply + "\n" + footer(level, scale, state)
}
