/*
 * 앙개봇 Android Bridge v0.3.0 — 전체 명령 파서/기존 로컬 명령 설명
 * 1. 기존 '앙개야' 호출어를 엄격히 검사하고 공백이 뒤따를 때만 명령을 파싱한다.
 * 2. 공백·명령어·인수를 기존 규칙으로 구분하며 미인식 호출어는 거부한다.
 * 3. 기존 테스트/ping/상태/도움말/help 명령과 응답 동작을 유지한다.
 * 4. 계산/시간/서버상태는 Kotlin 파서에서 실행하지 않고 기존 Python 전달 단계를 따른다.
 * 5. 질문/요약/AI상태/대화초기화의 사용법을 도움말에 추가한다.
 * 6. 자유 자연어 해석은 별도 사용자 승인 스위치로만 허용하고 이 파서 자체는 변경하지 않는다.
 * 7. 기존 Android 알림, SQLite 이벤트 로그, 카카오톡 답장, UI와 보안 정책은 변경하지 않는다.
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
        "테스트", "ping" -> "✅ 앙개봇 Bridge v0.2.0 정상 작동 중입니다.\n카카오톡 빠른 답장을 요청했습니다."
        "상태" -> "✅ 앙개봇 Bridge v0.2.0 동작 중\n처리 위치: Galaxy S20+\n모드: Android + 선택형 Python\nPython 명령: 별도 연결 설정 / PC 연동: 향후 단계"
        "도움말", "help" -> "🤖 앙개봇 v0.3.0 명령\n앙개야 테스트\n앙개야 상태\n앙개야 도움말\n[Python 연결 ON 시]\n앙개야 계산 123*456\n앙개야 시간\n앙개야 서버상태\n앙개야 질문 안녕하세요\n앙개야 요약 본문\n앙개야 AI상태\n앙개야 대화초기화\n※ AI 기능은 Termux에서 별도 설정해야 합니다.\n※ Windows PC 명령은 향후 단계에서 추가됩니다."
        else -> "지원하지 않는 명령: $name\n도움말: 앙개야 도움말"
    }
}
