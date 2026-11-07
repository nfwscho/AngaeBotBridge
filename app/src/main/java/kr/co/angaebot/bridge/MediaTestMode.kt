/*
 * AngaeBot MediaSender-style media experiments — complete feature and safety summary
 * 1. Existing image automatic-test mode remains unchanged and is the default PNG share.
 * 2. Accept exact opt-in "미디어 시험 사진/JPG/동영상/PDF/2장" commands only.
 * 3. Send one PNG, one JPEG, a built-in tiny H.264 MP4, one generated PDF, or PNG+JPEG.
 * 4. Keep every sample in private app cache and allow only fixed, audited ContentProvider paths.
 * 5. Two-file mode uses ACTION_SEND_MULTIPLE, one-file mode uses ACTION_SEND.
 * 6. Exact allowed room, sender, click count, settings, lock and Accessibility policy all remain mandatory.
 * 7. Channel identifiers inferred from notification metadata are unverified hints, never send destinations.
 * 8. No file picker, arbitrary external URL, user media, credential bypass, or new permissions.
 * 9. Existing text RemoteInput, Python commands, stocks, todos, data, logs and UI remain preserved.
 */
package kr.co.angaebot.bridge

internal enum class MediaTestMode(val displayName: String, val mimeType: String) {
    PNG("PNG 사진", "image/png"),
    JPEG("JPG 사진", "image/jpeg"),
    VIDEO("MP4 동영상", "video/mp4"),
    PDF("PDF 문서", "application/pdf"),
    TWO_IMAGES("사진 2장", "image/*");

    companion object {
        fun parse(rawArgument: String): MediaTestMode? {
            val phrase = rawArgument.trim().replace(Regex("\\s+"), " ")
            return when (phrase) {
                "시험 사진", "시험 PNG", "시험 이미지" -> PNG
                "시험 JPG", "시험 JPEG" -> JPEG
                "시험 동영상", "시험 MP4", "시험 비디오" -> VIDEO
                "시험 PDF", "시험 문서" -> PDF
                "시험 2장", "시험 두장", "시험 사진2장" -> TWO_IMAGES
                else -> null
            }
        }
        const val HELP = "📎 미디어 전송 시험\\n" +
            "앙개야 미디어 시험 사진 (PNG)\\n" +
            "앙개야 미디어 시험 JPG\\n" +
            "앙개야 미디어 시험 동영상 (MP4)\\n" +
            "앙개야 미디어 시험 PDF\\n" +
            "앙개야 미디어 시험 2장\\n" +
            "앙개야 미디어 방정보 (ID 후보 확인만)\\n" +
            "※ 기존 이미지 자동전송 ON·접근성 연결 필요. PIN 인증 잠금은 우회하지 않습니다."
    }
}

/** Only fixed file names may ever leave the private ContentProvider. */
internal object MediaSamplePolicy {
    val allowedMime = mapOf(
        "angaebot-test.png" to "image/png",
        "angaebot-test.jpg" to "image/jpeg",
        "angaebot-test.pdf" to "application/pdf",
        "angaebot-video-test.mp4" to "video/mp4"
    )
    fun mimeFor(fileName: String): String? =
        if ('/' in fileName || '\\' in fileName || fileName == "." || fileName == "..") null
        else allowedMime[fileName]

    /** No notification tag is authoritative; numeric value is displayed only as an unverified hint. */
    fun candidateId(tag: String?): String? {
        val value = tag?.trim() ?: return null
        return value.takeIf { it.length in 9..20 && it.all(Char::isDigit) &&
            it.first() != '0' }
    }
}
