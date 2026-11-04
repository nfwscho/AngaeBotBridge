/*
 * 앙개봇 Android Bridge v0.4.1 회귀 테스트: 기존 호출어/명령/경계값 및 새 운영 도움말 검증.
 * 본 프로그램은 알림 수신, 허용목록, RemoteInput 응답, SQLite 영구 로그, UI를 함께 제공한다.
 * 이 테스트는 단말기와 무관한 순수 Kotlin 명령 처리 부분만 검사한다.
 * v0.4.0: 상세상태·통계·최근오류·가동시간의 파서 인식과 도움말 표시를 검증한다.
 * 기존 6개 Kotlin 테스트를 그대로 유지하고 새 검사만 추가한다.
 * v0.4.1: 주식 메모리7/메모리7 명령의 파싱 및 도움말 표시를 검증한다.
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
        assertEquals(ParseResult.Command("도움말", ""), CommandParser.parse("앙개야", "앙개야"))
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

    @Test fun helpText() {
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("테스트"))
    }
}
