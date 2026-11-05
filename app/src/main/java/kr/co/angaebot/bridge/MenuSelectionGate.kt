/*
 * 앙개봇 Android Bridge v0.4.3 숫자 메뉴 선택 게이트 — 전체 기능·보존 사항
 * 1. 오직 기존 카카오톡 방/발신자 허용 검사가 통과한 다음에 호출되는 순수 Kotlin 보조 모듈이다.
 * 2. '주' 또는 정상적인 인증 Core 주식 메뉴 응답 이후에만 숫자 1~9를 선택 명령으로 변환한다.
 * 12. v0.4.5는 메모리7 8종목/관심그룹 최대 10종목 시세표 선택을 위해 숫자 10도 허용한다.
 * 13. '10개'/'123'/'1만원' 같은 일상 문장은 차단하고 기존 5분·채팅방/발신자 격리·토큰/로그를 보존한다.
 * 3. '1', '1번', '1.', '1)', '1 선택'처럼 숫자로 시작하는 간단한 선택 문법을 지원한다.
 * 4. '1만원', '10개', '123', '주변' 등 일반 채팅/잘못된 숫자는 단축 명령으로 해석하지 않는다.
 * 5. 각 메뉴는 같은 room/sender 쌍에서만 유효하며 다른 사용자나 채팅방에 전파하지 않는다.
 * 6. 메뉴가 열린 뒤 300초를 초과하면 만료시켜 숫자 한 글자의 오인식을 방지한다.
 * 7. Python Core가 menu_active=true를 응답하고 RemoteInput 전송이 요청된 후에만 메뉴를 연다.
 * 8. 메뉴 선택 후 Python Core가 다음 메뉴가 없다고 응답하면 즉시 닫는다.
 * 9. 기존 모든 명령·SHA256 중복·SQLite/Android 로그·메모리7·주식 분석/AI OFF/설정·UI를 유지한다.
 * 10. 시계 주입을 지원해 시간 만료/채팅방·발신자 격리/문법 테스트를 Android 기기 없이 수행한다.
 * 11. 등록·삭제·AI·가격 알림·원격 명령 같은 부작용 선택을 이 모듈 자체에서 수행하지 않는다.
 * 14. 활성 메뉴에서 숫자 0도 기존 선택 API로 전달해 Python Core의 이전 메뉴 이동을 지원한다.
 * 15. 별도 HelpMenuGate는 도움말 1~10번·하위 메뉴·0 이전 메뉴를 5분 동안 방/발신자별로 처리한다.
 * 16. 주식 게이트와 도움말 게이트의 세션을 분리하고 기존 로그/권한/명령 흐름을 보존한다.
 */
package kr.co.angaebot.bridge

class MenuSelectionGate(
    private val clockMs: () -> Long = { System.nanoTime() / 1_000_000L },
) {
    companion object {
        const val MENU_TTL_MS = 300_000L
        private val SELECTION = Regex("^(10|[0-9])(?:번|[.)])?(?:\\s+.*)?$")
    }
    private data class Scope(val room: String, val sender: String)
    private val expiresAt = mutableMapOf<Scope, Long>()

    fun setActive(room: String, sender: String, active: Boolean) {
        if (room.isBlank() || sender.isBlank()) return
        val scope = Scope(room, sender)
        if (active) {
            val now = clockMs()
            expiresAt.entries.removeAll { it.value <= now }
            if (expiresAt.size >= 200 && scope !in expiresAt) {
                val oldest = expiresAt.minByOrNull { it.value }?.key
                if (oldest != null) expiresAt.remove(oldest)
            }
            expiresAt[scope] = now + MENU_TTL_MS
        } else {
            expiresAt.remove(scope)
        }
    }

    fun parseSelection(text: String, room: String, sender: String): ParseResult.Command? {
        val scope = Scope(room, sender)
        val expires = expiresAt[scope] ?: return null
        if (expires <= clockMs()) {
            expiresAt.remove(scope)
            return null
        }
        val number = SELECTION.matchEntire(text.trim())?.groupValues?.get(1) ?: return null
        return ParseResult.Command("주식", "선택 $number")
    }
}

/** 기존 주식 숫자 메뉴와 독립적인 도움말 전용 선택 세션. */
class HelpMenuGate(private val clockMs: () -> Long = { System.nanoTime() / 1_000_000L }) {
    private data class Scope(val room: String, val sender: String)
    private data class State(val section: String, val expiresAt: Long)
    private val states = mutableMapOf<Scope, State>()
    private val selection = Regex("^(10|[0-9])(?:번|[.)])?(?:\\\\s+선택)?$")
    @Synchronized fun open(room: String, sender: String, section: String = "") {
        if (room.isBlank() || sender.isBlank()) return
        val now = clockMs()
        states.entries.removeAll { it.value.expiresAt <= now }
        if (states.size >= 200 && Scope(room, sender) !in states) {
            val oldest = states.minByOrNull { it.value.expiresAt }?.key
            if (oldest != null) states.remove(oldest)
        }
        states[Scope(room, sender)] = State(section, now + 300_000L)
    }
    @Synchronized fun close(room: String, sender: String) { states.remove(Scope(room, sender)) }
    @Synchronized fun parseSelection(text: String, room: String, sender: String): ParseResult.Command? {
        val key = Scope(room, sender)
        val state = states[key] ?: return null
        if (state.expiresAt <= clockMs()) { states.remove(key); return null }
        val number = selection.matchEntire(text.trim())?.groupValues?.get(1) ?: return null
        return ParseResult.Command("도움말", "선택 $number")
    }
    /** 첫 번째 값은 실행할 기존 명령, 두 번째 값은 표시할 도움말/안내. */
    @Synchronized fun choose(room: String, sender: String, number: String): Pair<ParseResult.Command?, String?> {
        val key = Scope(room, sender)
        val state = states[key] ?: return null to "⚠️ 도움말 메뉴가 만료됐습니다. 앙개야 도움말을 입력하세요."
        if (state.expiresAt <= clockMs()) {
            states.remove(key)
            return null to "⚠️ 도움말 메뉴가 만료됐습니다. 앙개야 도움말을 입력하세요."
        }
        if (number == "0") {
            if (state.section.isEmpty()) {
                states.remove(key)
                return null to "↩️ 도움말 메뉴를 닫았습니다. 다시 열려면 앙개야 도움말을 입력하세요."
            }
            open(room, sender)
            return null to HelpNumericMenu.rootText()
        }
        val entries = HelpNumericMenu.entries(state.section)
        val index = number.toIntOrNull()?.minus(1) ?: -1
        if (index !in entries.indices) return null to "⚠️ 1~${entries.size}번 중 선택하세요. 0: 이전 메뉴"
        val entry = entries[index]
        if (entry.section.isNotEmpty()) {
            open(room, sender, entry.section)
            return null to HelpNumericMenu.render(entry.section)
        }
        states.remove(key)
        return ParseResult.Command(entry.command, entry.argument) to null
    }
}
