/*
 * 앙개봇 Android Bridge v0.4.4 S20+ 배터리 상태 수집 — 전체 기능 및 호환성
 * 1. 카카오톡 답장 직전 ACTION_BATTERY_CHANGED 최신 sticky Intent를 조회한다.
 * 2. BatteryManager level/scale/status 값을 Android 시스템에서 읽어 BatteryStatusFormatter로 전달한다.
 * 3. 충전 중·충전 완료·방전 중·충전하지 않음·알 수 없음의 실제 시스템 상태를 구분한다.
 * 4. 배터리 정보가 없거나 시스템 조회에 실패해도 기존 답장을 막지 않고 '확인 불가'를 덧붙인다.
 * 5. 브로드캐스트 리시버 객체를 등록하거나 상주시키지 않으며 새 Android 권한이 필요 없다.
 * 6. 기존 NotificationListenerService 허용 방/발신자, 중복 방지, 메뉴, 로깅, RemoteInput을 그대로 유지한다.
 * 7. Android UI·설정·토큰·Python Core·SQLite 및 알림 정책에 대한 변경은 수행하지 않는다.
 * 8. 기존 ACTION_BATTERY_CHANGED 수집·예외 처리는 유지하고 실제 응답에만 한 줄 🔋 잔량 또는 ⚡ 충전 아이콘을 표시한다.
 * 9. 상세 충전 상태를 판정하는 BatteryStatusFormatter.footer 원본은 API 호환과 모듈 테스트를 위해 유지한다.
 * 10. 고정 섹터 간략 시세표만 명시적으로 inlineSectorFooter=true를 받아 99 상세보기와 배터리를 같은 줄에 표시한다.
 * 11. 기존 append(context, reply) 호출 호환성 및 모든 오류·상세·일반 명령의 배터리 마지막 단독 줄은 그대로 유지한다.
 */
package kr.co.angaebot.bridge

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager

object BatteryStatusReporter {
    fun append(context: Context, reply: String, inlineSectorFooter: Boolean = false): String {
        val footer = try {
            // null 리시버로 sticky 상태만 읽음: 지속 수신/백그라운드 배터리 감시 없음.
            val battery: Intent? = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            if (battery == null) {
                BatteryStatusFormatter.compactFooter(-1, -1, BatteryChargeState.UNKNOWN)
            } else {
                val state = when (battery.getIntExtra(BatteryManager.EXTRA_STATUS, -1)) {
                    BatteryManager.BATTERY_STATUS_CHARGING -> BatteryChargeState.CHARGING
                    BatteryManager.BATTERY_STATUS_FULL -> BatteryChargeState.FULL
                    BatteryManager.BATTERY_STATUS_DISCHARGING -> BatteryChargeState.DISCHARGING
                    BatteryManager.BATTERY_STATUS_NOT_CHARGING -> BatteryChargeState.NOT_CHARGING
                    else -> BatteryChargeState.UNKNOWN
                }
                BatteryStatusFormatter.compactFooter(
                    battery.getIntExtra(BatteryManager.EXTRA_LEVEL, -1),
                    battery.getIntExtra(BatteryManager.EXTRA_SCALE, -1),
                    state
                )
            }
        } catch (_: Exception) {
            BatteryStatusFormatter.compactFooter(-1, -1, BatteryChargeState.UNKNOWN)
        }
        return if (inlineSectorFooter) {
            BatteryStatusFormatter.appendCompactSectorFooter(reply, footer)
        } else reply + "\n" + footer
    }
}
