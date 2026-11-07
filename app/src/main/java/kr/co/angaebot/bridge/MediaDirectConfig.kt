/*
 * 앙개봇 MediaSender 채팅방 직공유 실험 전용 설정 — 전체 기능
 * 1. 기존 이미지 자동전송 설정과 독립된 신규 OFF 기본값 스위치로 사용자 승인 여부를 저장한다.
 * 2. 기존 방·발신자 허용목록, PIN 보호, 접근성 및 이미지 자동전송 스위치도 전부 통과해야 한다.
 * 3. 기존 운영 토큰·SQLite DB·메뉴·로그/주식·날씨 설정을 변경하거나 초기화하지 않는다.
 * 4. Android 내부 SharedPreferences의 commit으로 사용자의 선택을 지속 보관한다.
 */
package kr.co.angaebot.bridge

import android.content.Context

internal object MediaDirectConfig {
    private const val PREF = "angaebot_media_direct_experiment"
    fun enabled(context: Context): Boolean =
        context.getSharedPreferences(PREF, Context.MODE_PRIVATE).getBoolean("enabled", false)

    fun save(context: Context, enabled: Boolean): Boolean =
        context.getSharedPreferences(PREF, Context.MODE_PRIVATE).edit()
            .putBoolean("enabled", enabled).commit()
}
