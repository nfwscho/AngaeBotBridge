/*
 * 앙개봇 Android Bridge v0.3.0 — 전체 알림/명령/로그 기능 안내
 * 1. 기존 NotificationListenerService/카카오톡 패키지 검증/마지막 알림 선택 기능을 모두 보존한다.
 * 2. 기본 자동응답 OFF, 정확한 방·발신자 허용목록, 호출어 검증 및 거절 로그를 유지한다.
 * 3. SHA-256 이벤트 지문과 SQLite TTL 중복방지 및 모든 RECEIVE/COMMAND/REPLY 로그를 유지한다.
 * 4. 기존 테스트·상태·도움말 등 Android 로컬 명령을 그대로 처리한다.
 * 5. 계산·시간·서버상태 및 신규 AI 명령을 선택형 인증된 loopback Python에 전달한다.
 * 6. 자연어 모드가 별도로 ON인 경우에만 기존 미등록 명령을 AI 질문으로 전달한다.
 * 7. AI 기능/Python OFF 또는 장애가 발생해도 기존 명령과 RemoteInput 답장 흐름은 유지한다.
 * 8. PYTHON_REQUEST/RESULT/FAILED를 기존 SQLite 로그에 추가하고 토큰은 기록하지 않는다.
 * 9. 답장 직전 긴급 OFF 상태 재검증, RemoteInput 실패 기록, 서비스 생명주기 로그를 유지한다.
 * 10. AI 네트워크 처리에 시간 제한을 걸고 셸/파일/PC 제어 등 위험한 명령은 지원하지 않는다.
 * 11. v0.4.3은 활성 주식 메뉴가 열린 방/발신자에게서만 맨 앞 숫자 선택을 수신한다.
 * 12. 숫자 인식은 허용목록 확인 이후 실행하고, 비활성/만료/다른 방/발신자의 숫자는 기존처럼 무시한다.
 * 13. 기존 RECEIVE/COMMAND/PYTHON_REQUEST/RESULT/REPLY/오류 로그와 SHA-256 중복 방지를 유지한다.
 * 14. 메뉴 활성화는 인증된 Python menu_active 응답을 실제 RemoteInput에 요청한 이후에만 허용한다.
 * 15. 기존 주식 분석/그룹/메모리7/AI OFF/자동응답 OFF/앱 UI/토큰/권한은 변경하지 않는다.
 * 16. v0.4.4 모든 허용 명령(로컬/주식/숫자 메뉴/AI/오류)의 답장 마지막에 S20+ 배터리 수준/충전 상태를 추가한다.
 * 17. 배터리는 답장 직전에 ACTION_BATTERY_CHANGED sticky 정보를 읽고 별도 권한/네트워크/상시 감시를 추가하지 않는다.
 * 18. 기존 알림 승인·차단, 호출어, 중복 지문, COMMAND/PYTHON/REPLY 단계, RemoteInput 본문 기록을 보존한다.
 * 19. v0.4.5는 정상 인증 Core의 메모리7/사용자그룹 시세표에 menu_active가 있을 때도 번호 선택 게이트를 연다.
 * 20. 기존 주/숫자 메뉴/한글 종목 분석, 5분·방/발신자 제한, 배터리·모든 기존 로깅/RemoteInput을 유지한다.
 * 21. 알림 권한·토큰·UI/SQLite/AI OFF·명령의 기존 동작은 변경하지 않으며 가격 알림·매매 기능을 넣지 않는다.
 * 22. 도움말의 숫자 선택을 별도 세션에서 해석하며 하위 메뉴 0은 상위 도움말로 돌아간다.
 * 23. 도움말 숫자 선택도 기존 허용 방/발신자·중복검사·명령 로그·RemoteInput·배터리 처리 경로를 재사용한다.
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
    private lateinit var pythonConfig: PythonBridgeConfig
    private val menuGate = MenuSelectionGate()
    private val helpGate = HelpMenuGate()

    override fun onCreate() {
        super.onCreate()
        settings = BotConfig(this)
        logger = LogRepository(this)
        pythonConfig = PythonBridgeConfig(this)
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
                menuGate.setActive(message.room, message.sender, false)
                helpGate.close(message.room, message.sender)
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
            // 정확한 허용 방/발신자에서만 지난 5분 내 주식 메뉴의 숫자 선택을 허용한다.
            val helpSelection = helpGate.parseSelection(message.text, message.room, message.sender)
            val numericSelection = if (helpSelection == null) menuGate.parseSelection(message.text, message.room, message.sender) else null
            val rawParsed = helpSelection ?: numericSelection ?: CommandParser.parse(message.text, config.wakeWord)
            val helpChoice = if (helpSelection != null) {
                helpGate.choose(message.room, message.sender, helpSelection.argument.removePrefix("선택 ").trim())
            } else null
            val parsed = helpChoice?.first ?: rawParsed
            if (parsed !is ParseResult.Command) {
                logger.log("INFO", "IGNORE_PREFIX", "호출어 없음", message.room, message.sender)
                return
            }
            // 메뉴가 열린 상태에서 다른 명령으로 전환하면 기존 번호 선택을 즉시 무효화한다.
            if (numericSelection == null && !(parsed.name == "주식" && parsed.argument == "메뉴")) {
                menuGate.setActive(message.room, message.sender, false)
            }
            if (helpSelection == null && parsed.name !in setOf("도움말", "help")) {
                helpGate.close(message.room, message.sender)
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
            // 명시적으로 켠 자연어 모드에서만 미등록 명령을 AI 질문으로 전달한다.
            // 기존 로컬 명령 및 기존 Python 3개 명령의 우선순위는 그대로 보존한다.
            val isLocal = parsed.name in setOf("테스트", "ping", "상태", "도움말", "help")
            val explicitPython = parsed.name in PythonBridgeClient.supportedCommands
            val freeform = if (!isLocal && !explicitPython) {
                try { val p = pythonConfig.load(); p.enabled && p.freeformEnabled } catch (_: Exception) { false }
            } else false
            val forwardName = if (freeform) "질문" else parsed.name
            val forwardArgument = if (freeform) {
                (parsed.name + " " + parsed.argument).trim()
            } else parsed.argument
            var nextMenuActive = false
            val response = if (helpChoice?.second != null) helpChoice.second!! else if (explicitPython || freeform) {
                try {
                    val p = pythonConfig.load()
                    if (!p.enabled) {
                        // 기존 v0.1 로컬 명령은 한 글자도 바꾸지 않는다.
                        LocalCommandExecutor.execute(parsed.name, parsed.argument)
                    } else {
                        logger.log("INFO", "PYTHON_REQUEST", "command=${parsed.name} forwarded=$forwardName requestId=$fingerprint", message.room, message.sender)
                        when (val result = PythonBridgeClient.execute(p.token, fingerprint, forwardName, forwardArgument, message.room, message.sender)) {
                            is PythonOutcome.Success -> {
                                nextMenuActive = result.commandOk && result.menuActive
                                logger.log(if (result.commandOk) "INFO" else "WARN", "PYTHON_RESULT",
                                    "command=${parsed.name} ok=${result.commandOk} duplicate=${result.duplicate} reply=${result.reply}", message.room, message.sender)
                                result.reply
                            }
                            is PythonOutcome.Failure -> {
                                logger.log("ERROR", "PYTHON_FAILED", "command=${parsed.name} ${result.reason}", message.room, message.sender)
                                "⚠️ 앙개봇 Python 연결 실패\n${result.reason}"
                            }
                        }
                    }
                } catch (e: Exception) {
                    logger.log("ERROR", "PYTHON_FAILED", "command=${parsed.name} ${e.javaClass.simpleName}", message.room, message.sender)
                    "⚠️ Python 설정에 문제가 있습니다. 앙개봇 관리 화면에서 연결을 확인하세요."
                }
            } else LocalCommandExecutor.execute(parsed.name, parsed.argument)
            // 답장 전에 설정을 다시 읽어서 UI에서 OFF로 전환한 경우 답장하지 않는다.
            if (!settings.load().enabled) {
                logger.log("WARN", "REJECT_DISABLED", "실행 도중 자동응답 OFF", message.room, message.sender)
                return
            }
            // 실제로 전송할 답장에만 배터리 정보를 추가해 기존 Python/로컬 명령 결과를 수정하지 않는다.
            val replyWithBattery = BatteryStatusReporter.append(this, response)
            logger.log("INFO", "REPLY_ATTEMPT", replyWithBattery, message.room, message.sender)
            when (val outcome = ReplyManager.reply(this, sbn.notification, replyWithBattery)) {
                ReplyOutcome.Requested -> {
                    if (helpSelection == null && parsed.name in setOf("도움말", "help")) {
                        helpGate.open(message.room, message.sender)
                    }
                    logger.log("INFO", "REPLY_REQUESTED", "PendingIntent.send 요청 성공(실제 수신 확인 불가)", message.room, message.sender)
                    // 새 시세 요약도 다음 숫자 선택 메뉴이므로 인증 Core의 menu_active가 true일 때 열어준다.
                    // 기존 메뉴와 숫자 선택의 종료 규칙은 유지하고 외부 응답/실패는 메뉴를 열지 않는다.
                    if ((parsed.name == "주식" && parsed.argument == "메뉴") || nextMenuActive || numericSelection != null) {
                        menuGate.setActive(message.room, message.sender, nextMenuActive)
                    }
                }
                ReplyOutcome.NoAction -> {
                    if (numericSelection != null) menuGate.setActive(message.room, message.sender, false)
                    logger.log("WARN", "REPLY_UNAVAILABLE", "답장 가능한 알림 액션이 없음", message.room, message.sender)
                }
                is ReplyOutcome.Failed -> {
                    if (numericSelection != null) menuGate.setActive(message.room, message.sender, false)
                    logger.log("ERROR", "REPLY_FAILED", outcome.reason, message.room, message.sender)
                }
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
