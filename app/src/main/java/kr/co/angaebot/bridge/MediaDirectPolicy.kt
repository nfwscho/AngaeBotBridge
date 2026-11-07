/*
 * 앙개봇 MediaSender 방식 채팅방 ID 후보 검증 — 전체 기능
 * 1. 카카오톡 Android 알림 tag를 미검증 channelId 후보로만 취급하며 공식 식별자로 단정하지 않는다.
 * 2. room과 sender가 동일한 개인 1:1 채팅에서만 길이 8~18자리 양의 Long 숫자 tag를 후보로 허용한다.
 * 3. 1차 진단 후 같은 방·발신자·태그를 가진 2차 요청을 5분 내 딱 한 번 허용한다.
 * 4. 승인 흔적은 프로세스 메모리에서만 유지하고 시도 즉시 폐기하여 재전송은 재진단을 요구한다.
 * 5. 로그와 응답에서 후보 ID 전체를 숨기고 자릿수/끝 4자리만 표시해 개인정보 노출을 제한한다.
 * 6. 기존 허용 방/발신자, Python, SQLite, 사진 자동전송, 잠금/로그/UI 동작을 보존한다.
 * 7. PIN 인증 잠금을 해제하거나 카카오톡 내부 DB를 조회하는 기능은 포함하지 않는다.
 * 8. 공유 대상 선택창이 실제 나타났는지 관찰 전용 UI 스냅샷으로 분류하며 자동 클릭을 하지 않는다.
 * 9. 방/상대 확인이 불충분할 때는 식별 불가로 표시하고 직접 공유 성공으로 판단하지 않는다.
 * 10. A/B 비교군에는 서로 다른 고정 PNG 파일명과 명확한 영문 표식을 할당해 같은 그림의 오인 식별을 막는다.
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

/** 채팅방 선택 UI가 나타났는지 판정하는 읽기 전용 정책. 실제 수신/채팅방 ID를 인증하지 않는다. */
internal enum class MediaDirectRoute { RECIPIENT_PICKER, TARGET_SCREEN_CANDIDATE, UNVERIFIED }

internal data class MediaDirectRouteSnapshot(
    val recipientPickerHeadingVisible: Boolean,
    val clickableRoomCount: Int,
    val exactTargetNameVisible: Boolean,
    val sendButtonCount: Int
)

internal object MediaDirectRoutePolicy {
    fun classify(snapshot: MediaDirectRouteSnapshot): MediaDirectRoute = when {
        snapshot.recipientPickerHeadingVisible && snapshot.clickableRoomCount > 0 ->
            MediaDirectRoute.RECIPIENT_PICKER
        !snapshot.recipientPickerHeadingVisible &&
            snapshot.exactTargetNameVisible && snapshot.sendButtonCount == 1 ->
            MediaDirectRoute.TARGET_SCREEN_CANDIDATE
        else -> MediaDirectRoute.UNVERIFIED
    }
}

/** A/B 시험 파일명·표식은 중앙 정책으로 한정하며 외부 경로/파일명을 받지 않는다. */
internal object MediaDirectComparisonPolicy {
    fun fileName(withChannelHint: Boolean): String =
        if (withChannelHint) "angaebot-direct-a.png" else "angaebot-direct-b.png"

    fun imageLabel(withChannelHint: Boolean): String =
        if (withChannelHint) "A: DIRECT (KEY_ID)" else "B: CONTROL (NO KEY_ID)"

    fun mode(withChannelHint: Boolean): String =
        if (withChannelHint) "A_KEY_ID" else "B_NO_KEY"
}
