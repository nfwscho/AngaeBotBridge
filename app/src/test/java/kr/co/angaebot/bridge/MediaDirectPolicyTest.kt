/*
 * 앙개봇 MediaSender 직접 공유 후보 ID 및 일회성 승인 검증 테스트 — 전체 기능
 * 1. S20+에서 확인된 알림 숫자형 태그를 channelId 후보로 제한적으로 인식한다.
 * 2. 단체방·발신자 불일치·음수·0·짧거나 긴 ID·선행0·비숫자·Long 범위 초과를 거부한다.
 * 3. 진단 미실시/다른 채팅/태그 변경/5분 초과/재사용된 승인 요청을 모두 차단한다.
 * 4. 원본 채팅 메시지나 인증정보를 다루지 않고 실제 Android 동작 없이 Kotlin JUnit으로만 검증한다.
 */
package kr.co.angaebot.bridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class MediaDirectPolicyTest {
    private val tag = "484036463708064"

    @Test fun onlySameRoomNumericTagIsCandidate() {
        assertEquals(484036463708064L, MediaDirectPolicy.candidate(tag, "조우상", "조우상"))
        assertEquals("15자리 · 끝 8064", MediaDirectPolicy.mask(484036463708064L))
        for (bad in listOf(null, "", "not-id", "0", "-123456789", "0123456789",
                            "100", "999999999999999999999", "12345678901234567890", "1foo56789")) {
            assertNull(MediaDirectPolicy.candidate(bad, "조우상", "조우상"))
        }
        assertNull(MediaDirectPolicy.candidate(tag, "단톡방", "조우상"))
        assertNull(MediaDirectPolicy.candidate(tag, "", ""))
    }

    @Test fun diagnosisIsSingleUseAndExpires() {
        val gate = MediaDirectApproval()
        assertNull(gate.consume(tag, "조우상", "조우상", 100L))
        assertEquals(484036463708064L, gate.diagnose(tag, "조우상", "조우상", 100L))
        assertEquals(484036463708064L, gate.consume(tag, "조우상", "조우상", 110L))
        assertNull(gate.consume(tag, "조우상", "조우상", 120L))
        gate.diagnose(tag, "조우상", "조우상", 100L)
        assertNull(gate.consume(tag, "조우상", "조우상", 300101L))
        gate.diagnose(tag, "조우상", "조우상", 500000L)
        assertNull(gate.consume("484036463708065", "조우상", "조우상", 500001L))
        gate.diagnose(tag, "조우상", "조우상", 500000L)
        assertNull(gate.consume(tag, "다른사람", "다른사람", 500001L))
        gate.diagnose(tag, "조우상", "조우상", 500000L)
        assertNull(gate.consume(tag, "조우상", "조우상", 499999L))
    }
}
