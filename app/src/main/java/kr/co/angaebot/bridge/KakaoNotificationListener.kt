/*
 * 앙개봇 Android Bridge v0.1 — 모든 구현 기능
 * 1. NotificationListenerService로 카카오톡(com.kakao.talk)의 신규/삭제 알림을 감지한다.
 * 2. 단체방 식별이 모호하거나 본문/발신자가 없는 알림은 거부하고 원인을 로그로 남긴다.
 * 3. 기본 자동응답 OFF; 정확한 채팅방 이름과 발신자 이름의 명시적 허용목록을 적용한다.
 * 4. 호출어 '앙개야' 뒤의 테스트/상태/도움말만 로컬에서 실행한다.
 * 5. 갱신·재게시 알림의 명령 중복 실행을 SQLite 지문과 2분 TTL로 차단한다.
 * 6. RemoteInput이 제공될 때만 알림 빠른 답장을 요청한다(최종 배달 보장 아님).
 * 7. 수신, 거절, 중복, 실행, 답장 요청, 오류, 서비스 연결/종료를 SQLite에 기록한다.
 * 8. UI에서 허용 목록, ON/OFF, 진단, 로그 열람/내보내기/삭제를 관리한다.
 * 9. INTERNET/SMS/접근성 권한 없이 S20+ 로컬에서 작동하며, 비공식 계정 자동화를
 *    대량 전송에 사용하지 않는다. 알림 표시 이름은 공식 신원 인증 자료가 아니다.
 */
package kr.co.angaebot.bridge

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import java.security.MessageDigest
import java.util.concurrent.Executors

class KakaoNotificationListener : NotificationListenerService() {
    private val executor = Executors.newSingleThreadExecutor()
    private lateinit var settings: BotConfig
    private lateinit var logger: LogRepository

    override fun onCreate() {
        super.onCreate()
        settings = BotConfig(this)
        logger = LogRepository(this)
    }

    override fun onListenerConnected() {
        super.onListenerConnected()
        connected = true
        submit { logger.log("INFO", "LISTENER_CONNECTED", "알림 수신 서비스 연결됨") }
    }

    override fun onListenerDisconnected() {
        connected = false
        submit { logger.log("WARN", "LISTENER_DISCONNECTED", "알림 수신 서비스 연결 끊김") }
        super.onListenerDisconnected()
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        if (sbn == null || sbn.packageName != KAKAO_PACKAGE) return
        submit { processNotification(sbn) }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
        if (sbn == null || sbn.packageName != KAKAO_PACKAGE) return
        submit { logger.log("INFO", "NOTIFICATION_REMOVED", "key=${sbn.key}") }
    }

    private fun processNotification(sbn: StatusBarNotification) {
        try {
            val messages = NotificationParser.extract(sbn)
            if (messages.isEmpty()) {
                logger.log("WARN", "EXTRACTION_SKIPPED", "카카오톡 알림 식별 실패: ${NotificationParser.diagnostic(sbn)}")
                return
            }
            // 누적 알림의 과거 대화를 재실행하지 않도록 마지막 메시지 하나만 처리한다.
            val message = messages.last()
            logger.log("INFO", "RECEIVE", "type=${message.identification} text=${message.text}", message.room, message.sender)
            val config = settings.load()
            if (!config.enabled) {
                logger.log("INFO", "REJECT_DISABLED", "자동응답 OFF", message.room, message.sender)
                return
            }
            if (!config.isAllowedRoom(message.room)) {
                logger.log("WARN", "REJECT_ROOM", "채팅방 허용목록에 없음", message.room, message.sender)
                return
            }
            if (!config.isAllowedSender(message.sender)) {
                logger.log("WARN", "REJECT_SENDER", "발신자 허용목록에 없음", message.room, message.sender)
                return
            }
            val parsed = CommandParser.parse(message.text, config.wakeWord)
            if (parsed !is ParseResult.Command) {
                logger.log("INFO", "IGNORE_PREFIX", "호출어 없음", message.room, message.sender)
                return
            }
            val identity = "${sbn.key}|${message.room}|${message.sender}|${message.messageTime}|${message.text}"
            val fingerprint = MessageDigest.getInstance("SHA-256")
                .digest(identity.toByteArray(Charsets.UTF_8))
                .joinToString("") { "%02x".format(it) }
            val dedupTtl = if (message.identification == "MESSAGING_STYLE" && message.messageTime > 0L) {
                24L * 60 * 60 * 1000
            } else 120_000L
            if (!logger.claim(fingerprint, ttlMs = dedupTtl)) {
                logger.log("INFO", "DUPLICATE", "동일 이벤트 지문 재처리 차단(ttlMs=$dedupTtl)", message.room, message.sender)
                return
            }
            logger.log("INFO", "COMMAND", "command=${parsed.name} arg=${parsed.argument}", message.room, message.sender)
            val response = LocalCommandExecutor.execute(parsed.name, parsed.argument)
            // 답장 전에 설정을 다시 읽어서 UI에서 OFF로 전환한 경우 답장하지 않는다.
            if (!settings.load().enabled) {
                logger.log("WARN", "REJECT_DISABLED", "실행 도중 자동응답 OFF", message.room, message.sender)
                return
            }
            logger.log("INFO", "REPLY_ATTEMPT", response, message.room, message.sender)
            when (val outcome = ReplyManager.reply(this, sbn.notification, response)) {
                ReplyOutcome.Requested -> logger.log("INFO", "REPLY_REQUESTED", "PendingIntent.send 요청 성공(실제 수신 확인 불가)", message.room, message.sender)
                ReplyOutcome.NoAction -> logger.log("WARN", "REPLY_UNAVAILABLE", "답장 가능한 알림 액션이 없음", message.room, message.sender)
                is ReplyOutcome.Failed -> logger.log("ERROR", "REPLY_FAILED", outcome.reason, message.room, message.sender)
            }
        } catch (t: Exception) {
            Log.e("AngaeBotBridge", "notification processing error", t)
            try { logger.log("ERROR", "PROCESS_FAILED", "${t.javaClass.simpleName}: ${t.message}") } catch (_: Exception) { }
        }
    }

    private fun submit(block: () -> Unit) {
        try { executor.execute(block) } catch (e: RuntimeException) {
            Log.e("AngaeBotBridge", "task rejected", e)
        }
    }

    override fun onDestroy() {
        connected = false
        submit { logger.log("INFO", "LISTENER_DESTROY", "서비스 종료") }
        executor.shutdown()
        super.onDestroy()
    }

    companion object {
        const val KAKAO_PACKAGE = "com.kakao.talk"
        @Volatile var connected: Boolean = false
            private set
    }
}
