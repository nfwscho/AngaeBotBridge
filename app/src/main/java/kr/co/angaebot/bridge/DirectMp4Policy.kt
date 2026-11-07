/*
 * 앙개봇 S20+ 카카오톡 MP4 직접전송 순수 검증 정책 — 전체 기능 상세 주석
 * 1. MP4 파일의 ISO BMFF ftyp/moov/mdat 상위 박스 구조와 길이를 검사하여 비영상/깨진 파일을 차단한다.
 * 2. ftyp에는 isom/mp4/iso 브랜드 중 하나를 요구하고, 검증 실패한 파일은 전송에 사용하지 않는다.
 * 3. 최대 50MiB MP4만 허용하며 영상 시간/트랙 정보는 Android MediaMetadataRetriever로 추가 확인한다.
 * 4. 전송 파일명은 UUID에서 파생한 20자리 소문자 16진수 mp4만 허용해 임의 URI·경로 탐색을 차단한다.
 * 5. 기존 PNG provider 파일명, 이미지 RemoteInput, 잠금/허용 목록/SQLite 로그/주식 API는 변경하지 않는다.
 * 6. 최종 사용자 승인 1:1 방과 현재 알림 tag 확인은 기존 DirectPngPolicy의 정확 비교 정책을 재사용한다.
 * 7. 외부 URL/임의 SD 경로/클립보드를 읽지 않으며 선택 파일은 Android SAF 사용자의 명시적인 선택만 허용한다.
 * 8. 이 정책은 코덱 디코딩 검증이나 카카오톡 서버 전송 확인을 보장하지 않으므로 '전송 요청'으로만 기록한다.
 */
package kr.co.angaebot.bridge

import java.io.File
import java.io.RandomAccessFile

internal object DirectMp4Policy {
    const val MAX_BYTES = 50L * 1024L * 1024L
    const val MAX_DURATION_MS = 180_000L
    private val idName = Regex("angaebot-video-[0-9a-f]{20}\\.mp4")

    fun allowedFileName(name: String): Boolean = idName.matches(name)
    fun acceptedDuration(durationMs: Long, width: Int, height: Int): Boolean =
        durationMs in 1L..MAX_DURATION_MS && width in 160..3840 && height in 90..2160

    fun valid(file: File): Boolean {
        if (!file.isFile || file.length() !in 48L..MAX_BYTES) return false
        return try {
            RandomAccessFile(file, "r").use { input ->
                val end = input.length()
                var offset = 0L
                var seenFtyp = false
                var seenMoov = false
                var seenMdat = false
                var boxes = 0
                while (offset < end) {
                    if (++boxes > 1000 || end - offset < 8) return false
                    input.seek(offset)
                    val len32 = input.readInt().toLong() and 0xffffffffL
                    val typeBytes = ByteArray(4)
                    input.readFully(typeBytes)
                    val type = String(typeBytes, Charsets.US_ASCII)
                    var header = 8L
                    val size = when (len32) {
                        0L -> end - offset
                        1L -> {
                            if (end - offset < 16) return false
                            header = 16L
                            input.readLong()
                        }
                        else -> len32
                    }
                    if (size < header || size > end - offset) return false
                    if (boxes == 1 && type != "ftyp") return false
                    if (type == "ftyp") {
                        if (boxes != 1 || size < header + 8) return false
                        val brands = ByteArray(minOf((size - header).toInt(), 100))
                        input.readFully(brands)
                        val text = String(brands, Charsets.US_ASCII)
                        if (!listOf("isom", "iso2", "mp41", "mp42", "avc1", "M4V ").any(text::contains)) return false
                        seenFtyp = true
                    }
                    if (type == "moov") seenMoov = true
                    if (type == "mdat" && size > header) seenMdat = true
                    offset += size
                }
                offset == end && seenFtyp && seenMoov && seenMdat
            }
        } catch (_: Exception) {
            false
        }
    }
}
