/*
 * 앙개봇 Android Bridge v0.4.1 회귀 테스트: 기존 호출어/명령/경계값 및 새 운영 도움말 검증.
 * 본 프로그램은 알림 수신, 허용목록, RemoteInput 응답, SQLite 영구 로그, UI를 함께 제공한다.
 * 이 테스트는 단말기와 무관한 순수 Kotlin 명령 처리 부분만 검사한다.
 * v0.4.0: 상세상태·통계·최근오류·가동시간의 파서 인식과 도움말 표시를 검증한다.
 * 기존 6개 Kotlin 테스트를 그대로 유지하고 새 검사만 추가한다.
 * v0.4.1: 주식 메모리7/메모리7 명령의 파싱 및 도움말 표시를 검증한다.
 * v0.4.2: '주'/'주 분' 단축 명령, 한글 종목·그룹명, 기존 명령과 사용자 정의 호출어 보존을 검증한다.
 * v0.4.2: 주식 데이터·SQLite/운영 로그·알림·AI OFF·기존 UI를 변경하지 않고 순수 Kotlin 파서만 테스트한다.
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


    @Test fun shortStockWakeWord() {
        assertEquals(ParseResult.Command("주식", ""), CommandParser.parse("주", "앙개야"))
        assertEquals(ParseResult.Command("주식", ""), CommandParser.parse("  주  ", "앙개야"))
        assertEquals(ParseResult.Command("주식", ""), CommandParser.parse("주\t", "앙개야"))
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
        for (value in listOf("주가", "주식", "주분 삼성전자", "주변", "ㅈㅅ", "ㅈㅅ 분석 마이크론")) {
            assertEquals(ParseResult.NoTrigger, CommandParser.parse(value, "앙개야"))
        }
        assertEquals(ParseResult.Command("주식", "메모리7"), CommandParser.parse("주 메모리7", "앙개야"))
        assertEquals(ParseResult.Command("계산", "2+3"), CommandParser.parse("주 계산 2+3", "주"))
        assertEquals(ParseResult.Command("테스트", ""), CommandParser.parse("봇 테스트", "봇"))
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("주", ""))
    }

    @Test fun helpText() {
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("테스트"))
    }
}
