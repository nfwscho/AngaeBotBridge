/*
 * 앙개봇 Android Bridge v0.4.2 명령 파서 — 기존 기능 및 단축 명령 전체 상세 설명
 * 1. 기존 사용자가 설정한 '앙개야' 등의 호출어를 정확히 인식하고, 호출어 바로 뒤 명령·인수를 분리한다.
 * 2. 호출어 일부만 일치하는 텍스트는 무시하여 일반 카카오톡 대화에서 오작동하지 않는다.
 * 3. 호출어만 입력하면 기존 '도움말' 명령을 반환하고 기존 모든 장문 명령을 그대로 지원한다.
 * 4. 기존 '테스트/ping/상태/도움말/help' 로컬 응답과 안내 텍스트를 모두 유지한다.
 * 5. 계산/시간/서버상태 및 운영 명령, 주식 메모리7/그룹/분석, AI 질문/요약 등은 기존 Python Bridge 경로를 유지한다.
 * 6. 새 정확한 단축 호출 '주'를 Python '주식' 명령(인수 없음=기존 주식 도움말)에 대응한다.
 * 7. '주 분 삼성전자'를 '주식 분석 삼성전자'로 바꾸고 한글 종목·기존 티커·그룹명도 그대로 전달한다.
 * 8. '주 분'만 입력하면 지원되는 기존 '주식 도움말'을 반환해 분석 대상 입력 방법을 안내한다.
 * 9. '주 목록', '주 반도체', '주 미국시총10'처럼 다른 기존 주식 인수는 변형 없이 전달한다.
 * 10. '주식', '주변', '주분', 'ㅈㅅ'처럼 경계가 없는 문자열을 임의로 단축 호출 처리하지 않는다.
 * 11. 앱 설정의 호출어를 '주'로 변경한 사용자는 기존 호출어 방식이 우선되도록 해 동작을 보존한다.
 * 12. 알림 수신, 허용 방/발신자, 중복 검출, Android 관리 UI, SQLite 로그, 기존 답장/오류/AI OFF 처리는 변경하지 않는다.
 * 13. 단축 인식은 문자열 해석에만 적용하고 권한 우회·외부 URL·임의 코드 실행·자동 매매·가격 알림은 추가하지 않는다.
 * 18. v0.4.3 단축 '주'는 주식 메뉴를 열며 기존 '앙개야 주식' 도움말 동작은 변경하지 않는다.
 * 19. 번호 '1'~'9'의 수신 및 세션 범위 검사는 별도 MenuSelectionGate가 수행한다.
 * 20. 기존 '주 분 종목명', '주 목록', 사용자 호출어, 로그/AI/카톡 응답을 그대로 유지한다.
 * 21. v0.4.5는 배터리 표시를 별도 모듈에서 추가하므로 파싱 동작을 보존하고 로컬 상태·도움말의 버전만 갱신한다.
 * 22. v0.4.5는 최대 10종목 선택/배터리 상태를 지원하고 로컬 상태·도움말 버전만 갱신한다.
 * 23. 기존 긴 호출어/주·주 분·숫자 선택·AI OFF/명령 파싱·로그/권한·UI 동작은 모두 보존한다.
 * 24. 도움말을 1~10번 선택 가능한 상위 메뉴로 구성하고 하위 목록에서 0으로 복귀한다.
 * 25. 기존 모든 명령어·안내·AI OFF 고지·무료 시세 고지·배터리 추가 흐름을 유지한다.
 */
package kr.co.angaebot.bridge

sealed interface ParseResult {
    data object NoTrigger : ParseResult
    data class Command(val name: String, val argument: String) : ParseResult
}

object CommandParser {
    fun parse(text: String, wakeWord: String): ParseResult {
        val message = text.trim()
        val prefix = wakeWord.trim()
        if (prefix.isEmpty()) return ParseResult.NoTrigger
        // '주'는 사용자가 직접 선택한 짧은 주식 호출어. 원래 호출어 및 사용자 설정을 먼저 보호한다.
        // 정확히 '주'이거나 '주'+공백/탭/개행일 때만 사용하고, 붙여 쓴 일반 단어는 무시한다.
        if (prefix != "주" && message.isNotEmpty() && message[0] == '주' &&
            (message.length == 1 || message[1].isWhitespace())) {
            val stockArgument = message.substring(1).trim()
            if (stockArgument.isEmpty()) return ParseResult.Command("주식", "메뉴")
            val action = stockArgument.takeWhile { !it.isWhitespace() }
            if (action == "분") {
                val target = stockArgument.substring(action.length).trim()
                return ParseResult.Command("주식", if (target.isEmpty()) "도움말" else "분석 $target")
            }
            return ParseResult.Command("주식", stockArgument)
        }
        if (prefix.isEmpty() || !message.startsWith(prefix)) return ParseResult.NoTrigger
        val rest = message.substring(prefix.length)
        if (rest.isNotEmpty() && !rest.first().isWhitespace()) return ParseResult.NoTrigger
        val commandText = rest.trim()
        if (commandText.isBlank()) return ParseResult.Command("도움말", "")
        val command = commandText.substringBefore(' ').trim()
        val argument = commandText.substringAfter(' ', "").trim()
        return ParseResult.Command(command, argument)
    }
}

object LocalCommandExecutor {
    fun execute(name: String, argument: String): String = when (name) {
        "테스트", "ping" -> "✅ 앙개봇 Bridge v0.4.7 정상 작동 중입니다.\n카카오톡 빠른 답장을 요청했습니다."
        "상태" -> "✅ 앙개봇 Bridge v0.4.7 동작 중\n처리 위치: Galaxy S20+\n모드: Android + 선택형 Python\nPython 명령: 별도 연결 설정 / PC 연동: 향후 단계"
        "도움말", "help" -> HelpNumericMenu.rootText()

        else -> "지원하지 않는 명령: $name\n도움말: 앙개야 도움말"
    }
}

/**
 * 도움말의 표시 번호와 실제 기존 명령을 한 곳에서 관리한다.
 * 기존 로컬 명령/인증된 Python 명령만 재사용하며 별도 실행 권한은 없다.
 */
object HelpNumericMenu {
    data class Entry(val label: String, val command: String = "", val argument: String = "", val section: String = "")
    private val root = listOf(
        Entry("테스트", "테스트"),
        Entry("상태", "상태"),
        Entry("시간", "시간"),
        Entry("서버상태", "서버상태"),
        Entry("상세상태", "상세상태"),
        Entry("통계", "통계"),
        Entry("최근오류", "최근오류"),
        Entry("가동시간", "가동시간"),
        Entry("주식·메모리7", section = "stock"),
        Entry("계산·AI·기타 명령", section = "other"),
    )
    private val stock = listOf(
        Entry("주식 메모리7", "주식", "메모리7"),
        Entry("메모리7", "메모리7"),
        Entry("주식 메뉴", "주식", "메뉴"),
        Entry("관심종목 목록", "주식", "목록"),
        Entry("삼성전자 분석", "주식", "분석 삼성전자"),
        Entry("마이크론 분석", "주식", "분석 마이크론"),
    )
    private val other = listOf(
        Entry("계산 123*456", "계산", "123*456"),
        Entry("AI상태", "AI상태"),
        Entry("질문 안녕하세요", "질문", "안녕하세요"),
        Entry("요약 본문", "요약", "본문"),
        Entry("대화초기화", "대화초기화"),
    )
    fun entries(section: String): List<Entry> = when (section) {
        "stock" -> stock
        "other" -> other
        else -> root
    }
    fun rootText(): String = render("")
    fun render(section: String): String {
        val heading = when (section) {
            "stock" -> "📊 주식·메모리7 메뉴"
            "other" -> "🛠 계산·AI·기타 명령"
            else -> "🤖 앙개봇 v0.4.7 명령 메뉴"
        }
        return buildString {
            appendLine(heading)
            entries(section).forEachIndexed { i, entry -> appendLine("${i + 1}. ${entry.label}") }
            appendLine("0. 이전 메뉴 / 닫기")
            appendLine("※ 5분 내 숫자로 선택 · 직접 명령도 사용 가능")
            appendLine("※ 앙개야 계산 123*456 / 앙개야 질문 안녕하세요 / 앙개야 요약 본문")
            appendLine("※ 단축 주식 명령: 주(메뉴) / 주 분 삼성전자 / 주 분 마이크론 / 주 목록")
            appendLine("※ AI 기능은 Termux에서 별도 설정해야 합니다.")
            appendLine("※ 주식 시세는 비공식 무료 데이터로 지연될 수 있습니다.")
            append("※ Windows PC 명령은 향후 단계에서 추가됩니다.")
        }
    }
}
