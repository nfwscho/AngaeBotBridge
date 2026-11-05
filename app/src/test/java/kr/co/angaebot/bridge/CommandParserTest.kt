/*
 * 앙개봇 Android Bridge v0.4.2 명령 파서 회귀 테스트 — 보존 기능과 단축 명령 전체 설명
 * 1. 원래 호출어, 누락 호출어, 부분 일치 거부, 도움말, 명령 인수 분리를 모두 검증한다.
 * 2. 테스트/ping/상태/도움말, 계산/시간/서버상태, 운영 명령/주식 메모리7과 원래 도움말을 유지한다.
 * 3. 정확한 단축 '주'가 주식 도움말로 연결되며 기존 '앙개야 주식'과 같은 Python 명령을 사용하는지 검사한다.
 * 4. '주 분 삼성전자/마이크론/하이닉스/반도체'가 기존 주식 분석 명령/한글 종목명으로 변환되는지 검사한다.
 * 5. '주 분' 단독 입력은 기존 주식 도움말로 처리해 잘못된 시세 조회를 실행하지 않게 한다.
 * 6. '주 목록/메모리7/미국시총10/추가'의 기존 인수와 한국어·영문·일본 티커/별칭은 보존한다.
 * 7. '주가/주분/주식/ㅈㅅ' 등의 부분 일치와 사용자가 지정한 호출어가 충돌하지 않는지 검사한다.
 * 8. Android 알림·채팅방/발신자 허용·중복 방지·SQLite 로그·RemoteInput·기존 UI를 변경하지 않는 순수 Kotlin 단위 테스트이다.
 * 9. 가격 알림/주기 감시/AI 강제 활성화/자동 주문/자동 발송은 추가하거나 검사 중 실행하지 않는다.
 * v0.4.3: 단축 주가 메뉴를 열고 기존 긴 호출어의 도움말 및 별칭을 보존하는지 검사한다.
 * v0.4.5: 설치 버전 상태 텍스트만 0.4.4로 갱신하고 기존 단축 명령/숫자 메뉴 전체 회귀 테스트를 유지한다.
 * 통합 메뉴: 앙·주·민·요·여·종·영·상·도 정확한 단축어, 사용자 호출어 보호, 장문 명령 호환성을 검사한다.
 * v0.4.9: 영 호출 제거, 날씨·설정 한 글자 단축 메뉴와 주/앙/날/설 1~5단계 숫자 메뉴 점프를 검증한다.
 * 기존 주 분/주 목록/상/도/사용자 호출어 및 일반 문장 오인식 방지 회귀 테스트를 보존한다.
 */
package kr.co.angaebot.bridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CommandParserTest {
    @Test fun testCommand() {
        assertEquals(ParseResult.Command("테스트", ""), CommandParser.parse("앙개야 테스트", "앙개야"))
    }
    @Test fun noPrefix() {
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("테스트", "앙개야"))
    }
    @Test fun notPartialPrefix() {
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("앙개야야 테스트", "앙개야"))
    }
    @Test fun emptyCommandShowsHelp() {
        assertEquals(ParseResult.Command("메뉴", "홈"), CommandParser.parse("앙개야", "앙개야"))
    }
    @Test fun parseArgument() {
        assertEquals(ParseResult.Command("계산", "12 30"), CommandParser.parse("앙개야 계산 12 30", "앙개야"))
    }
    @Test fun operatingCommandNames() {
        for (name in listOf("상세상태", "통계", "최근오류", "가동시간")) {
            assertEquals(ParseResult.Command(name, ""), CommandParser.parse("앙개야 $name", "앙개야"))
            assertTrue(LocalCommandExecutor.execute("도움말", "").contains("앙개야 $name"))
        }
    }
    @Test fun stockMemory7() {
        assertEquals(ParseResult.Command("주식", "메모리7"), CommandParser.parse("앙개야 주식 메모리7", "앙개야"))
        assertEquals(ParseResult.Command("메모리7", ""), CommandParser.parse("앙개야 메모리7", "앙개야"))
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("앙개야 주식 메모리7"))
    }
    @Test fun displaysActualInstalledBridgeVersion() {
        assertTrue(LocalCommandExecutor.execute("상태", "").contains("v0.4.9"))
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("앙(홈)"))
    }

    @Test fun helpText() {
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("테스트"))
    }
    @Test fun exactShortcutMenus() {
        val menuShortcuts = mapOf(
            "앙" to "홈", "민" to "배드민턴", "요" to "요리",
            "여" to "여행", "종" to "종친", "날" to "날씨", "설" to "설정"
        )
        for ((shortcut, category) in menuShortcuts) {
            assertEquals(ParseResult.Command("메뉴", category), CommandParser.parse(shortcut, "앙개야"))
        }
        assertEquals(ParseResult.Command("메뉴", "홈"), CommandParser.parse("앙개야 메뉴", "앙개야"))
        assertEquals(ParseResult.Command("상태", ""), CommandParser.parse("상", "앙개야"))
        assertEquals(ParseResult.Command("도움말", ""), CommandParser.parse("도", "앙개야"))
        for (text in listOf("앙상블", "민트", "요리", "여행", "종친", "영어", "날씨", "설정", "영", "상황", "도움")) {
            assertEquals(ParseResult.NoTrigger, CommandParser.parse(text, "앙개야"))
        }
        assertEquals(ParseResult.Command("메뉴", "홈"), CommandParser.parse("앙", "앙개야"))
        // 앱에 별도 호출어를 설정한 경우 기존 호출어 우선 규칙은 유지된다.
        assertEquals(ParseResult.Command("도움말", ""), CommandParser.parse("앙", "앙"))
    }
    @Test fun menuJumpChainedNumbers() {
        assertEquals(ParseResult.Command("메뉴", "경로 주식 2"), CommandParser.parse("주 2", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 주식 2 2"), CommandParser.parse("주 2 2", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 주식 6 2"), CommandParser.parse("주   6  2", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 홈 1 2 2"), CommandParser.parse("앙 1 2 2", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 홈 1 2"), CommandParser.parse("앙개야 메뉴 1 2", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 설정 3"), CommandParser.parse("설 3", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 날씨 1"), CommandParser.parse("날 1", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 요리 2"), CommandParser.parse("요 2", "앙개야"))
        for (text in listOf("주변 2", "설정 2", "날씨 2", "민트 1", "요 레시피", "앙상블 1")) {
            assertEquals(ParseResult.NoTrigger, CommandParser.parse(text, "앙개야"))
        }
        assertEquals(ParseResult.Command("주식", "분석 삼성전자"), CommandParser.parse("주 분 삼성전자", "앙개야"))
    }
    @Test fun shortStockWakeWord() {
        assertEquals(ParseResult.Command("주식", "메뉴"), CommandParser.parse("주", "앙개야"))
        assertEquals(ParseResult.Command("주식", "메뉴"), CommandParser.parse("  주  ", "앙개야"))
        assertEquals(ParseResult.Command("주식", "메뉴"), CommandParser.parse("주\t", "앙개야"))
        assertEquals(ParseResult.Command("주식", ""), CommandParser.parse("앙개야 주식", "앙개야"))
    }
    @Test fun shortAnalysisNamesAndGroups() {
        for (target in listOf("삼성전자", "마이크론", "하이닉스", "엔비디아", "반도체", "미국시총10", "MU", "285A.T")) {
            assertEquals(ParseResult.Command("주식", "분석 $target"), CommandParser.parse("주 분 $target", "앙개야"))
        }
        assertEquals(ParseResult.Command("주식", "분석 웨스턴 디지털"), CommandParser.parse("주  분   웨스턴 디지털", "앙개야"))
        assertEquals(ParseResult.Command("주식", "분석 삼성전자"), CommandParser.parse("주\t분\t삼성전자", "앙개야"))
        assertEquals(ParseResult.Command("주식", "도움말"), CommandParser.parse("주 분", "앙개야"))
    }
    @Test fun shortOtherStockArguments() {
        for (argument in listOf("목록", "메모리7", "반도체", "미국시총10", "프리셋 미국시총10", "추가 반도체 삼성전자")) {
            assertEquals(ParseResult.Command("주식", argument), CommandParser.parse("주 $argument", "앙개야"))
        }
        assertEquals(ParseResult.Command("주식", "분석 마이크론"), CommandParser.parse("주 분석 마이크론", "앙개야"))
    }
    @Test fun shortBoundaryAndCustomWakeWord() {
        for (text in listOf("주가", "주식", "주분 삼성전자", "주변", "ㅈㅅ", "ㅈㅅ 분석 마이크론")) {
            assertEquals(ParseResult.NoTrigger, CommandParser.parse(text, "앙개야"))
        }
        assertEquals(ParseResult.Command("주식", "메모리7"), CommandParser.parse("주 메모리7", "앙개야"))
        assertEquals(ParseResult.Command("계산", "2+3"), CommandParser.parse("주 계산 2+3", "주"))
        assertEquals(ParseResult.Command("테스트", ""), CommandParser.parse("봇 테스트", "봇"))
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("주", ""))
    }
}
