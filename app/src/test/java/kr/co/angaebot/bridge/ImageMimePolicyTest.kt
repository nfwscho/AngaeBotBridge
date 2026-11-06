/*
 * 앙개봇 이미지 첨부 MIME 정책 회귀 테스트 — 전체 검사 항목
 * 1. 카카오톡 알림의 이미지 MIME 표시가 없을 때 기존 텍스트 답장을 안전하게 유지하도록 검증한다.
 * 2. PNG/JPEG/범용 범용 이미지 와일드카드 지원을 정확히 구분하고 PNG 우선순위를 검증한다.
 * 3. 텍스트나 다른 미디어 입력만 제시한 알림에 사진을 억지로 첨부하지 않는지 검증한다.
 * 4. Android 실기기 카카오톡 수신 확인과 무관한 단위 테스트이며 다른 기존 테스트를 변경하지 않는다.
 */
package kr.co.angaebot.bridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ImageMimePolicyTest {
    @Test fun missingInputsDoNotAdvertiseImageReply() {
        assertNull(ImageMimePolicy.selectMime(null))
        assertNull(ImageMimePolicy.selectMime(emptySet()))
        assertNull(ImageMimePolicy.selectMime(setOf("text/plain", "video/mp4")))
    }

    @Test fun pngAndWildcardAreAccepted() {
        assertEquals("image/png", ImageMimePolicy.selectMime(setOf("image/png")))
        assertEquals("image/png", ImageMimePolicy.selectMime(setOf("image/*")))
        assertEquals("image/png", ImageMimePolicy.selectMime(setOf("image/jpeg", "image/png")))
    }

    @Test fun jpegOnlyUsesJpeg() {
        assertEquals("image/jpeg", ImageMimePolicy.selectMime(setOf("image/jpeg")))
        assertEquals("image/jpeg", ImageMimePolicy.selectMime(setOf("image/jpg")))
    }
}
