/*
 * 앙개봇 Android Bridge v0.1 — 전체 기능 설명
 * 카카오톡 알림 → 정확한 호출어 검사 → 명령(테스트/상태/도움말) 실행 → 알림 답장.
 * 정확한 채팅방·발신자 허용 목록, SQLite 중복방지·처리 로그, 관리 UI가 함께 동작한다.
 * 이 파일은 Android 런타임과 무관한 순수 명령 파서이며 단위 테스트 가능하다.
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
        "테스트", "ping" -> "✅ 앙개봇 Bridge v0.1 정상 작동 중입니다.\n카카오톡 빠른 답장을 요청했습니다."
        "상태" -> "✅ 앙개봇 Bridge v0.1 동작 중\n처리 위치: Galaxy S20+\n모드: Android 단독 자동응답\nPython/PC 연결: 2단계 예정"
        "도움말", "help" -> "🤖 앙개봇 v0.1 명령\n앙개야 테스트\n앙개야 상태\n앙개야 도움말\n※ Windows/Python 명령은 다음 단계에서 추가됩니다."
        else -> "지원하지 않는 명령: $name\n도움말: 앙개야 도움말"
    }
}
