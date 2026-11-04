/*
 * 앙개봇 Android Bridge v0.4.4 배터리 응답 회귀 테스트 — 전체 기능/호환성
 * 1. 0%/100%/반올림 등 잔량 산식을 확인한다.
 * 2. 충전 중/충전 완료/방전 중/충전 안 함/상태 미확인을 확인한다.
 * 3. 20% 이하일 때 충전 중이 아니면 충전 권고를 표시하되 정상 구간에서는 경고하지 않는다.
 * 4. 잘못된 배터리 값이 오면 숫자를 날조하지 않고 '확인 불가'를 출력한다.
 * 5. 원래 주식 분석/메뉴/오류 답장 본문을 그대로 보존하고 맨 아래에 배터리 상태를 추가한다.
 * 6. 기존 Kotlin 단축어/번호 선택/권한·로그·UI 기능은 그대로 유지한다.
 */
package kr.co.angaebot.bridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class BatteryStatusFormatterTest {
    @Test fun chargingState() {
        assertEquals("🔋 S20+ 배터리 68% · 충전 중", BatteryStatusFormatter.footer(68, 100, BatteryChargeState.CHARGING))
        assertEquals("🔋 S20+ 배터리 100% · 충전 완료", BatteryStatusFormatter.footer(100, 100, BatteryChargeState.FULL))
    }
    @Test fun lowBatteryWarning() {
        assertTrue(BatteryStatusFormatter.footer(20, 100, BatteryChargeState.DISCHARGING).contains("⚠️ 충전 권장"))
        assertTrue(BatteryStatusFormatter.footer(0, 100, BatteryChargeState.NOT_CHARGING).contains("⚠️ 충전 권장"))
        assertFalse(BatteryStatusFormatter.footer(21, 100, BatteryChargeState.DISCHARGING).contains("⚠️"))
        assertFalse(BatteryStatusFormatter.footer(10, 100, BatteryChargeState.CHARGING).contains("⚠️"))
    }
    @Test fun invalidLevelNotInvented() {
        for ((level, scale) in listOf(-1 to 100, 10 to 0, 101 to 100)) {
            assertEquals("🔋 S20+ 배터리 확인 불가", BatteryStatusFormatter.footer(level, scale, BatteryChargeState.UNKNOWN))
        }
    }
    @Test fun percentRoundedCorrectly() {
        assertEquals("🔋 S20+ 배터리 67% · 방전 중", BatteryStatusFormatter.footer(2, 3, BatteryChargeState.DISCHARGING))
        assertEquals("🔋 S20+ 배터리 50% · 충전 안 함", BatteryStatusFormatter.footer(1, 2, BatteryChargeState.NOT_CHARGING))
    }
    @Test fun replyBodyPreserved() {
        val original = "📈 삼성전자 (005930.KS)\n5거래일 누적 -9.59%"
        assertEquals(original + "\n🔋 S20+ 배터리 70% · 방전 중", BatteryStatusFormatter.append(original, 70, 100, BatteryChargeState.DISCHARGING))
        assertEquals("⚠️ 조회 실패\n🔋 S20+ 배터리 확인 불가", BatteryStatusFormatter.append("⚠️ 조회 실패", -1, -1, BatteryChargeState.UNKNOWN))
    }
    @Test fun unknownBatteryState() {
        assertEquals("🔋 S20+ 배터리 45% · 충전 상태 미확인", BatteryStatusFormatter.footer(45, 100, BatteryChargeState.UNKNOWN))
    }
}
