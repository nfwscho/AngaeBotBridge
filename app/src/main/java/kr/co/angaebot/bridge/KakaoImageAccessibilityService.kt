/*
 * 앙개봇 S20+ 카카오톡 실제 사진 자동전송 실험 서비스 — 전체 기능/보안/로그
 * 1. 기존 카카오톡 알림 텍스트 답장/허용 방·발신자 필터/Python Core/배터리/SQLite 로그/관리 UI를 변경하지 않는다.
 * 2. 사용자가 Android 접근성 권한과 별도 이미지 자동전송 스위치를 모두 켠 경우에만 이미지 전송 시험을 수락한다.
 * 3. 잠금 화면에서는 작업을 시작하지 않고, 사용자 허용 채팅방 이름이 명확하지 않아도 전송하지 않는다.
 * 4. Android ACTION_SEND와 앱 자체 ContentProvider의 테스트 PNG를 사용하며 다른 파일·개인 사진은 접근하지 않는다.
 * 5. 카카오톡 화면에서 실제 방 이름이 단일·정확히 일치하고 공유 UI 단서가 있을 때만 방을 선택한다.
 * 6. 이후 화면에 같은 방 이름·사진 첨부 단서·단일 '보내기' 버튼이 보일 때에만 전송 버튼을 누른다.
 * 7. UI 구조가 다르거나 15초 내 대상 확인에 실패하면 아무 곳에도 전송하지 않는다. 좌표 클릭/화면 OCR은 사용하지 않는다.
 * 8. 새 작업 도중 중복 수락을 거부하고 UI 조작 성공과 실제 카카오톡 수신 성공을 엄격히 구분해 로그를 남긴다.
 * 9. 사용자 대화/상대방 목록의 화면 텍스트를 저장·전송하지 않는다. 로그는 단계명과 버튼 탐지 개수만 기록한다.
 * 10. 공유 Activity는 Android의 백그라운드 실행 제한으로 열리지 않을 수 있으며, 그 경우 기존 RemoteInput 텍스트 답장은 유지된다.
 * 11. 이 모듈은 실기기 카카오톡 버전별 확인을 위한 fail-closed 실험판으로 정상 수신 보장은 하지 않는다.
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
        var stage: ImageUiStage = ImageUiStage.PICK_ROOM
    )

    private val handler = Handler(Looper.getMainLooper())
    private lateinit var logger: LogRepository
    private var activeJob: ImageJob? = null

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
        if (event?.packageName?.toString() != KAKAO_PACKAGE) return
        if (!ImageAutoConfig.enabled(this) || !BotConfig(this).load().enabled) {
            finish("IMAGE_UI_ABORTED", "자동응답/이미지 전송 OFF로 중단", true)
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
        }
        val sendCandidates = nodes.filter { node ->
            (node.text?.toString()?.trim() in setOf("보내기", "전송", "확인") ||
             node.contentDescription?.toString()?.trim() in setOf("보내기", "전송", "확인")) &&
                clickableParent(node) != null && node.isVisibleToUser
        }
        val decision = ImageUiPolicy.action(
            job.stage, job.room, ImageUiSnapshot(labeled, roomCandidates.size, sendCandidates.size)
        )
        when (decision) {
            ImageUiAction.WAIT -> return
            ImageUiAction.CLICK_ROOM -> {
                if (roomCandidates.size == 1 &&
                    clickableParent(roomCandidates[0])?.performAction(AccessibilityNodeInfo.ACTION_CLICK) == true) {
                    job.stage = ImageUiStage.CONFIRM_IMAGE
                    logger.log("INFO", "IMAGE_UI_ROOM_SELECTED", "검증된 동일 이름 채팅방 항목 선택 요청")
                } else {
                    finish("IMAGE_UI_ABORTED", "대상 방 항목을 클릭하지 못함", true)
                }
            }
            ImageUiAction.CLICK_SEND -> {
                if (sendCandidates.size == 1 &&
                    clickableParent(sendCandidates[0])?.performAction(AccessibilityNodeInfo.ACTION_CLICK) == true) {
                    finish("IMAGE_UI_SEND_REQUESTED",
                        "사진 보내기 UI 버튼 클릭 요청 성공(실제 카카오톡 수신 확인 불가)", false)
                } else {
                    finish("IMAGE_UI_ABORTED", "이미지 전송 UI 클릭 불가", true)
                }
            }
        }
    }

    private fun collectNodes(node: AccessibilityNodeInfo, results: MutableList<AccessibilityNodeInfo>, depth: Int) {
        if (depth > 20 || results.size >= 250) return
        if (!node.isVisibleToUser) return
        results.add(node)
        for (i in 0 until node.childCount) {
            val child = node.getChild(i) ?: continue
            collectNodes(child, results, depth + 1)
            if (results.size >= 250) return
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

    private fun beginShare(room: String): ImageAutoStart {
        if (!ImageAutoConfig.enabled(this)) return ImageAutoStart.Rejected("이미지 자동전송 스위치 OFF")
        val settings = BotConfig(this).load()
        if (!settings.enabled || !settings.isAllowedRoom(room)) {
            return ImageAutoStart.Rejected("자동응답 OFF 또는 허용되지 않은 채팅방")
        }
        if (room.isBlank() || room.length > 100) return ImageAutoStart.Rejected("채팅방 식별 불가")
        val lock = getSystemService(Context.KEYGUARD_SERVICE) as KeyguardManager
        if (lock.isKeyguardLocked) return ImageAutoStart.Rejected("화면 잠금 해제 필요")
        if (activeJob != null) return ImageAutoStart.Rejected("이전 이미지 작업 진행 중")
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
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        return try {
            grantUriPermission(KAKAO_PACKAGE, uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
            val job = ImageJob(room, SystemClock.elapsedRealtime())
            activeJob = job
            logger.log("INFO", "IMAGE_UI_QUEUED", "정확한 허용 채팅방 기준 이미지 공유 준비")
            handler.postDelayed({
                if (activeJob !== job) return@postDelayed
                try {
                    startActivity(intent)
                    logger.log("INFO", "IMAGE_UI_SHARE_OPEN_REQUESTED",
                        "Android ACTION_SEND로 카카오톡 사진 공유 화면 열기 요청")
                } catch (e: Exception) {
                    finish("IMAGE_UI_ABORTED", "공유 화면 시작 실패: ${e.javaClass.simpleName}", true)
                }
            }, 900L)
            handler.postDelayed({
                if (activeJob === job) finish("IMAGE_UI_TIMEOUT",
                    "15초 안에 안전하게 확인된 카카오톡 이미지 공유 UI가 나타나지 않음", true)
            }, EXPIRE_MS + 100L)
            ImageAutoStart.Queued
        } catch (e: Exception) {
            activeJob = null
            ImageAutoStart.Rejected("이미지 공유 요청 실패: ${e.javaClass.simpleName}")
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
        private const val EXPIRE_MS = 15_000L
        @Volatile private var connected: KakaoImageAccessibilityService? = null

        fun isConnected(): Boolean = connected != null

        fun queueTest(room: String): ImageAutoStart {
            val service = connected ?: return ImageAutoStart.Rejected("접근성 서비스 미연결")
            return service.beginShare(room)
        }
    }
}
