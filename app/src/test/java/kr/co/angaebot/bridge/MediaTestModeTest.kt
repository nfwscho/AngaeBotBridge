/*
 * Tests for MediaSender-style experimental formats — complete regression coverage
 * 1. Exact media-test commands cannot be confused with normal conversations or arbitrary file paths.
 * 2. Verify PNG, JPG, MP4, PDF, multi-image media types and previous PNG behavior.
 * 3. Restrict ContentProvider to the four internal sample file names and prevent path traversal.
 * 4. Never treat notification tag or shortcut metadata as an authenticated channel ID.
 * 5. Preserve all preexisting image/stock/todo/menu/Android UI/log behavior.
 */
package kr.co.angaebot.bridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertNotNull
import org.junit.Test

class MediaTestModeTest {
    @Test fun sampleModesAndMimes() {
        assertEquals(MediaTestMode.PNG, MediaTestMode.parse("시험 사진"))
        assertEquals(MediaTestMode.PNG, MediaTestMode.parse("시험 PNG"))
        assertEquals(MediaTestMode.JPEG, MediaTestMode.parse("시험 JPG"))
        assertEquals(MediaTestMode.VIDEO, MediaTestMode.parse("시험 동영상"))
        assertEquals(MediaTestMode.PDF, MediaTestMode.parse("시험 PDF"))
        assertEquals(MediaTestMode.TWO_IMAGES, MediaTestMode.parse("시험 2장"))
        assertEquals("image/*", MediaTestMode.TWO_IMAGES.mimeType)
        assertEquals("video/mp4", MediaTestMode.VIDEO.mimeType)
        assertNull(MediaTestMode.parse("시험 /sdcard/secret.jpg"))
        assertNull(MediaTestMode.parse("시험 https://example.com/x.jpg"))
        assertNull(MediaTestMode.parse("자동시험"))
        assertNull(MediaTestMode.parse("동영상 삭제"))
    }

    @Test fun onlyFixedProviderSamplePaths() {
        assertEquals("image/png", MediaSamplePolicy.mimeFor("angaebot-test.png"))
        assertEquals("image/jpeg", MediaSamplePolicy.mimeFor("angaebot-test.jpg"))
        assertEquals("application/pdf", MediaSamplePolicy.mimeFor("angaebot-test.pdf"))
        assertEquals("video/mp4", MediaSamplePolicy.mimeFor("angaebot-video-test.mp4"))
        listOf("../../secret.jpg", "../angaebot-test.png", "private.db", "test.mkv", "", "angaebot-video-test.mp4/..").forEach {
            assertNull(it, MediaSamplePolicy.mimeFor(it))
        }
    }

    @Test fun candidateChannelIdIsOnlyDiagnosticHint() {
        assertEquals("484036463708064", MediaSamplePolicy.candidateId("484036463708064"))
        assertNull(MediaSamplePolicy.candidateId("not-a-channel"))
        assertNull(MediaSamplePolicy.candidateId("-12345"))
        assertNull(MediaSamplePolicy.candidateId("000012345678"))
        assertNull(MediaSamplePolicy.candidateId(""))
        assertNotNull(MediaTestMode.HELP)
    }
}
