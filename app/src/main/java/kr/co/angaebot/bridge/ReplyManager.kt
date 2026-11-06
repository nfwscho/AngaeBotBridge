/*
 * 앙개봇 Android Bridge v0.2.0 — 전체 기능 설명
 * 카카오톡 알림 수신 → 허용 채팅방/발신자 필터 → '앙개야' 호출어 검사 →
 * 테스트/상태/도움말 명령 → 알림 RemoteInput 빠른 답장 요청.
 * SQLite에는 수신·차단·중복·답장 성공(요청만)·오류 모든 단계를 기록하며 관리 UI가 제공된다.
 * 이 파일은 응답 액션 탐색/전송만 담당한다. 실제 카톡 도착 여부는 확인할 수 없다.
 * v0.2.0 확장: Python 연결은 별도 구성·인증 모듈에서만 처리하고 이 파일의 기존 기능과 로그는 유지한다.
 * 이미지 시험 확장: 카카오톡 알림이 명시적으로 허용한 이미지 MIME 입력이 있을 때에만
 * 이미지 데이터를 앱 전용 읽기 전용 ContentProvider로 전달한다. 원래 reply()와 텍스트·예외 로그는 그대로 보존한다.
 * 이미지 전송 요청이 수락되어도 카카오톡 대화방의 실제 수신·표시 여부는 S20+로 별도 확인해야 한다.
 * 접근성 공유 시험에서는 기존 앱 전용 640x360 PNG 생성을 재사용하고 content URI만 제공하며 원래 텍스트 답장 코드는 변경하지 않는다.
 */
package kr.co.angaebot.bridge

import android.app.Notification
import android.app.PendingIntent
import android.app.RemoteInput
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.net.Uri
import java.io.File
import android.os.Build
import android.os.Bundle

sealed interface ReplyOutcome {
    data object NoAction : ReplyOutcome
    data object Requested : ReplyOutcome
    data class Failed(val reason: String) : ReplyOutcome
}

object ReplyManager {
    fun reply(context: Context, notification: Notification, replyText: String): ReplyOutcome {
        val actions = notification.actions ?: return ReplyOutcome.NoAction
        val replyAction = actions.firstOrNull { action ->
            val inputs = action.remoteInputs?.filter { it.allowFreeFormInput }.orEmpty()
            val replyLabel = action.title?.toString()?.lowercase().orEmpty()
            val semanticReply = Build.VERSION.SDK_INT >= 28 &&
                action.semanticAction == Notification.Action.SEMANTIC_ACTION_REPLY
            inputs.isNotEmpty() && (semanticReply || "답장" in replyLabel || "reply" in replyLabel)
        } ?: actions.firstOrNull { action ->
            action.remoteInputs?.any { it.allowFreeFormInput } == true
        } ?: return ReplyOutcome.NoAction

        val inputs = replyAction.remoteInputs?.filter { it.allowFreeFormInput }?.toTypedArray()
            ?: return ReplyOutcome.NoAction
        if (inputs.isEmpty()) return ReplyOutcome.NoAction

        val results = Bundle()
        inputs.forEach { input -> results.putCharSequence(input.resultKey, replyText) }
        val fillInIntent = Intent()
        RemoteInput.addResultsToIntent(inputs, fillInIntent, results)
        if (Build.VERSION.SDK_INT >= 28) {
            RemoteInput.setResultsSource(fillInIntent, RemoteInput.SOURCE_FREE_FORM_INPUT)
        }
        return try {
            replyAction.actionIntent.send(context, 0, fillInIntent)
            ReplyOutcome.Requested
        } catch (e: PendingIntent.CanceledException) {
            ReplyOutcome.Failed("취소된 알림 액션: ${e.message}")
        } catch (e: SecurityException) {
            ReplyOutcome.Failed("권한 거부: ${e.message}")
        } catch (e: RuntimeException) {
            ReplyOutcome.Failed("빠른 답장 예외: ${e.javaClass.simpleName} ${e.message}")
        }
    }
    private data class ImageTarget(val action: Notification.Action, val input: RemoteInput, val mime: String)

    private fun findImageTarget(notification: Notification): ImageTarget? =
        notification.actions?.firstNotNullOfOrNull { action ->
            action.remoteInputs?.firstNotNullOfOrNull { input ->
                ImageMimePolicy.selectMime(input.allowedDataTypes)?.let { mime ->
                    ImageTarget(action, input, mime)
                }
            }
        }

    /** 해당 카카오톡 알림 액션이 이미지 파일 입력을 명시적으로 허용할 때만 MIME 반환. */
    fun supportedImageMime(notification: Notification): String? = findImageTarget(notification)?.mime

    /** 앱이 만든 샘플만 전송 시도한다. 다른 사진이나 외부 URL은 읽지 않는다. */
    fun replyTestImage(context: Context, notification: Notification, caption: String): ReplyOutcome {
        val target = findImageTarget(notification) ?: return ReplyOutcome.NoAction
        return try {
            val fileName = if (target.mime == "image/png") "angaebot-test.png" else "angaebot-test.jpg"
            createTestImage(context, fileName, target.mime)
            val uri = Uri.Builder()
                .scheme("content")
                .authority("${context.packageName}.imageprovider")
                .appendPath(fileName)
                .build()
            val fillInIntent = Intent().addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            val textInputs = target.action.remoteInputs?.filter { it.allowFreeFormInput }.orEmpty()
            if (textInputs.isNotEmpty()) {
                val results = Bundle()
                textInputs.forEach { input -> results.putCharSequence(input.resultKey, caption) }
                RemoteInput.addResultsToIntent(textInputs.toTypedArray(), fillInIntent, results)
            }
            RemoteInput.addDataResultToIntent(target.input, fillInIntent, mapOf(target.mime to uri))
            if (Build.VERSION.SDK_INT >= 28) {
                RemoteInput.setResultsSource(fillInIntent, RemoteInput.SOURCE_FREE_FORM_INPUT)
            }
            context.grantUriPermission("com.kakao.talk", uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
            target.action.actionIntent.send(context, 0, fillInIntent)
            ReplyOutcome.Requested
        } catch (e: PendingIntent.CanceledException) {
            ReplyOutcome.Failed("이미지 알림 액션 취소: ${e.message}")
        } catch (e: SecurityException) {
            ReplyOutcome.Failed("이미지 읽기 권한 거부: ${e.message}")
        } catch (e: Exception) {
            ReplyOutcome.Failed("이미지 전송 요청 오류: ${e.javaClass.simpleName} ${e.message}")
        }
    }

    /** ACTION_SEND 공유 실험용 PNG를 앱 전용 캐시에 생성한다. 외부 사진/파일은 일절 읽지 않는다. */
    fun prepareShareTestImage(context: Context): Uri {
        createTestImage(context, "angaebot-test.png", "image/png")
        return Uri.Builder()
            .scheme("content")
            .authority("${context.packageName}.imageprovider")
            .appendPath("angaebot-test.png")
            .build()
    }

    private fun createTestImage(context: Context, fileName: String, mime: String) {
        val outputDir = File(context.cacheDir, "image-reply")
        if (!outputDir.isDirectory && !outputDir.mkdirs()) {
            throw IllegalStateException("이미지 캐시 폴더 생성 실패")
        }
        val bitmap = Bitmap.createBitmap(640, 360, Bitmap.Config.ARGB_8888)
        try {
            val canvas = Canvas(bitmap)
            canvas.drawColor(Color.rgb(25, 51, 72))
            val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                color = Color.WHITE
                textSize = 39f
                isFakeBoldText = true
            }
            canvas.drawText("AngaeBot Image Test", 44f, 160f, paint)
            paint.textSize = 27f
            paint.isFakeBoldText = false
            canvas.drawText("S20+ / Android RemoteInput", 44f, 216f, paint)
            File(outputDir, fileName).outputStream().use { stream ->
                val format = if (mime == "image/png") Bitmap.CompressFormat.PNG else Bitmap.CompressFormat.JPEG
                if (!bitmap.compress(format, 90, stream)) throw IllegalStateException("테스트 이미지 인코딩 실패")
            }
        } finally {
            bitmap.recycle()
        }
    }

}
