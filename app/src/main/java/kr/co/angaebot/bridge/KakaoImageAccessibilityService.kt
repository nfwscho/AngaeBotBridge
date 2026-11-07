/*
 * 앙개봇 S20+ 카카오톡 실제 사진 자동전송 실험 서비스 — 전체 기능/보안/로그
 * 1. 기존 카카오톡 알림 텍스트 답장/허용 방·발신자 필터/Python Core/배터리/SQLite 로그/관리 UI를 변경하지 않는다.
 * 2. 사용자가 Android 접근성 권한과 별도 이미지 자동전송 스위치를 모두 켠 경우에만 이미지 전송 시험을 수락한다.
 * 3. 잠금 화면에서 인증이 필요한 기기는 거절하고, 인증 불필요한 잠금/꺼진 화면은 공식 Android 잠금 해제 API로 깨운다.
 * 3-1. PIN·패턴·비밀번호 및 사용자 인증 정보는 저장·입력·우회하지 않고 안전하게 거부한다.
 * 4. Android ACTION_SEND와 앱 자체 ContentProvider의 테스트 PNG를 사용하며 다른 파일·개인 사진은 접근하지 않는다.
 * 5. 카카오톡 화면에서 실제 방 이름이 단일·정확히 일치하고 공유 UI 단서가 있을 때만 방을 선택한다.
 * 6. 이후 화면에 같은 방 이름·사진 첨부 단서·단일 '보내기' 버튼이 보일 때에만 전송 버튼을 누른다.
 * 7. UI 구조가 다르거나 15초 내 대상 확인에 실패하면 아무 곳에도 전송하지 않는다. 좌표 클릭/화면 OCR은 사용하지 않는다.
 * 8. 새 작업 도중 중복 수락을 거부하고 UI 조작 성공과 실제 카카오톡 수신 성공을 엄격히 구분해 로그를 남긴다.
 * 9. 사용자 대화/상대방 목록의 화면 텍스트를 저장·전송하지 않는다. 로그는 단계명과 버튼 탐지 개수만 기록한다.
 * 10. 공유 Activity는 Android의 백그라운드 실행 제한으로 열리지 않을 수 있으며, 그 경우 기존 RemoteInput 텍스트 답장은 유지된다.
 * 11. 이 모듈은 실기기 카카오톡 버전별 확인을 위한 fail-closed 실험판으로 정상 수신 보장은 하지 않는다.
 * 12. 공유 Activity 실행 요청 전의 과거 카카오톡 UI 이벤트는 무시해 다른 대화방의 기존 보내기 버튼을 누르지 않는다.
 * 13. v0.4.17은 사진 확인 화면에서 방 이름이 숨겨진 경우에도 앞 단계의 정확한 방 선택을 기억하고 이미지 미리보기를 검증한다.
 * 14. 350ms 이상 지난 최종 화면에서 유일한 보내기 버튼만 찾아 누르며, 미확인/중복 버튼/잠금 상태에서는 중단한다.
 * 15. 카카오 UI 변경 진단은 화면 내용·채팅 문구 없이 단계/버튼 개수/사진 미리보기 유무만 주기적으로 기록한다.
 * 16. v0.4.18은 Android 공식 화면 깨우기 Activity로 사용자 인증이 불필요한 경우에만 공유를 재개한다.
 * 17. 일회성 토큰·화면 잠금 재검사·타임아웃·기존 Image_UI 및 IMAGE_WAKE 로그와 접근성 방 검증을 유지한다.
 * 18. v0.4.19는 S20+ 공유 화면 하단의 '1 보내기'를 인식해 선택된 1명에게만 전송하도록 보완한다.
 * 19. 기존 수신 방 선택 성공/단일 버튼/잠금/타임아웃/사진 확인/모든 기존 로그와 응답 흐름을 보존한다.
 * 20. v0.4.22에서 사용자가 별도 승인한 경우에만 MediaSender 방식의 3가지 채팅방 직접 지정 인텐트 힌트를 추가한다.
 * 21. 기존 공유/사진/방 선택/버튼 클릭/잠금 인증 제한 로직은 전부 유지하고 직공유는 실제 수신 미확인으로 기록한다.
 * 22. 알림 숫자형 tag가 실제 카카오 채널 ID인지 미검증이며 자체 2단계 진단 후 1:1 시험에만 사용한다.
 * 23. v0.4.23 직공유경로확인은 Intent만 띄우고 수신자/전송 버튼을 절대 클릭하지 않는 관찰 모드다.
 * 24. 수신자 선택창과 직접 목적지 화면의 징후를 UI 텍스트 저장 없이 분류하며 실제 ID·전송 완료로 단정하지 않는다.
 * 25. 기존 직공유시험의 방 클릭은 MEDIA_DIRECT_FALLBACK_ROOM_CLICK 로그로 식별하고 기존 자동전송 경로는 보존한다.
 */
package kr.co.angaebot.bridge

import android.accessibilityservice.AccessibilityService
import android.app.KeyguardManager
import android.content.ClipData
import android.content.Context
import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.os.PowerManager
import java.util.UUID
import android.graphics.Rect
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo

internal object ImageAutoConfig {
    private const val PREF = "angaebot_image_auto"
    fun enabled(context: Context): Boolean =
        context.getSharedPreferences(PREF, Context.MODE_PRIVATE).getBoolean("enabled", false)

    fun save(context: Context, enabled: Boolean): Boolean =
        context.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit()
            .putBoolean("enabled", enabled).commit()
}

internal sealed interface ImageAutoStart {
    data object Queued : ImageAutoStart
    data class Rejected(val reason: String) : ImageAutoStart
}

class KakaoImageAccessibilityService : AccessibilityService() {
    private data class ImageJob(
        val room: String,
        val startedMs: Long,
        @Volatile var shareLaunched: Boolean = false,
        var stage: ImageUiStage = ImageUiStage.PICK_ROOM,
        var selectedRoomAtMs: Long = 0L,
        var lastDiagnosticAtMs: Long = 0L,
        val shareIntent: Intent,
        val wakeToken: String,
        val directCandidate: Long? = null,
        val observeOnly: Boolean = false,
        @Volatile var wakePending: Boolean = false
    )

    private val handler = Handler(Looper.getMainLooper())
    private lateinit var logger: LogRepository
    @Volatile private var activeJob: ImageJob? = null

    override fun onCreate() {
        super.onCreate()
        logger = LogRepository(this)
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        connected = this
        logger.log("INFO", "IMAGE_UI_CONNECTED", "이미지 전송용 접근성 서비스 연결(별도 기능 OFF 기본값)")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        val job = activeJob ?: return
        if (!job.shareLaunched || event?.packageName?.toString() != KAKAO_PACKAGE) return
        inspectCurrentWindow(job)
    }

    private fun inspectCurrentWindow(job: ImageJob) {
        if (activeJob !== job || !job.shareLaunched) return
        val settings = BotConfig(this).load()
        if (!ImageAutoConfig.enabled(this) ||
            (job.directCandidate != null && !MediaDirectConfig.enabled(this)) ||
            !settings.enabled || !settings.isAllowedRoom(job.room)) {
            finish("IMAGE_UI_ABORTED", "자동응답/이미지 전송 OFF 또는 허용 채팅방 변경으로 중단", true)
            return
        }
        if (SystemClock.elapsedRealtime() - job.startedMs > EXPIRE_MS) {
            finish("IMAGE_UI_TIMEOUT", "대상/사진 확인 시간 초과", true)
            return
        }
        val lock = getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager
        if (lock.isKeyguardLocked) {
            finish("IMAGE_UI_ABORTED", "화면 잠금 감지", true)
            return
        }
        val root = rootInActiveWindow ?: return
        if (root.packageName?.toString() != KAKAO_PACKAGE) return
        val nodes = mutableListOf<AccessibilityNodeInfo>()
        collectNodes(root, nodes, 0)
        val labeled = nodes.mapNotNull { node ->
            val text = node.text?.toString()?.trim().orEmpty()
            val desc = node.contentDescription?.toString()?.trim().orEmpty()
            when {
                text.isNotEmpty() -> text
                desc.isNotEmpty() -> desc
                else -> null
            }
        }
        val roomCandidates = nodes.filter { node ->
            (node.text?.toString()?.trim() == job.room ||
             node.contentDescription?.toString()?.trim() == job.room) &&
                clickableParent(node) != null && node.isVisibleToUser
        }.mapNotNull { clickableParent(it) }.distinct()
        // 팝업의 일반 '확인'은 전송 버튼으로 인정하지 않는다.
        val sendCandidates = nodes.filter { node ->
            isExplicitSendControl(node) && node.isVisibleToUser
        }.mapNotNull { clickableParent(it) }.distinct()
        val density = resources.displayMetrics.density
        val imagePreview = nodes.any { node ->
            if (!node.className.toString().endsWith("ImageView")) false else {
                val bounds = Rect()
                node.getBoundsInScreen(bounds)
                bounds.width() >= 160f * density && bounds.height() >= 95f * density
            }
        }
        if (job.observeOnly) {
            // 관찰 모드는 카카오톡 공유 Activity를 열기만 한다.
            // 수신 방 선택 및 보내기 버튼은 이 경로에서 절대로 자동 클릭하지 않는다.
            val isPicker = labeled.any { it in setOf("채팅방", "대화방", "친구", "공유", "전송 대상", "보낼 대상") }
            val observation = MediaDirectRoutePolicy.classify(MediaDirectRouteSnapshot(
                recipientPickerHeadingVisible = isPicker,
                clickableRoomCount = roomCandidates.size,
                exactTargetNameVisible = labeled.any { it == job.room },
                sendButtonCount = sendCandidates.size
            ))
            if (observation != MediaDirectRoute.UNVERIFIED) {
                finish("MEDIA_DIRECT_PROBE_RESULT",
                    "route=" + observation.name +
                        " targetNameVisible=" + labeled.any { it == job.room } +
                        " roomChoices=" + roomCandidates.size +
                        " sendButtons=" + sendCandidates.size +
                        " autoClick=false · 실제 채팅방 ID/수신 확인 아님", false)
            } else if (SystemClock.elapsedRealtime() - job.lastDiagnosticAtMs >= 2500L) {
                job.lastDiagnosticAtMs = SystemClock.elapsedRealtime()
                logger.log("INFO", "MEDIA_DIRECT_PROBE_WAIT",
                    "pickerHeading=" + isPicker +
                        " targetNameVisible=" + labeled.any { it == job.room } +
                        " roomChoices=" + roomCandidates.size +
                        " sendButtons=" + sendCandidates.size +
                        " autoClick=false")
            }
            return
        }
        val elapsedSinceSelection = SystemClock.elapsedRealtime() - job.selectedRoomAtMs
        val readyAfterRoomSelection = job.selectedRoomAtMs > 0L && elapsedSinceSelection >= 350L
        val decision = ImageUiPolicy.action(
            job.stage, job.room,
            ImageUiSnapshot(labeled, roomCandidates.size, sendCandidates.size,
                selectedRoomVerified = job.selectedRoomAtMs > 0L,
                afterRoomClick = readyAfterRoomSelection,
                largeImagePreviewVisible = imagePreview,
                explicitSendControlVisible = nodes.any { isExplicitSendControl(it) })
        )
        if (decision == ImageUiAction.WAIT && job.stage == ImageUiStage.CONFIRM_IMAGE &&
            SystemClock.elapsedRealtime() - job.lastDiagnosticAtMs >= 2000L) {
            job.lastDiagnosticAtMs = SystemClock.elapsedRealtime()
            logger.log("INFO", "IMAGE_UI_CONFIRM_WAIT",
                "recipientOnScreen=${labeled.count { it == job.room }} mediaPreview=$imagePreview sendButtons=${sendCandidates.size} roomSelectionReady=$readyAfterRoomSelection")
        }
        when (decision) {
            ImageUiAction.WAIT -> return
            ImageUiAction.CLICK_ROOM -> {
                if (roomCandidates.size == 1 &&
                    roomCandidates[0].performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                    job.stage = ImageUiStage.CONFIRM_IMAGE
                    job.selectedRoomAtMs = SystemClock.elapsedRealtime()
                    logger.log("INFO", "IMAGE_UI_ROOM_SELECTED", "검증된 동일 이름 채팅방 항목 선택 요청")
                    if (job.directCandidate != null) {
                        logger.log("INFO", "MEDIA_DIRECT_FALLBACK_ROOM_CLICK",
                            "직공유시험에서 기존 수신자 클릭이 실행됨 · key_id 만으로 방 선택을 건너뛰지 않았음")
                    }
                    // 이벤트를 생략하는 카카오 UI에서도 후속 화면을 반복 확인한다.
                    for (delay in longArrayOf(550L, 1150L, 2100L, 3500L, 5500L)) {
                        handler.postDelayed({
                            if (activeJob === job) inspectCurrentWindow(job)
                        }, delay)
                    }
                } else {
                    finish("IMAGE_UI_ABORTED", "대상 방 항목을 클릭하지 못함", true)
                }
            }
            ImageUiAction.CLICK_SEND -> {
                if (sendCandidates.size == 1 &&
                    sendCandidates[0].performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                    finish("IMAGE_UI_SEND_REQUESTED",
                        "사진 보내기 UI 버튼 클릭 요청 성공(실제 카카오톡 수신 확인 불가)", false)
                } else {
                    finish("IMAGE_UI_ABORTED", "이미지 전송 UI 클릭 불가", true)
                }
            }
        }
    }

    private fun isExplicitSendControl(node: AccessibilityNodeInfo): Boolean {
        val labels = listOfNotNull(node.text?.toString()?.trim(), node.contentDescription?.toString()?.trim())
        // 1 보내기처럼 선택 인원 수가 붙은 카카오 공유 화면 버튼도 인식한다.
        // 2 보내기 등의 복수 선택은 ImageUiPolicy에서 별도로 차단한다.
        val textMatches = labels.any { ImageSendButtonLabel.matches(it) }
        val resourceName = node.viewIdResourceName?.substringAfterLast('/')?.lowercase().orEmpty()
        val idMatches = resourceName in setOf("btn_send", "button_send", "send_button",
            "action_send", "share_send", "send")
        return textMatches || idMatches
    }

    private fun collectNodes(node: AccessibilityNodeInfo, results: MutableList<AccessibilityNodeInfo>, depth: Int) {
        if (depth > 20 || results.size >= 400) return
        if (!node.isVisibleToUser) return
        results.add(node)
        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            collectNodes(child, results, depth + 1)
            if (results.size >= 400) return
        }
    }

    private fun clickableParent(node: AccessibilityNodeInfo): AccessibilityNodeInfo? {
        var current: AccessibilityNodeInfo? = node
        repeat(6) {
            if (current?.isClickable == true && current?.isEnabled == true) return current
            current = current?.parent
        }
        return null
    }

    private fun beginShare(room: String, directCandidate: Long? = null, observeOnly: Boolean = false): ImageAutoStart {
        if (!ImageAutoConfig.enabled(this)) return ImageAutoStart.Rejected("이미지 자동전송 스위치 OFF")
        if (directCandidate != null && !MediaDirectConfig.enabled(this)) {
            return ImageAutoStart.Rejected("MediaSender 직공유 실험 스위치 OFF")
        }
        val settings = BotConfig(this).load()
        if (!settings.enabled || !settings.isAllowedRoom(room)) {
            return ImageAutoStart.Rejected("자동응답 OFF 또는 허용되지 않은 채팅방")
        }
        if (room.isBlank() || room.length > 100) return ImageAutoStart.Rejected("채팅방 식별 불가")
        if (activeJob != null) return ImageAutoStart.Rejected("이전 이미지 작업 진행 중")
        val lock = getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager
        val power = getSystemService(Context.POWER_SERVICE) as PowerManager
        val action = ImageLockPolicy.evaluate(lock.isKeyguardLocked, lock.isDeviceLocked, power.isInteractive)
        if (action == ImageLockAction.AUTH_REQUIRED) {
            logger.log("WARN", "IMAGE_WAKE_AUTH_REQUIRED", "S20+에 사용자 인증이 필요한 잠금이 걸림")
            return ImageAutoStart.Rejected("S20+ 보안 잠금 인증 필요: PIN·패턴·비밀번호는 자동 해제하지 않습니다.")
        }
        val uri = try {
            ReplyManager.prepareShareTestImage(this)
        } catch (e: Exception) {
            return ImageAutoStart.Rejected("테스트 이미지 준비 실패: ${e.javaClass.simpleName}")
        }
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "image/png"
            setPackage(KAKAO_PACKAGE)
            putExtra(Intent.EXTRA_STREAM, uri)
            clipData = ClipData.newUri(contentResolver, "AngaeBot photo test", uri)
            if (directCandidate != null) {
                // MediaSender의 공유 힌트를 실험한다. 공식 API 아님·타겟/전송 성공 보장 없음.
                putExtra("key_id", directCandidate)
                putExtra("key_type", 1)
                putExtra("key_from_direct_share", true)
                addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP)
            }
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        return try {
            grantUriPermission(KAKAO_PACKAGE, uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
            val job = ImageJob(room, SystemClock.elapsedRealtime(),
                shareIntent = intent, wakeToken = UUID.randomUUID().toString(),
                directCandidate = directCandidate,
                observeOnly = observeOnly,
                wakePending = action == ImageLockAction.WAKE)
            activeJob = job
            logger.log("INFO", "IMAGE_UI_QUEUED", "허용 채팅방 기준 이미지 공유 준비")
            if (action == ImageLockAction.WAKE) {
                logger.log("INFO", "IMAGE_WAKE_REQUESTED", "사용자 인증 불필요: Android 공식 화면 깨우기 요청")
                handler.post {
                    if (activeJob !== job || !job.wakePending) return@post
                    try {
                        startActivity(Intent(this, ImageWakeActivity::class.java).apply {
                            putExtra(ImageWakeActivity.EXTRA_TOKEN, job.wakeToken)
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or
                                Intent.FLAG_ACTIVITY_NO_HISTORY or Intent.FLAG_ACTIVITY_EXCLUDE_FROM_RECENTS)
                        })
                    } catch (e: Exception) {
                        finish("IMAGE_WAKE_FAILED", "깨우기 Activity 시작 오류: ${e.javaClass.simpleName}", true)
                    }
                }
            } else {
                handler.postDelayed({ launchShare(job) }, 900L)
            }
            handler.postDelayed({
                if (activeJob === job) {
                    if (job.observeOnly) {
                        finish("MEDIA_DIRECT_PROBE_TIMEOUT",
                            "카카오톡 공유 화면 식별 실패 · 자동 클릭 없음 · 채팅방 ID 미검증", true)
                    } else {
                        finish("IMAGE_UI_TIMEOUT", "잠금/이미지 화면 확인 시간 초과", true)
                    }
                }
            }, EXPIRE_MS + 100L)
            ImageAutoStart.Queued
        } catch (e: Exception) {
            activeJob = null
            ImageAutoStart.Rejected("이미지 공유 시작 오류: ${e.javaClass.simpleName}")
        }
    }

    private fun onWakeResult(token: String, success: Boolean, reason: String) {
        handler.post {
            val job = activeJob ?: return@post
            if (job.wakeToken != token || !job.wakePending) return@post
            job.wakePending = false
            if (!success) {
                finish("IMAGE_WAKE_FAILED", reason, true)
            } else {
                logger.log("INFO", "IMAGE_WAKE_DISMISSED", "인증 불필요 잠금 해제 확인 후 공유 단계 재개")
                handler.postDelayed({
                    if (activeJob === job) launchShare(job)
                }, 350L)
            }
        }
    }

    /** 재개 직전 허용목록과 잠금 상태를 다시 확인하여 잠긴 화면에는 사진을 전송하지 않는다. */
    private fun launchShare(job: ImageJob) {
        if (activeJob !== job || job.shareLaunched || job.wakePending) return
        val settings = BotConfig(this).load()
        if (!ImageAutoConfig.enabled(this) ||
            (job.directCandidate != null && !MediaDirectConfig.enabled(this)) ||
            !settings.enabled || !settings.isAllowedRoom(job.room)) {
            finish("IMAGE_UI_ABORTED", "자동응답/이미지 설정 또는 허용 채팅방 변경", true)
            return
        }
        val lock = getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager
        if (lock.isKeyguardLocked || lock.isDeviceLocked) {
            finish("IMAGE_WAKE_FAILED", "잠금 미해제 또는 재잠금 감지", true)
            return
        }
        try {
            startActivity(job.shareIntent)
            job.shareLaunched = true
            logger.log("INFO", "IMAGE_UI_SHARE_OPEN_REQUESTED", "Android ACTION_SEND 카카오톡 사진 공유 화면 열기 요청")
            if (job.observeOnly) {
                logger.log("INFO", "MEDIA_DIRECT_PROBE_STARTED",
                    "공유 UI 읽기 전용 관찰 · 수신자/보내기 자동 클릭 비활성 · 20초 타임아웃")
                for (delay in longArrayOf(450L, 1100L, 2200L, 4000L)) {
                    handler.postDelayed({
                        if (activeJob === job && job.shareLaunched) inspectCurrentWindow(job)
                    }, delay)
                }
            }
            if (job.directCandidate != null) {
                logger.log("INFO", "MEDIA_DIRECT_INTENT_STARTED",
                    "알림 태그 기반 key_id 힌트 포함 · 후보 " + MediaDirectPolicy.mask(job.directCandidate) +
                        " · 실제 수신/대상은 S20+ 카카오톡에서 확인 필요")
            }
        } catch (e: Exception) {
            finish("IMAGE_UI_ABORTED", "공유 화면 시작 오류: ${e.javaClass.simpleName}", true)
        }
    }

    private fun finish(stage: String, reason: String, warning: Boolean) {
        if (activeJob == null) return
        activeJob = null
        logger.log(if (warning) "WARN" else "INFO", stage, reason)
    }

    override fun onInterrupt() {
        finish("IMAGE_UI_INTERRUPTED", "Android 접근성 서비스 일시 중단", true)
    }

    override fun onDestroy() {
        if (connected === this) connected = null
        finish("IMAGE_UI_INTERRUPTED", "접근성 서비스 종료", true)
        super.onDestroy()
    }

    companion object {
        private const val KAKAO_PACKAGE = "com.kakao.talk"
        private const val EXPIRE_MS = 20_000L
        @Volatile private var connected: KakaoImageAccessibilityService? = null

        fun isConnected(): Boolean = connected != null

        internal fun wakeResult(token: String, success: Boolean, reason: String) {
            connected?.onWakeResult(token, success, reason)
        }

        internal fun queueTest(room: String): ImageAutoStart {
            val service = connected ?: return ImageAutoStart.Rejected("접근성 서비스 미연결")
            return service.beginShare(room)
        }

        internal fun queueDirectTest(room: String, candidate: Long): ImageAutoStart {
            val service = connected ?: return ImageAutoStart.Rejected("접근성 서비스 미연결")
            if (candidate <= 0L) return ImageAutoStart.Rejected("잘못된 채팅방 ID 후보")
            return service.beginShare(room, candidate)
        }

        internal fun queueRouteProbe(room: String, candidate: Long): ImageAutoStart {
            val service = connected ?: return ImageAutoStart.Rejected("접근성 서비스 미연결")
            if (candidate <= 0L) return ImageAutoStart.Rejected("잘못된 채팅방 ID 후보")
            return service.beginShare(room, candidate, observeOnly = true)
        }
    }
}
