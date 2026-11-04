/*
 * 앙개봇 Android Bridge v0.2.0 — 전체 기능 설명
 * 1) 카카오톡(com.kakao.talk) 알림을 감지하고 명령 호출어(기본 '앙개야')를 검사한다.
 * 2) 사용자가 명시적으로 허용한 정확한 채팅방 이름 + 발신자 이름을 둘 다 확인한다.
 * 3) 테스트, 상태, 도움말 명령을 수행하고 알림의 RemoteInput으로 답장을 시도한다.
 * 4) 알림 갱신으로 인한 중복 명령은 SQLite로 제한하고 모든 처리 단계/오류를 보관한다.
 * 5) Android 관리 화면에서 ON/OFF, 허용 목록, 로그 열람·내보내기·삭제를 제어한다.
 * 6) 기본 OFF / 빈 허용 목록, 서버·인터넷 연결 없이 1단계를 수행한다.
 * 이 파일은 설정 저장/로드를 담당한다. 알림의 사람 이름은 강력한 본인 인증이 아니다.
 * v0.2.0 확장: Python 연결은 별도 구성·인증 모듈에서만 처리하고 이 파일의 기존 기능과 로그는 유지한다.
 */
package kr.co.angaebot.bridge

import android.content.Context

/** 자동응답은 기본적으로 꺼져 있고 허용 목록이 없으면 절대로 실행되지 않는다. */
data class SettingsSnapshot(
    val enabled: Boolean,
    val wakeWord: String,
    val allowedRooms: Set<String>,
    val allowedSenders: Set<String>
) {
    fun isAllowedRoom(value: String) = value.isNotBlank() && value in allowedRooms
    fun isAllowedSender(value: String) = value.isNotBlank() && value in allowedSenders
}

class BotConfig(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences("angaebot_settings", Context.MODE_PRIVATE)

    fun load(): SettingsSnapshot = SettingsSnapshot(
        enabled = prefs.getBoolean("enabled", false),
        wakeWord = prefs.getString("wake_word", "앙개야")?.trim().orEmpty().ifBlank { "앙개야" },
        allowedRooms = parseLines(prefs.getString("rooms", "").orEmpty()),
        allowedSenders = parseLines(prefs.getString("senders", "").orEmpty())
    )

    fun save(enabled: Boolean, wakeWord: String, roomText: String, senderText: String) {
        val wake = wakeWord.trim()
        require(wake.length in 2..30 && !wake.contains('\n')) { "호출어는 2~30자여야 합니다." }
        val rooms = parseLines(roomText)
        val senders = parseLines(senderText)
        if (enabled) require(rooms.isNotEmpty() && senders.isNotEmpty()) { "활성화하려면 허용 채팅방과 발신자를 각각 입력하세요." }
        prefs.edit()
            .putBoolean("enabled", enabled)
            .putString("wake_word", wake)
            .putString("rooms", rooms.joinToString("\n"))
            .putString("senders", senders.joinToString("\n"))
            .apply()
    }

    /** 잘못된 편집 값에 관계없이 즉시 OFF. 디스크에도 동기적으로 저장한다. */
    fun disableImmediately(): Boolean = prefs.edit().putBoolean("enabled", false).commit()

    companion object {
        fun parseLines(raw: String): Set<String> = raw.lineSequence()
            .map { it.trim() }
            .filter { it.isNotBlank() }
            .toCollection(linkedSetOf())
    }
}
