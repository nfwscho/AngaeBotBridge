/*
 * 앙개봇 MediaSender 방식 채팅방 ID 후보 검증 — 전체 기능
 * 1. 카카오톡 Android 알림 tag를 미검증 channelId 후보로만 취급하며 공식 식별자로 단정하지 않는다.
 * 2. room과 sender가 동일한 개인 1:1 채팅에서만 길이 8~18자리 양의 Long 숫자 tag를 후보로 허용한다.
 * 3. 1차 진단 후 같은 방·발신자·태그를 가진 2차 요청을 5분 내 딱 한 번 허용한다.
 * 4. 승인 흔적은 프로세스 메모리에서만 유지하고 시도 즉시 폐기하여 재전송은 재진단을 요구한다.
 * 5. 로그와 응답에서 후보 ID 전체를 숨기고 자릿수/끝 4자리만 표시해 개인정보 노출을 제한한다.
 * 6. 기존 허용 방/발신자, Python, SQLite, 사진 자동전송, 잠금/로그/UI 동작을 보존한다.
 * 7. PIN 인증 잠금을 해제하거나 카카오톡 내부 DB를 조회하는 기능은 포함하지 않는다.
 */
package kr.co.angaebot.bridge

internal object MediaDirectPolicy {
    fun candidate(tag: String?, room: String, sender: String): Long? {
        if (room.isBlank() || sender.isBlank() || room != sender) return null
        if (tag == null || !tag.matches(Regex("[1-9][0-9]{7,17}"))) return null
        return tag.toLongOrNull()?.takeIf { it > 0L }
    }

    fun mask(value: Long): String {
        val number = value.toString()
        return number.length.toString() + "자리 · 끝 " + number.takeLast(4)
    }
}

internal class MediaDirectApproval(private val lifetimeMs: Long = 5L * 60L * 1000L) {
    private data class Evidence(val room: String, val sender: String, val tagValue: Long, val time: Long)
    private var evidence: Evidence? = null

    @Synchronized fun diagnose(tag: String?, room: String, sender: String, nowMs: Long): Long? {
        val id = MediaDirectPolicy.candidate(tag, room, sender)
        evidence = if (id != null) Evidence(room, sender, id, nowMs) else null
        return id
    }

    @Synchronized fun consume(tag: String?, room: String, sender: String, nowMs: Long): Long? {
        val previous = evidence
        evidence = null
        val id = MediaDirectPolicy.candidate(tag, room, sender)
        if (previous == null || id == null) return null
        return id.takeIf {
            previous.room == room && previous.sender == sender && previous.tagValue == id &&
                nowMs >= previous.time && nowMs - previous.time <= lifetimeMs
        }
    }
}
