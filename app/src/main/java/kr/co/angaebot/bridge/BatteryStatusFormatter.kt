/*
 * 앙개봇 Android Bridge v0.4.4 배터리 응답 문구 — 전체 기능 및 기존 기능 보존
 * 1. 기존 카카오톡 알림 수신, 방/발신자 허용, 자동응답 ON/OFF, 호출어, 숫자 메뉴와 분석 명령을 유지한다.
 * 2. 원래 명령의 응답 본문은 보존하고 기본 하단에는 🔋 잔량 또는 ⚡ 충전 아이콘만 한 줄에 표시한다. 상세 상태 문자열은 기존 footer로 보존한다.
 * 3. 배터리 백분율은 level/scale 비율로 계산하고 음수/잘못된 값은 추정하지 않고 '확인 불가' 처리한다.
 * 4. 충전 중/충전 완료/방전 중/충전 안 함/알 수 없음을 구분하여 한국어로 표시한다.
 * 5. 잔량이 20% 이하이며 실제 충전 중 또는 충전 완료가 아닐 때에만 충전을 권고한다.
 * 6. 정상 답장, Python 연결 실패, 로컬 명령, 번호 메뉴 모두 동일한 배터리 문구 형식을 사용한다.
 * 7. 기존 로그, SQLite DB, 사용자 그룹, 인증 토큰, AI OFF, 앱 UI, 알림·RemoteInput 흐름은 변경하지 않는다.
 * 8. 숫자, 상태, 긴 원문 등을 외부 전송하지 않으며 기존 허용 채팅방/발신자 외에는 응답하지 않는다.
 * 9. 새 앱 권한이나 별도 네트워크 호출 없이 Android 기기의 현재 배터리 정보만 활용한다.
 * 10. 순수 Kotlin 코드이므로 단위 테스트로 응답 본문 보존, 퍼센트, 경고 경계를 검증한다.
 * 11. Android 실제 답장에는 🔋 79%, 충전/완충 중에는 ⚡ 79% 한 줄만 붙여 공간을 절약한다.
 * 12. 기존 footer/append의 상세 충전 상태 문자열과 배터리 오차/20% 저전력 알림은 삭제하지 않고 명시 조회·테스트용으로 보존한다.
 * 13. 알 수 없는 잔량은 추정하지 않으며 배터리 상태 수집/RemoteInput/SQLite/운영 로그·설정·UI는 변경하지 않는다.
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

    /** 자동응답의 한 줄 기본 배터리 표시. 충전/완충 상태는 ⚡로 구분. */
    fun compactFooter(level: Int, scale: Int, state: BatteryChargeState): String {
        if (level < 0 || scale <= 0 || level > scale) return "🔋 확인 불가"
        val percent = ((level.toLong() * 100L + scale / 2L) / scale.toLong()).toInt()
        val icon = if (state == BatteryChargeState.CHARGING || state == BatteryChargeState.FULL) "⚡" else "🔋"
        val warning = if (percent <= 20 && state !in setOf(BatteryChargeState.CHARGING, BatteryChargeState.FULL)) {
            " ⚠️"
        } else ""
        return "$icon $percent%$warning"
    }

    fun compactAppend(reply: String, level: Int, scale: Int, state: BatteryChargeState): String =
        reply.trimEnd('\n') + "\n" + compactFooter(level, scale, state)

    // API 호환성: 기존 상세 표시기를 제거하거나 반환 문자열을 변경하지 않는다.
    fun append(reply: String, level: Int, scale: Int, state: BatteryChargeState): String =
        reply + "\n" + footer(level, scale, state)
}
