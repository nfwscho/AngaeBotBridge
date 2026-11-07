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
 * 22. 주식 전용 숫자 게이트를 통합 메뉴 게이트로 활용하며 앙/주/민/요/여/종/영을 같은 인증·로그 경로로 처리한다.
 * 23. 상/도는 기존 로컬 상태·도움말로 처리하고 일반 카톡 문장 및 비허용 방·발신자는 그대로 차단한다.
 * 24. Core menu_active 확인과 RemoteInput 전송 요청 후에만 숫자 메뉴를 열고 기존 세션 제한을 보존한다.
 * 25. v0.4.9 기존 담당 모듈 식별과 경로 기록을 유지하되 기본 카카오톡 화면에는 숨기고 '앙개야 모듈'로 직전 경로를 한 번 조회한다.
 * 26. 로컬 상 명령의 기존 본문에 인증 Core health의 실제 배포 브랜치/커밋을 덧붙인다.
 * 27. Core OFF/장애/기록 누락 시 미확인 표시, GitHub main을 배포 브랜치라고 추정하지 않는다.
 * 28. 기존 RECEIVE/COMMAND/PYTHON/REPLY 로그·SQLite·RemoteInput·인증·AI OFF·UI·배터리 유지.
 * 29. 모든 일반 답장의 두 줄 모듈/파일경로 자동 노출을 제거하되 기존 소스 식별·jobs/events·SQLite의 원본 로그는 보존한다.
 * 30. '앙개야 모듈' 명시 조회에 한해 동일한 방/발신자의 직전 성공적으로 전송 요청한 답장의 실제 모듈·경로를 출력한다.
 * 31. 모듈 조회만으로 기존 주식 5분 숫자 선택 세션을 닫지 않고 다른 방/발신자에게 이력을 공개하지 않는다.
 * 32. 짧은 🔋/⚡ 잔량만 응답 마지막 한 줄에 표시하고 ACTION_BATTERY_CHANGED 상태 판정/오류·20% 알림을 유지한다.
 * 33. 고정 섹터 13/19/5종목의 간략보기에서만 99 상세보기와 배터리 잔량을 같은 줄에 합쳐 시각 줄 다음 1줄로 완료한다.
 * 34. 종목별 1~19 분석, 99 상세, 다른 메뉴/오류/모듈 조회에는 기존 배터리 분리 표기를 유지한다.
 * 35. 개인 '반도체' 그룹과 미국시총10 등 core.watchlists/core.market의 간략 시세도 99 뒤 배터리를 한 줄로 합치고 정규장·프리/애프터 상세는 원본 유지한다.
 * 36. 메뉴·오류·일반 답장에는 같은 줄 배터리를 붙이지 않으며 해당 응답의 정확한 모듈 식별과 작업 로그를 보존한다.
 * 37. 이미지 테스트 명령을 기존 허용 방·발신자/호출어/중복검증 후 로컬에서만 처리한다.
 * 38. 카카오톡 알림에 이미지 MIME 입력이 없으면 억지로 첨부하지 않고 기존 텍스트 답장으로 불가 사유를 알려준다.
 * 39. 지원되는 경우 앱 전용 테스트 이미지만 전달하고 IMAGE_REPLY_* 로그를 추가하되 기존 RECEIVE/COMMAND/REPLY 로그를 보존한다.
 * 40. 전송 요청 성공과 실제 카카오톡 사진 수신은 구분하며 기존 메뉴·Python·AI·배터리·상태·SQLite·UI를 유지한다.
 * 41. '앙개야 이미지 자동시험'은 별도 사용자가 승인한 접근성 서비스가 연결된 경우에만 실제 카카오톡 공유 UI 자동 전송을 시험한다.
 * 42. 이전 '앙개야 이미지 테스트'와 텍스트 알림 답장·방/발신자 허용·중복방지 및 기존 로그 체계는 모두 유지한다.
 * 43. 접근성 OFF·잠금·방 확인 실패는 실패로 보고하고 실제 사진 전송 성공으로 오인하지 않는다.
 * 44. v0.4.22 MediaSender 진단/직공유시험 명령은 기존 정확한 방·발신자·호출어·중복 검증 뒤에만 처리한다.
 * 45. 알림 tag 후보는 카카오 채팅방 ID라고 확정하지 않으며 1:1에서 5분 내 일회성 진단 승인 후에만 사용한다.
 * 46. 새 실험 스위치는 기본 OFF, 일반 이미지 자동시험·텍스트/시세/메모·배터리·모든 로그는 유지한다.
 */
package kr.co.angaebot.bridge

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import android.os.SystemClock
import java.security.MessageDigest
import java.util.concurrent.Executors

class KakaoNotificationListener : NotificationListenerService() {
    private val executor = Executors.newSingleThreadExecutor()
    private lateinit var settings: BotConfig
    private lateinit var logger: LogRepository
    private lateinit var pythonConfig: PythonBridgeConfig
    private val menuGate = MenuSelectionGate()
    private val lastModules = LastModuleTracker()
    private val mediaDirectApproval = MediaDirectApproval()

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
            val numericSelection = menuGate.parseSelection(message.text, message.room, message.sender)
            val parsed = numericSelection ?: CommandParser.parse(message.text, config.wakeWord)
            if (parsed !is ParseResult.Command) {
                logger.log("INFO", "IGNORE_PREFIX", "호출어 없음", message.room, message.sender)
                return
            }
            val isModuleLookup = parsed.name == "모듈" && parsed.argument.isBlank()
            val isImageTest = parsed.name == "이미지" && parsed.argument == "테스트"
            val isImageAutoTest = parsed.name == "이미지" && parsed.argument == "자동시험"
            val isMediaDirectDiagnostic = parsed.name == "이미지" && parsed.argument == "직공유진단"
            val isMediaDirectTest = parsed.name == "이미지" && parsed.argument == "직공유시험"
            // 요청한 모듈 정보는 원래 시세 선택 상태를 방해하지 않는다.
            // 그 밖의 기존 명령은 이전과 동일하게 번호 선택을 무효화한다.
            if (numericSelection == null && !isModuleLookup &&
                !(parsed.name == "주식" && parsed.argument == "메뉴")) {
                menuGate.setActive(message.room, message.sender, false)
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
            val isLocal = parsed.name in setOf("테스트", "ping", "상태", "도움말", "help", "이미지") || isModuleLookup
            val explicitPython = parsed.name in PythonBridgeClient.supportedCommands
            val freeform = if (!isLocal && !explicitPython) {
                try { val p = pythonConfig.load(); p.enabled && p.freeformEnabled } catch (_: Exception) { false }
            } else false
            val forwardName = if (freeform) "질문" else parsed.name
            val forwardArgument = if (freeform) {
                (parsed.name + " " + parsed.argument).trim()
            } else parsed.argument
            var nextMenuActive = false
            var sourceModule = ModuleSourceFormatter.localCommandSource(parsed.name)
            val imageMime = if (isImageTest) ReplyManager.supportedImageMime(sbn.notification) else null
            val imageAutoStart = if (isImageAutoTest) KakaoImageAccessibilityService.queueTest(message.room) else null
            val directCandidate = if (isMediaDirectDiagnostic) {
                mediaDirectApproval.diagnose(sbn.tag, message.room, message.sender, SystemClock.elapsedRealtime())
            } else if (isMediaDirectTest && MediaDirectConfig.enabled(this)) {
                mediaDirectApproval.consume(sbn.tag, message.room, message.sender, SystemClock.elapsedRealtime())
            } else null
            val directStart = if (isMediaDirectTest && directCandidate != null) {
                KakaoImageAccessibilityService.queueDirectTest(message.room, directCandidate)
            } else null
            val response = if (parsed.name == "이미지") {
                sourceModule = "bridge.image"
                if (isMediaDirectDiagnostic) {
                    if (directCandidate == null) {
                        logger.log("WARN", "MEDIA_DIRECT_NO_CANDIDATE",
                            "1:1 이름 일치 또는 숫자형 알림 tag 검증 실패", message.room, message.sender)
                        "🧪 MediaSender 직공유 진단\n채팅방 ID 후보를 확보하지 못했습니다.\n※ 기존 이미지 자동시험은 정상 유지됩니다."
                    } else {
                        logger.log("INFO", "MEDIA_DIRECT_CANDIDATE",
                            "알림 tag 후보 " + MediaDirectPolicy.mask(directCandidate) + " · 실제 ID 미확인",
                            message.room, message.sender)
                        "🧪 MediaSender 직공유 진단\n숫자형 알림 tag 후보: " +
                            MediaDirectPolicy.mask(directCandidate) + "\n" +
                            "※ 실제 카카오 채팅방 ID인지 미확인\n" +
                            "※ S20+ ②-B-1 스위치를 켜고 5분 안에 앙개야 이미지 직공유시험 입력"
                    }
                } else if (isMediaDirectTest) {
                    when {
                        !MediaDirectConfig.enabled(this) -> {
                            logger.log("WARN", "MEDIA_DIRECT_REJECTED", "별도 직공유 스위치 OFF",
                                message.room, message.sender)
                            "⚠️ MediaSender 직공유 스위치 OFF\nS20+ 관리화면에서 별도로 허용하세요."
                        }
                        directCandidate == null -> {
                            logger.log("WARN", "MEDIA_DIRECT_REJECTED",
                                "1:1 동일 알림 tag 진단·5분 내 일회성 승인 없음", message.room, message.sender)
                            "⚠️ 직공유 후보 미검증\n먼저 앙개야 이미지 직공유진단을 보내세요."
                        }
                        directStart == ImageAutoStart.Queued -> {
                            logger.log("INFO", "MEDIA_DIRECT_QUEUED",
                                "단일 허용 방 직접 공유 예약 · 카카오 수신 미확인", message.room, message.sender)
                            "🧪 MediaSender 직접 공유 시험 시작\n" +
                                "파일: 테스트 PNG · 후보: " + MediaDirectPolicy.mask(directCandidate) + "\n" +
                                "※ 사진이 실제로 올바른 1:1 채팅에 도착했는지 확인하세요."
                        }
                        directStart is ImageAutoStart.Rejected -> {
                            logger.log("WARN", "MEDIA_DIRECT_REJECTED", directStart.reason,
                                message.room, message.sender)
                            "⚠️ 직접 공유 시험 거부\n" + directStart.reason +
                                "\n※ 기존 자동전송은 유지됩니다."
                        }
                        else -> "⚠️ 직공유 시험 상태를 확인하지 못했습니다."
                    }
                } else if (isImageAutoTest) {
                    when (imageAutoStart) {
                        ImageAutoStart.Queued -> {
                            logger.log("INFO", "IMAGE_UI_START_ACCEPTED", "카카오톡 사진 공유 UI 실험 예약(실제 수신 미확인)", message.room, message.sender)
                            "🖼️ 이미지 자동전송 시험 시작\nS20+의 카카오톡 화면에서 대상 방과 사진을 확인합니다.\n※ 실제 사진 말풍선이 도착했는지 확인하세요."
                        }
                        is ImageAutoStart.Rejected -> {
                            logger.log("WARN", "IMAGE_UI_START_REJECTED", imageAutoStart.reason, message.room, message.sender)
                            "⚠️ 이미지 자동전송 시험 불가\n${imageAutoStart.reason}\n※ 기존 텍스트 자동응답은 정상 유지됩니다."
                        }
                        null -> "⚠️ 이미지 자동전송 상태를 확인하지 못했습니다."
                    }
                } else if (!isImageTest) {
                    "🖼️ 이미지 진단: 앙개야 이미지 테스트 / 앙개야 이미지 자동시험\n" +
                        "MediaSender: 앙개야 이미지 직공유진단 / 앙개야 이미지 직공유시험\n" +
                        "※ 직접 공유는 별도 OFF 기본값이며 진단이 선행돼야 합니다."
                } else if (imageMime == null) {
                    logger.log("WARN", "IMAGE_REPLY_UNAVAILABLE", "카카오톡 알림에 이미지 MIME RemoteInput 액션 없음", message.room, message.sender)
                    "🖼️ 이미지 직접 전송 미지원\n현재 카카오톡 알림은 사진 첨부 입력을 제공하지 않습니다.\n※ 텍스트 자동응답은 정상 유지됩니다."
                } else {
                    logger.log("INFO", "IMAGE_REPLY_SUPPORTED", "image MIME=$imageMime", message.room, message.sender)
                    "🖼️ 이미지 전송 시험 요청 ($imageMime)\n※ 실제 카카오톡 수신 여부를 대화방에서 확인하세요."
                }
            } else if (isModuleLookup) {
                // 사용자가 명시한 경우에만 직전 화면 출처를 표시. 가격·본문은 저장하지 않음.
                ModuleSourceFormatter.onDemandDetail(lastModules.last(message.room, message.sender))
            } else if (explicitPython || freeform) {
                try {
                    val p = pythonConfig.load()
                    if (!p.enabled) {
                        // 기존 Python OFF 로컬 응답과 그 로그·오류 경로를 유지한다.
                        sourceModule = "bridge.python"
                        LocalCommandExecutor.execute(parsed.name, parsed.argument)
                    } else {
                        logger.log("INFO", "PYTHON_REQUEST", "command=${parsed.name} forwarded=$forwardName requestId=$fingerprint", message.room, message.sender)
                        when (val result = PythonBridgeClient.execute(p.token, fingerprint, forwardName, forwardArgument, message.room, message.sender)) {
                            is PythonOutcome.Success -> {
                                nextMenuActive = result.commandOk && result.menuActive
                                sourceModule = result.moduleSource.ifBlank { "core.main" }
                                logger.log(if (result.commandOk) "INFO" else "WARN", "PYTHON_RESULT",
                                    "command=${parsed.name} ok=${result.commandOk} duplicate=${result.duplicate} reply=${result.reply}", message.room, message.sender)
                                result.reply
                            }
                            is PythonOutcome.Failure -> {
                                sourceModule = "bridge.python"
                                logger.log("ERROR", "PYTHON_FAILED", "command=${parsed.name} ${result.reason}", message.room, message.sender)
                                "⚠️ 앙개봇 Python 연결 실패\n${result.reason}"
                            }
                        }
                    }
                } catch (e: Exception) {
                    sourceModule = "bridge.python"
                    logger.log("ERROR", "PYTHON_FAILED", "command=${parsed.name} ${e.javaClass.simpleName}", message.room, message.sender)
                    "⚠️ Python 설정에 문제가 있습니다. 앙개봇 관리 화면에서 연결을 확인하세요."
                }
            } else {
                val original = LocalCommandExecutor.execute(parsed.name, parsed.argument)
                if (parsed.name == "상태") {
                    // Only the explicit local status command checks authenticated Core health.
                    // Other local commands remain fully offline as before.
                    val extra = try {
                        val settings = pythonConfig.load()
                        ModuleSourceFormatter.statusDeployment(
                            if (settings.enabled) PythonBridgeClient.health(settings.token) else null,
                            settings.enabled
                        )
                    } catch (_: Exception) {
                        "📦 배포 정보: Core 확인 불가 · 브랜치 미확인"
                    }
                    original + "\n\n" + extra
                } else original
            }
            // 답장 전에 설정을 다시 읽어서 UI에서 OFF로 전환한 경우 답장하지 않는다.
            if (!settings.load().enabled) {
                logger.log("WARN", "REJECT_DISABLED", "실행 도중 자동응답 OFF", message.room, message.sender)
                return
            }
            // 실제로 전송할 답장에만 배터리 정보를 추가해 기존 Python/로컬 명령 결과를 수정하지 않는다.
            val replyWithSource = ModuleSourceFormatter.append(response, sourceModule, showDetails = false)
            // 고정 주식 섹터 간략 시세만 시각/99+배터리 두 줄로 출력한다.
            // 상세보기/오류/타 메뉴의 기존 배터리 단독 줄은 변경하지 않는다.
            val inlineSectorBattery =
                response.startsWith("📊 ") &&
                response.trimEnd().endsWith("99. 🔎 상세보기") &&
                (sourceModule == "core.sector_watchlists" ||
                 sourceModule == "core.watchlists" ||
                 sourceModule == "core.market")
            val replyWithBattery = BatteryStatusReporter.append(
                this, replyWithSource, inlineSectorFooter = inlineSectorBattery)
            logger.log("INFO", "REPLY_ATTEMPT", replyWithBattery, message.room, message.sender)
            val replyOutcome = if (isImageTest && imageMime != null) {
                ReplyManager.replyTestImage(this, sbn.notification, replyWithBattery)
            } else {
                ReplyManager.reply(this, sbn.notification, replyWithBattery)
            }
            when (val outcome = replyOutcome) {
                ReplyOutcome.Requested -> {
                    if (isImageTest && imageMime != null) {
                        logger.log("INFO", "IMAGE_REPLY_REQUESTED", "이미지 MIME=$imageMime PendingIntent 요청 성공(실제 수신 확인 불가)", message.room, message.sender)
                    }
                    logger.log("INFO", "REPLY_REQUESTED", "PendingIntent.send 요청 성공(실제 수신 확인 불가)", message.room, message.sender)
                    if (!isModuleLookup) {
                        // 알림 응답 요청에 성공한 화면의 모듈 ID만 최근 이력으로 기억한다.
                        lastModules.remember(message.room, message.sender, sourceModule)
                    }
                    // 새 시세 요약도 다음 숫자 선택 메뉴이므로 인증 Core의 menu_active가 true일 때 열어준다.
                    // 기존 메뉴와 숫자 선택의 종료 규칙은 유지하고 외부 응답/실패는 메뉴를 열지 않는다.
                    if ((parsed.name == "주식" && parsed.argument == "메뉴") || parsed.name == "메뉴" || nextMenuActive || numericSelection != null) {
                        menuGate.setActive(message.room, message.sender, nextMenuActive)
                    }
                }
                ReplyOutcome.NoAction -> {
                    if (numericSelection != null) menuGate.setActive(message.room, message.sender, false)
                    if (isImageTest && imageMime != null) {
                        logger.log("WARN", "IMAGE_REPLY_UNAVAILABLE", "이미지 응답 액션을 사용하지 못함", message.room, message.sender)
                    }
                    logger.log("WARN", "REPLY_UNAVAILABLE", "답장 가능한 알림 액션이 없음", message.room, message.sender)
                }
                is ReplyOutcome.Failed -> {
                    if (numericSelection != null) menuGate.setActive(message.room, message.sender, false)
                    if (isImageTest && imageMime != null) {
                        logger.log("ERROR", "IMAGE_REPLY_FAILED", outcome.reason, message.room, message.sender)
                    }
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
