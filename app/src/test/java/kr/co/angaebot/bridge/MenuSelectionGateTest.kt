/*
 * 앙개봇 v0.4.3 메뉴 세션 회귀 테스트 — 전체 검증 기능
 * 1. 정상 활성화 이전 숫자 명령 차단, 활성화 이후 '1', '1번', '2.' 등 인식 검증.
 * 2. 메뉴 닫기 및 5분 세션 만료, 동일 방의 다른 발신자·다른 방 접근 차단 검증.
 * 3. 무관한 일반 대화·10개 이상 번호·한글 숫자 등을 선택으로 오인하지 않음.
 * 4. 기존 Kotlin 파서의 '앙개야' 장문 명령, 주 분 분석, 주 목록, 상태/테스트를 그대로 유지.
 * 5. Android SQLite/앱 설정/운영 로그/외부 Python 서버/실기기 사용 없이 순수 단위 테스트.
 * 6. v0.4.5는 메모리7 및 관심종목 시세표에서 번호 10/10번/10.까지 허용하고 10개/123/1만원은 거부한다.
 * 7. 기존 숫자 메뉴 1~9, 5분 만료, 방·발신자 격리, 명령·배터리/SQLite/로그 흐름을 보존한다.
 * 8. 메뉴가 활성화된 경우에만 0/0번을 이전 메뉴 선택으로 변환하며 일반 대화 오인식은 차단한다.
 * 9. 통합 메뉴 명령을 전달하고 00으로 홈 이동을 지원한다. 기존 5분·방/발신자 격리를 보존한다.
 * 10. 99번은 활성 5분 메뉴에서만 인식하고 9·10 종목 분석/0 이전/00 홈과 별도 번호를 유지하며 99개/999/99만원을 거부한다.
 * 11. 섹터별 97 이전/98 다음 페이지 번호는 활성 메뉴에서만 허용하며 97개·98만원 등 일반 대화를 메뉴 선택으로 오인하지 않는다.
 */
package kr.co.angaebot.bridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class MenuSelectionGateTest {
    @Test fun onlyWhenMenuOpened() {
        var now = 100L
        val gate = MenuSelectionGate(clockMs = { now })
        assertNull(gate.parseSelection("1", "방", "나"))
        assertNull(gate.parseSelection("0", "방", "나"))
        gate.setActive("방", "나", true)
        for (number in listOf("1", "1번", "1.", "1)", "1 선택")) {
            assertEquals(ParseResult.Command("메뉴", "선택 1"), gate.parseSelection(number, "방", "나"))
        }
        for (number in listOf("0", "0번", "0.", "0)", "0 선택")) {
            assertEquals(ParseResult.Command("메뉴", "선택 0"), gate.parseSelection(number, "방", "나"))
        }
        for (number in listOf("10", "10번", "10.", "10)", "10 선택")) {
            assertEquals(ParseResult.Command("메뉴", "선택 10"), gate.parseSelection(number, "방", "나"))
        }
        for (number in listOf("97", "97번", "97.", "98", "98번", "98.", "99", "99번", "99.", "99)", "99 선택")) {
            val chosen = if (number.startsWith("97")) "97" else if (number.startsWith("98")) "98" else "99"
            assertEquals(ParseResult.Command("메뉴", "선택 $chosen"), gate.parseSelection(number, "방", "나"))
        }
        assertEquals(ParseResult.Command("메뉴", "선택 00"), gate.parseSelection("00", "방", "나"))
        assertNull(gate.parseSelection("0", "다른방", "나"))
        assertNull(gate.parseSelection("1", "다른방", "나"))
        assertNull(gate.parseSelection("1", "방", "다른사람"))
    }
    @Test fun closeAndExpire() {
        var now = 100L
        val gate = MenuSelectionGate(clockMs = { now })
        gate.setActive("방", "나", true)
        now += 299_999L
        assertEquals(ParseResult.Command("메뉴", "선택 2"), gate.parseSelection("2", "방", "나"))
        now += 1L
        assertNull(gate.parseSelection("2", "방", "나"))
        assertNull(gate.parseSelection("0", "방", "나"))
        gate.setActive("방", "나", true)
        gate.setActive("방", "나", false)
        assertNull(gate.parseSelection("1", "방", "나"))
    }
    @Test fun doNotConfuseEverydayMessages() {
        val gate = MenuSelectionGate(clockMs = { 0L })
        gate.setActive("방", "나", true)
        for (text in listOf("123", "10개", "11", "1만원", "1만원이야", "주", "1만원 줘", "1번가", "1/2", "0만원", "0개", "99개", "99만원", "97개", "98만원", "999", "ㅈㅅ")) {
            assertNull(gate.parseSelection(text, "방", "나"))
        }
    }
}
