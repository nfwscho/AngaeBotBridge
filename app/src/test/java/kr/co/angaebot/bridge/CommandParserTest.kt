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
 * v0.4.10은 테스트/ping·계산·질문 명령이 카톡에서 무시됨을 검사하고, 간결 도움말과 상태 번호를 확인한다.
 * v0.4.12은 신규 부·금·개 및 홈 10/9 경로와 구형 투·메 호환을 회귀 검증한다.
 * 신규 날씨 단축 조회/지역 설정은 정확한 명령으로만 인식하고 기존 숫자 게이트·일상문장 차단을 보존한다.
 * 부 시세/매매/전세/월세/지역 직접 조회 단축어를 검증하고 기존 부 메모·번호 점프 및 8줄 도움말을 보존한다.
 * 공통 시세표 99 상세보기 숫자 경로는 1~10번 종목 분석과 충돌하지 않고 기존 0/00 및 메뉴 인증 흐름을 유지한다.
 * AI·반도체기자재 섹터의 97/98 페이지와 99 상세, 기존 주 2 메모리7·그룹 9/10 종목 분석을 함께 검사한다.
 * 고정 섹터 1~19 번호 경로와 '앙개야 모듈' 최근 기능 모듈 상세 조회를 기존 8줄 도움말 및 호출어 보호와 함께 확인한다.
 * 변경된 주식 홈 1 반도체주·2 미국시총10·3 AI·4 반도체기자재·5 데센 순서를 실제 로컬 도움말에서 검증하고 기존 메모리7 직접 명령은 유지한다.
 * 이미지 테스트 명령이 기존 장문 호출어와 정확한 공백 경계로만 파싱되며 기존 로컬 상태 버전 v0.4.17을 검사한다.
 */
package kr.co.angaebot.bridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CommandParserTest {
    @Test fun retiredUserCommandsIgnored() {
        for (name in listOf("테스트", "ping", "계산", "질문")) {
            assertEquals(ParseResult.NoTrigger, CommandParser.parse("앙개야 $name", "앙개야"))
            assertEquals(ParseResult.NoTrigger, CommandParser.parse("앙개야 $name 내용", "앙개야"))
            assertEquals(ParseResult.NoTrigger, CommandParser.parse("봇 $name 내용", "봇"))
        }
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
        assertEquals(ParseResult.Command("시간", "12 30"), CommandParser.parse("앙개야 시간 12 30", "앙개야"))
    }
    @Test fun operatingCommandNames() {
        for (name in listOf("상세상태", "통계", "최근오류", "가동시간")) {
            assertEquals(ParseResult.Command(name, ""), CommandParser.parse("앙개야 $name", "앙개야"))
            assertTrue(LocalCommandExecutor.execute("도움말", "").contains("설 1 통합 상태"))
        }
    }
    @Test fun stockMemory7() {
        assertEquals(ParseResult.Command("주식", "메모리7"), CommandParser.parse("앙개야 주식 메모리7", "앙개야"))
        assertEquals(ParseResult.Command("메모리7", ""), CommandParser.parse("앙개야 메모리7", "앙개야"))
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("주 1 반도체주"))
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("2 미국시총10"))
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("3 AI"))
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("4 반도체기자재"))
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("5 데센"))
    }
    @Test fun displaysActualInstalledBridgeVersion() {
        assertTrue(LocalCommandExecutor.execute("상태", "").contains("v0.4.17"))
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("앙(홈)"))
    }

    @Test fun imageTestRequiresWakeWordAndExactCommandBoundary() {
        assertEquals(ParseResult.Command("이미지", "테스트"), CommandParser.parse("앙개야 이미지 테스트", "앙개야"))
        assertEquals(ParseResult.Command("이미지", "자동시험"), CommandParser.parse("앙개야 이미지 자동시험", "앙개야"))
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("이미지 테스트", "앙개야"))
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("앙개야이미지 테스트", "앙개야"))
    }

    @Test fun helpText() {
        val help = LocalCommandExecutor.execute("도움말", "")
        assertTrue(help.contains("설 8 도움말"))
        assertTrue(help.contains("설 7 전체 메뉴"))
        assertTrue(help.contains("주 분 삼성전자"))
        assertTrue(!help.contains("앙개야 계산"))
        assertTrue(!help.contains("앙개야 테스트"))
        assertTrue(!help.contains("앙개야 질문"))
        assertTrue(!help.contains("서버상태"))
        assertTrue(!help.contains("상세상태"))
        assertTrue(help.lines().size <= 8)
    }
    @Test fun personalRecordSectorsAndCommands() {
        assertEquals(ParseResult.Command("메뉴", "부동산"), CommandParser.parse("부", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "금융·투자"), CommandParser.parse("금", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "개인"), CommandParser.parse("개", "앙개야"))
        // 구형 단축어도 지우지 않는다.
        assertEquals(ParseResult.Command("메뉴", "금융·투자"), CommandParser.parse("투", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "개인"), CommandParser.parse("메", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 부동산 1"), CommandParser.parse("부 1", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 금융·투자 1"), CommandParser.parse("금 1", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 개인 2"), CommandParser.parse("개 2", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 금융·투자 1"), CommandParser.parse("투 1", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 개인 2"), CommandParser.parse("메 2", "앙개야"))
        for (name in listOf("메모", "일정", "부동산", "투자", "금융", "기록")) {
            assertEquals(ParseResult.Command(name, "목록"),
                         CommandParser.parse("앙개야 $name 목록", "앙개야"))
        }
        assertEquals(ParseResult.Command("메모", "추가 계약 | 확인"),
                     CommandParser.parse("앙개야 메모 추가 계약 | 확인", "앙개야"))
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("부동산", "앙개야"))
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("투자가", "앙개야"))
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("메모장", "앙개야"))
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("부(부동산) · 금(금융·투자) · 개(개인 메모·일정)"))
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
        assertEquals(ParseResult.Command("메뉴", "경로 주식 2 99"), CommandParser.parse("주 2 99", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 주식 3 99"), CommandParser.parse("주 3 99", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 주식 7"), CommandParser.parse("주 7", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 주식 7 98"), CommandParser.parse("주 7 98", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 주식 7 98 99"), CommandParser.parse("주 7 98 99", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 주식 7 13"), CommandParser.parse("주 7 13", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 주식 8 15"), CommandParser.parse("주 8 15", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 주식 8 19"), CommandParser.parse("주 8 19", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 홈 1 8 19"), CommandParser.parse("앙 1 8 19", "앙개야"))
        assertEquals(ParseResult.Command("모듈", ""), CommandParser.parse("앙개야 모듈", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 주식 8 98 97"), CommandParser.parse("주 8 98 97", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 홈 1 3 99"), CommandParser.parse("앙 1 3 99", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 주식 6 2"), CommandParser.parse("주   6  2", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 홈 1 2 2"), CommandParser.parse("앙 1 2 2", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 홈 1 2"), CommandParser.parse("앙개야 메뉴 1 2", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 설정 3"), CommandParser.parse("설 3", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 홈 10 7"), CommandParser.parse("앙 10 7", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 홈 9 2"), CommandParser.parse("앙 9 2", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 날씨 1"), CommandParser.parse("날 1", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 요리 2"), CommandParser.parse("요 2", "앙개야"))
        for (text in listOf("주변 2", "설정 2", "날씨 2", "민트 1", "요 레시피", "앙상블 1")) {
            assertEquals(ParseResult.NoTrigger, CommandParser.parse(text, "앙개야"))
        }
        assertEquals(ParseResult.Command("주식", "분석 삼성전자"), CommandParser.parse("주 분 삼성전자", "앙개야"))
    }
    @Test fun realEstateShortcutsAndCompatibility() {
        assertEquals(ParseResult.Command("메뉴", "부동산"), CommandParser.parse("부", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 부동산 3"), CommandParser.parse("부 3", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 부동산 4"), CommandParser.parse("부 4", "앙개야"))
        assertEquals(ParseResult.Command("실거래", "시세 강남구"), CommandParser.parse("부 시세 강남구", "앙개야"))
        assertEquals(ParseResult.Command("실거래", "매매 서울 강남구 래미안"), CommandParser.parse("부 매매 서울 강남구 래미안", "앙개야"))
        assertEquals(ParseResult.Command("실거래", "전세 마포구"), CommandParser.parse("부 전세 마포구", "앙개야"))
        assertEquals(ParseResult.Command("실거래", "월세 강남구"), CommandParser.parse("부 월세 강남구", "앙개야"))
        assertEquals(ParseResult.Command("실거래", "지역 동작구"), CommandParser.parse("부 지역 동작구", "앙개야"))
        assertEquals(ParseResult.Command("부동산", "추가 계약 | 유지"), CommandParser.parse("앙개야 부동산 추가 계약 | 유지", "앙개야"))
        assertEquals(ParseResult.Command("부동산", "시세 강남구"), CommandParser.parse("앙개야 부동산 시세 강남구", "앙개야"))
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("부 매물 추천", "앙개야"))
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("부동산시세", "앙개야"))
        assertTrue(LocalCommandExecutor.execute("도움말", "").contains("부 3~5 실거래"))
        assertTrue(LocalCommandExecutor.execute("도움말", "").lines().size <= 8)
    }

    @Test fun weatherCommands() {
        assertEquals(ParseResult.Command("메뉴", "날씨"), CommandParser.parse("날", "앙개야"))
        assertEquals(ParseResult.Command("메뉴", "경로 날씨 2"), CommandParser.parse("날 2", "앙개야"))
        assertEquals(ParseResult.Command("날씨", "오늘"), CommandParser.parse("날 오늘", "앙개야"))
        assertEquals(ParseResult.Command("날씨", "내일"), CommandParser.parse("날 내일", "앙개야"))
        assertEquals(ParseResult.Command("날씨", "주간"), CommandParser.parse("날 주간", "앙개야"))
        assertEquals(ParseResult.Command("날씨", "지역"), CommandParser.parse("날 지역", "앙개야"))
        assertEquals(ParseResult.Command("날씨", "지역 강남구"), CommandParser.parse("날 지역 강남구", "앙개야"))
        assertEquals(ParseResult.Command("날씨", "지역 부산"), CommandParser.parse("앙개야 날씨 지역 부산", "앙개야"))
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("날 미세먼지", "앙개야"))
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("날씨 좋아", "앙개야"))
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
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("주 계산 2+3", "주"))
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("봇 테스트", "봇"))
        assertEquals(ParseResult.NoTrigger, CommandParser.parse("주", ""))
    }
}
