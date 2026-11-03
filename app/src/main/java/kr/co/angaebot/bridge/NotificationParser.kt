/*
 * 앙개봇 Android Bridge v0.1 — 전체 기능 설명
 * 카카오톡(com.kakao.talk) 새 알림을 안전하게 해석하고, 호출어·방/발신자 허용목록·
 * SQLite 중복 방지 후 테스트 명령을 실행한다. 응답은 알림 RemoteInput으로만 시도한다.
 * 수신, 거부, 실행, 답장 요청 및 오류 로그는 관리 UI에서 열람·내보낼 수 있다.
 * 이 파일은 알림별 대화방/발신자/본문 파싱을 담당한다. 신뢰할 수 없는 그룹 알림은 차단한다.
 */
package kr.co.angaebot.bridge

import android.app.Notification
import android.os.Build
import android.service.notification.StatusBarNotification

/** 알림에서 관측한 문자열이며 카카오톡의 인증된 ID가 아니다. */
data class IncomingMessage(
    val room: String,
    val sender: String,
    val text: String,
    val messageTime: Long,
    val identification: String
)

object NotificationParser {
    /** 실패 분석을 위한 진단 필드. 앱 내부 SQLite에만 기록하며 별도 서버로 전송하지 않는다. */
    fun diagnostic(sbn: StatusBarNotification): String {
        val extras = sbn.notification.extras
        val title = extras?.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty()
        val room = extras?.getCharSequence(Notification.EXTRA_CONVERSATION_TITLE)?.toString().orEmpty()
        val body = extras?.getCharSequence(Notification.EXTRA_TEXT)?.toString().orEmpty()
        val group = if (Build.VERSION.SDK_INT >= 28) extras?.getBoolean(Notification.EXTRA_IS_GROUP_CONVERSATION, false) else null
        val count = sbn.notification.actions?.size ?: 0
        return "key=${sbn.key} title=$title conversationTitle=$room group=$group text=$body actions=$count"
    }

    fun extract(sbn: StatusBarNotification): List<IncomingMessage> {
        val notification = sbn.notification
        // 시스템이 합친 여러 대화의 요약 알림은 개별 명령으로 처리하지 않는다.
        if ((notification.flags and Notification.FLAG_GROUP_SUMMARY) != 0) return emptyList()
        val extras = notification.extras ?: return emptyList()
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString()?.trim().orEmpty()
        val conversationTitle = extras.getCharSequence(Notification.EXTRA_CONVERSATION_TITLE)?.toString()?.trim().orEmpty()
        val groupFlag = if (Build.VERSION.SDK_INT >= 28) {
            extras.getBoolean(Notification.EXTRA_IS_GROUP_CONVERSATION, false)
        } else conversationTitle.isNotBlank()
        // 카카오톡 단체 알림은 일반적으로 대화방 제목을 제공하지만, 제공하지 않으면 안전하게 거부한다.
        if (groupFlag && conversationTitle.isBlank()) return emptyList()
        val room = if (groupFlag) conversationTitle else (conversationTitle.ifBlank { title })
        if (room.isBlank()) return emptyList()

        if (Build.VERSION.SDK_INT >= 30) {
            val bundles = extras.getParcelableArray(Notification.EXTRA_MESSAGES)
            if (bundles != null && bundles.isNotEmpty()) {
                val messages = Notification.MessagingStyle.Message.getMessagesFromBundleArray(bundles)
                val parsed = messages.mapNotNull { msg ->
                    val body = msg.text?.toString()?.trim().orEmpty()
                    if (body.isBlank()) return@mapNotNull null
                    val senderLabel = if (Build.VERSION.SDK_INT >= 28) {
                        msg.senderPerson?.name ?: msg.sender
                    } else msg.sender
                    val sender = senderLabel?.toString()?.trim().orEmpty()
                        .ifBlank { if (groupFlag) "" else title }
                    if (sender.isBlank()) return@mapNotNull null
                    IncomingMessage(room, sender, body, msg.timestamp, "MESSAGING_STYLE")
                }
                if (parsed.isNotEmpty()) return parsed
                return emptyList() // 구조화된 메시지가 있는데 파싱 실패하면 불안전한 fallback 금지
            }
        }
        val body = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString()?.trim().orEmpty()
        if (body.isBlank()) return emptyList()
        // groupFlag false라도 conversationTitle이 있는 알림의 제목에 보낸 사람 정보가 불명확할 수 있다.
        val sender = title.takeIf { it.isNotBlank() } ?: return emptyList()
        return listOf(IncomingMessage(room, sender, body, notification.`when`.takeIf { it > 0 } ?: sbn.postTime, "EXTRA_TEXT_FALLBACK"))
    }
}
