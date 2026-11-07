/*
 * 앙개봇 별도 MP4 직접전송 설정 및 사용자 명시 파일 선택 기록 — 전체 기능
 * 1. 검증된 개인 1:1 채팅방의 기존 DirectPngConfig 물리 승인 정보를 재사용하되 영상은 별도 스위치 기본 OFF이다.
 * 2. 기존 이미지 직접전송 ON/OFF와 독립적으로 동영상을 일시 허용·차단하고 기존 PNG/텍스트를 변경하지 않는다.
 * 3. 카카오톡 원격 명령으로 동영상 허용이나 사용자 파일 선택은 변경하지 않고 S20+ 관리 화면에서만 설정한다.
 * 4. Android SAF에서 선택한 원본 영상은 변경하지 않으며 앱 전용 캐시의 난수 MP4 이름만 저장한다.
 * 5. 연결된 room/sender/tag 일치·허용 목록·기본 응답 ON·별도 영상 ON을 매 전송마다 다시 검사한다.
 * 6. 파일이 없거나 캐시가 삭제됐으면 사용자가 다시 선택할 때까지 전송하지 않는다.
 * 7. 설정 해제 시 선택했던 복사본을 제거할 수 있고 기존 로그·DB·기타 미디어 캐시는 변경하지 않는다.
 * 8. 별도 토큰/비밀번호/영상 본문·임의 URL은 환경설정이나 로그에 보관하지 않는다.
 */
package kr.co.angaebot.bridge

import android.content.Context
import java.io.File

internal object DirectMp4Config {
    private const val PREF_NAME = "angaebot_direct_mp4_v01"
    private fun prefs(context: Context) = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE)

    fun enabled(context: Context): Boolean = prefs(context).getBoolean("enabled", false)

    fun saveEnabled(context: Context, enabled: Boolean): Boolean {
        if (enabled && DirectPngConfig.binding(context) == null) return false
        return prefs(context).edit().putBoolean("enabled", enabled).commit()
    }

    fun selectedFileName(context: Context): String? =
        prefs(context).getString("selected", null)?.takeIf(DirectMp4Policy::allowedFileName)

    fun saveSelected(context: Context, name: String, size: Long, durationMs: Long): Boolean {
        if (!DirectMp4Policy.allowedFileName(name) || size !in 48L..DirectMp4Policy.MAX_BYTES ||
            durationMs !in 1L..DirectMp4Policy.MAX_DURATION_MS) return false
        return prefs(context).edit()
            .putString("selected", name)
            .putLong("size", size)
            .putLong("durationMs", durationMs)
            .commit()
    }

    fun selectedSummary(context: Context): String {
        val name=selectedFileName(context) ?: return "선택된 MP4 없음"
        val file=File(File(context.cacheDir, "image-reply"), name)
        if (!file.isFile) return "MP4 캐시가 사라졌습니다. 파일을 다시 선택하세요."
        val size=prefs(context).getLong("size", file.length())
        val duration=prefs(context).getLong("durationMs", 0L)
        return "MP4 준비됨 · " + (size/1024) + " KiB · " + (duration/1000) + "초 (원본 보존)"
    }

    fun clearSelected(context: Context): Boolean {
        val old=selectedFileName(context)
        val ok=prefs(context).edit().remove("selected").remove("size").remove("durationMs").commit()
        if (ok && old != null) {
            val file=File(File(context.cacheDir, "image-reply"), old)
            if (file.isFile) file.delete()
        }
        return ok
    }

    fun authorized(context: Context, room: String, sender: String, tag: String?): Boolean {
        if (!enabled(context)) return false
        val config=BotConfig(context).load()
        if (!config.enabled || !config.isAllowedRoom(room) || !config.isAllowedSender(sender)) return false
        return DirectPngPolicy.authorized(DirectPngConfig.binding(context),room,sender,tag)
    }

    fun authorizedCandidate(context: Context, room: String, candidate: Long): Boolean {
        val binding=DirectPngConfig.binding(context) ?: return false
        return authorized(context,room,binding.sender,candidate.toString())
    }
}
