/*
 * 앙개봇 이미지 MIME 선택 규칙 — 기능과 호환성 안내
 * 1. 알림 RemoteInput이 선언한 MIME 타입만 검사하여 카카오톡이 허용하지 않는 이미지 전송을 시도하지 않는다.
 * 2. PNG를 우선하고 JPEG를 보조로 선택한다. image/* 포괄 지원도 인정한다.
 * 3. 입력 목록이 비어 있거나 이미지와 무관하면 null을 반환해 기존 텍스트 빠른답장으로 안전하게 안내한다.
 * 4. 저장소/설정/SQLite/네트워크를 접근하지 않는 순수 함수라 기존 Android와 Python 기능에 영향을 주지 않는다.
 * 5. 이 정책은 알림이 이미지 데이터를 허용하는지의 검사일 뿐 카카오톡 최종 수신을 보장하지 않는다.
 */
package kr.co.angaebot.bridge

object ImageMimePolicy {
    fun selectMime(allowedDataTypes: Set<String>?): String? {
        if (allowedDataTypes.isNullOrEmpty()) return null
        return when {
            "image/png" in allowedDataTypes || "image/*" in allowedDataTypes -> "image/png"
            "image/jpeg" in allowedDataTypes || "image/jpg" in allowedDataTypes -> "image/jpeg"
            else -> null
        }
    }
}
