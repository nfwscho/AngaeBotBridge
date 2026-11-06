/*
 * 앙개봇 이미지 전송 잠금 정책 회귀 테스트 — 검증 기능
 * 1. 화면이 켜져 있고 잠금이 없으면 기존 공유 경로를 선택한다.
 * 2. 인증 없는 잠금 화면과 꺼진 화면은 표준 잠금 해제 시도로 분기한다.
 * 3. 인증이 필요한 PIN·패턴·비밀번호 잠금은 항상 자동 해제를 거부한다.
 * 4. 실제 사용자 단말·카카오톡·Python·DB·로그/관리 UI에는 접근하지 않는다.
 */
package kr.co.angaebot.bridge

import org.junit.Assert.assertEquals
import org.junit.Test

class ImageLockPolicyTest {
    @Test fun readyWhenNoLock() {
        assertEquals(ImageLockAction.READY, ImageLockPolicy.evaluate(false, false, true))
    }
    @Test fun wakeWhenNoCredentialIsRequired() {
        assertEquals(ImageLockAction.WAKE, ImageLockPolicy.evaluate(true, false, true))
        assertEquals(ImageLockAction.WAKE, ImageLockPolicy.evaluate(false, false, false))
        assertEquals(ImageLockAction.WAKE, ImageLockPolicy.evaluate(true, false, false))
    }
    @Test fun neverBypassAuthentication() {
        for (keyguard in listOf(false, true)) {
            for (interactive in listOf(false, true)) {
                assertEquals(ImageLockAction.AUTH_REQUIRED, ImageLockPolicy.evaluate(keyguard, true, interactive))
            }
        }
    }
}
