/*
 * 앙개봇 Android Bridge v0.1 — 전체 기능 설명
 * 카카오톡 알림 수신 → 허용 채팅방/발신자 필터 → '앙개야' 호출어 검사 →
 * 테스트/상태/도움말 명령 → 알림 RemoteInput 빠른 답장 요청.
 * SQLite에는 수신·차단·중복·답장 성공(요청만)·오류 모든 단계를 기록하며 관리 UI가 제공된다.
 * 이 파일은 응답 액션 탐색/전송만 담당한다. 실제 카톡 도착 여부는 확인할 수 없다.
 */
package kr.co.angaebot.bridge

import android.app.Notification
import android.app.PendingIntent
import android.app.RemoteInput
import android.content.Context
import android.content.Intent
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
}
