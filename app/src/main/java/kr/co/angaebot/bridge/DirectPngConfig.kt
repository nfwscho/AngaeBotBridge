/*
 * 앙개봇 검증된 1:1 대상만 사용하는 PNG 직접전송 설정 — 전체 기능 설명
 * 1. 실험 A/B MediaDirectConfig와 분리된 별도 기본 OFF 스위치를 제공한다.
 * 2. 검증 후보는 S20+ 사용자가 화면의 명시적 버튼과 확인 대화상자를 눌러야만 등록된다.
 * 3. 단 한 1:1 room/sender 및 알림 tag 후보를 등록하며 2번째 연결 시 교체를 명시적으로 요구한다.
 * 4. 앱 전용 SharedPreferences에만 연결 기록 저장; Android 앱 백업은 기존대로 비활성.
 * 5. 기존 카카오톡 허용 목록에서 방/발신자가 제거되면 새 사진 전송도 즉시 거절한다.
 * 6. 직접전송 스위치 OFF/연결 해제 동작은 기존 이미지 실험/텍스트/DB/.env/로그를 변경하지 않는다.
 * 7. 공유 스위치를 잘못 누른 경우에도 후보 승인과 별도 작동 ON이 모두 필요하다.
 * 8. 토큰/전체 후보 ID는 카카오톡 답장이나 로그로 기록하지 않는다.
 */
package kr.co.angaebot.bridge

import android.content.Context

internal object DirectPngConfig {
    private const val PREF = "angaebot_direct_png_v01"
    fun enabled(context:Context):Boolean =
        context.getSharedPreferences(PREF,Context.MODE_PRIVATE).getBoolean("enabled",false)
    fun binding(context:Context):DirectPngBinding? {
        val p=context.getSharedPreferences(PREF,Context.MODE_PRIVATE)
        val room=p.getString("room",null).orEmpty()
        val sender=p.getString("sender",null).orEmpty()
        val tag=p.getString("tag",null)
        val id=MediaDirectPolicy.candidate(tag,room,sender) ?: return null
        return DirectPngBinding(room,sender,id)
    }
    fun saveEnabled(context:Context,on:Boolean):Boolean {
        if(on && binding(context)==null) return false
        return context.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit()
            .putBoolean("enabled",on).commit()
    }
    fun approve(context:Context,candidate:DirectPngBinding):Boolean {
        if(candidate.room!=candidate.sender || candidate.room.isBlank()) return false
        val settings=BotConfig(context).load()
        if(!settings.enabled || !settings.isAllowedRoom(candidate.room) ||
            !settings.isAllowedSender(candidate.sender)) return false
        return context.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit()
            .putString("room",candidate.room)
            .putString("sender",candidate.sender)
            .putString("tag",candidate.tag.toString())
            .putBoolean("enabled",false).commit()
    }
    fun clear(context:Context):Boolean =
        context.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().clear().commit()

    fun authorized(context:Context,room:String,sender:String,tag:String?):Boolean {
        if(!enabled(context)) return false
        val settings=BotConfig(context).load()
        if(!settings.enabled || !settings.isAllowedRoom(room) || !settings.isAllowedSender(sender)) return false
        return DirectPngPolicy.authorized(binding(context),room,sender,tag)
    }
    fun authorizedCandidate(context:Context,room:String,candidate:Long):Boolean {
        val binding=binding(context) ?: return false
        return authorized(context,room,binding.sender,candidate.toString())
    }
}
