/*
 * 앙개봇 카카오톡 사진 보내기 버튼 라벨 정책 — 전체 기능 및 보안
 * 1. 기존 '보내기', '전송', 사진 보내기, 영어 Send 등의 버튼 인식 기능을 보존한다.
 * 2. S20+ 공유 화면의 '1 보내기'와 '1 전송'을 인식하여 정확히 한 대상으로만 전송하도록 한다.
 * 3. 공백/줄바꿈/비분리 공백을 정규화해 접근성 레이블 표시 차이에 대응한다.
 * 4. '2 보내기' 등의 복수 수신 대상/0/부분 문자열 등은 인식하지 않으며 정책 단계에서 거부한다.
 * 5. 순수 Kotlin 정책으로 카카오톡/Android UI/DB/설정/로그/Python Core를 직접 변경하지 않는다.
 * 6. 대상 방 검증·버튼 단일성·사진 공유 화면 확인은 기존 접근성 서비스에서 별도로 수행한다.
 */
package kr.co.angaebot.bridge

internal object ImageSendButtonLabel {
    private val legacy = setOf(
        "보내기", "전송", "전송하기", "사진 보내기", "사진 전송",
        "이미지 보내기", "Send", "Send photo"
    )
    private val counted = Regex("^(\\d+)\\s*(?:보내기|전송)$")

    private fun normalize(label: String): String =
        label.replace('\u00A0', ' ').trim().replace(Regex("\\s+"), " ")

    fun matches(label: String): Boolean {
        val normalized = normalize(label)
        if (normalized in legacy) return true
        return counted.matchEntire(normalized)?.groupValues?.get(1) == "1"
    }

    /** 1명이 아닌 대상 수가 명시되어 있으면 자동 전송을 금지한다. */
    fun isOtherCount(label: String): Boolean {
        val count = counted.matchEntire(normalize(label))?.groupValues?.get(1)
        return count != null && count != "1"
    }
}
