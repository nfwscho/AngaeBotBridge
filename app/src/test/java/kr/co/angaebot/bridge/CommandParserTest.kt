/*
 * 앙개봇 Android Bridge v0.1 테스트: 호출어 판별, 명령 처리, 경계값 검증.
 * 본 프로그램은 알림 수신, 허용목록, RemoteInput 응답, SQLite 영구 로그, UI를 함께 제공한다.
 * 이 테스트는 단말기와 무관한 순수 Kotlin 명령 처리 부분만 검사한다.
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

    @Test fun helpText() {
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("테스트"))
    }
}
