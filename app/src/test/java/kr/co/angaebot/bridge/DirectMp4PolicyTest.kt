/*
 * 앙개봇 MP4 카카오톡 직접 공유 안전 정책 전체 회귀 테스트
 * 1. 실제 MP4 상위 ftyp/moov/mdat 박스 및 브랜드 검사, 파일 길이·용량 정책을 검증한다.
 * 2. 헤더 누락/잘못된 박스 길이/FTYP 미지원/영상 데이터 누락/손상 MP4를 거부한다.
 * 3. 영상 3분/50MiB와 기본 해상도 정책을 검사하고, 임의 파일명·경로 탐색을 거부한다.
 * 4. 기존 Android 이미지 전송·SQLite/로그/파이썬 차트/UI/허용목록에 접근하지 않는다.
 * 5. 실기기 MediaMetadataRetriever와 KakaoTalk 영상 수신 여부는 S20+에서 별도로 확인한다.
 */
package kr.co.angaebot.bridge

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.io.File
import java.io.RandomAccessFile
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class DirectMp4PolicyTest {
    private fun box(type: String, data: ByteArray): ByteArray {
        val out=ByteArrayOutputStream()
        DataOutputStream(out).use { stream ->
            stream.writeInt(8+data.size)
            stream.write(type.toByteArray(Charsets.US_ASCII))
            stream.write(data)
        }
        return out.toByteArray()
    }
    private fun mp4(brands: String="isomiso2avc1", withVideo: Boolean=true): ByteArray {
        val ftyp=box("ftyp",brands.toByteArray(Charsets.US_ASCII))
        val moov=box("moov",ByteArray(24){1})
        val mdat=if(withVideo) box("mdat",ByteArray(48){7}) else byteArrayOf()
        return ftyp+moov+mdat
    }
    private fun assertFileValid(bytes: ByteArray, expected: Boolean) {
        val file=File.createTempFile("angaebot-mp4-junit-",".mp4")
        try {
            file.writeBytes(bytes)
            if(expected) assertTrue(DirectMp4Policy.valid(file))
            else assertFalse(DirectMp4Policy.valid(file))
        } finally { file.delete() }
    }

    @Test fun validMp4ContainerRequiresFtypMoovAndMdat() {
        assertFileValid(mp4(),true)
        assertFileValid(mp4(withVideo=false),false)
        assertFileValid(mp4(brands="XXXXYYYY"),false)
        assertFileValid(mp4().copyOfRange(0,21),false)
        assertFileValid(box("moov",ByteArray(24))+box("mdat",ByteArray(48)),false)
    }

    @Test fun rejectsLengthTamperingAndMissingData() {
        val good=mp4()
        val corrupted=good.clone()
        corrupted[0]=0x7f.toByte()
        assertFileValid(corrupted,false)
        val badSize=good.clone()
        badSize[0]=0
        badSize[1]=0
        badSize[2]=0
        badSize[3]=1 // Invalid extended length (uses subsequent "isom")
        assertFileValid(badSize,false)
        assertFileValid(byteArrayOf(),false)
        val huge=File.createTempFile("angaebot-mp4-huge-",".mp4")
        try {
            RandomAccessFile(huge,"rw").use { it.setLength(DirectMp4Policy.MAX_BYTES+1) }
            assertFalse(DirectMp4Policy.valid(huge))
        } finally { huge.delete() }
    }

    @Test fun onlyGeneratedNamesAndDurationBoundsAreAccepted() {
        assertTrue(DirectMp4Policy.allowedFileName("angaebot-video-0123456789abcdef1234.mp4"))
        for (s in listOf("movie.mp4","../movie.mp4","angaebot-video-00.mp4",
                "angaebot-video-0123456789abcdef1234.MP4",
                "angaebot-prod-0123456789abcdef1234.png","angaebot-video-1234/abc.mp4")) {
            assertFalse(DirectMp4Policy.allowedFileName(s))
        }
        assertTrue(DirectMp4Policy.acceptedDuration(2500L,320,180))
        assertTrue(DirectMp4Policy.acceptedDuration(180000L,3840,2160))
        assertFalse(DirectMp4Policy.acceptedDuration(180001L,320,180))
        assertFalse(DirectMp4Policy.acceptedDuration(0L,320,180))
        assertFalse(DirectMp4Policy.acceptedDuration(2000L,100,180))
        assertFalse(DirectMp4Policy.acceptedDuration(2000L,320,4000))
    }
}
