/*
 * 앙개봇 별도 PNG 직접전송 엔진 전체 회귀 테스트
 * 1. 방/발신자/태그가 동일한 검증 1:1 연결만 승인, 단체방/타인/태그 변경은 거부한다.
 * 2. S20+ 물리 승인 이전 단계인 진단 후보는 5분이 지나거나 사용되면 폐기된다.
 * 3. 승인된 후보는 카카오톡 명령으로 직접 등록할 수 없고 S20+ 앱 버튼이 있어야 한다.
 * 4. 외부 라이브러리 없는 실제 zlib RGB PNG를 구성해 PNG 서명·IHDR·IDAT·IEND CRC를 확인한다.
 * 5. 이미지 크기·파일 용량·CRC 변조를 거부해 가짜 PNG가 카카오톡에 공유되지 않도록 한다.
 * 6. 기존 Android 이미지/텍스트/로그/UI/Python/SQLite 자료를 변경하지 않는 순수 Kotlin 테스트다.
 */
package kr.co.angaebot.bridge

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.util.zip.CRC32
import java.util.zip.DeflaterOutputStream
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class DirectPngPolicyTest {
    private val id = "484036463708064"
    private val owner = DirectPngBinding("조우상 폰주인","조우상 폰주인",484036463708064L)

    @Test fun pairingIsStrictlyOneToOne() {
        assertTrue(DirectPngPolicy.authorized(owner,owner.room,owner.sender,id))
        assertFalse(DirectPngPolicy.authorized(null,owner.room,owner.sender,id))
        assertFalse(DirectPngPolicy.authorized(owner,"단톡방",owner.sender,id))
        assertFalse(DirectPngPolicy.authorized(owner,owner.room,"다른사람",id))
        assertFalse(DirectPngPolicy.authorized(owner,owner.room,owner.sender,"484036463708065"))
        assertFalse(DirectPngPolicy.authorized(owner,owner.room,owner.sender,"invalid"))
        assertTrue(DirectPngPolicy.masked(owner).contains("끝 8064"))
        assertFalse(DirectPngPolicy.masked(owner).contains(id))
    }
    @Test fun pendingRequiresFreshPhysicalApproval() {
        assertTrue(DirectPngPairing.stage(id,owner.room,owner.sender,1000L))
        assertEquals(owner, DirectPngPairing.preview(1001L))
        assertNull(DirectPngPairing.preview(301001L))
        assertNull(DirectPngPairing.consume(301001L))
        assertFalse(DirectPngPairing.stage("invalid",owner.room,owner.sender,400000L))
        assertNull(DirectPngPairing.consume(400001L))
        assertTrue(DirectPngPairing.stage(id,owner.room,owner.sender,500000L))
        assertEquals(owner, DirectPngPairing.consume(500001L))
        assertNull(DirectPngPairing.consume(500002L))
        assertFalse(DirectPngPairing.stage(id,"단체방","다른사람",600000L))
    }

    private fun testPng(): ByteArray {
        val raw=ByteArray(180*(1+320*3))
        val compressed=ByteArrayOutputStream()
        DeflaterOutputStream(compressed).use { it.write(raw) }
        val signature=byteArrayOf(137.toByte(),80,78,71,13,10,26,10)
        val output=ByteArrayOutputStream()
        output.write(signature)
        fun chunk(type:String, bytes:ByteArray) {
            val data=type.toByteArray(Charsets.US_ASCII)
            DataOutputStream(output).writeInt(bytes.size)
            output.write(data)
            output.write(bytes)
            val crc=CRC32()
            crc.update(data)
            crc.update(bytes)
            DataOutputStream(output).writeInt(crc.value.toInt())
        }
        val head=ByteArrayOutputStream()
        DataOutputStream(head).apply {
            writeInt(320);writeInt(180);writeByte(8);writeByte(2);writeByte(0);writeByte(0);writeByte(0)
        }
        chunk("IHDR",head.toByteArray())
        chunk("IDAT",compressed.toByteArray())
        chunk("IEND",byteArrayOf())
        return output.toByteArray()
    }
    @Test fun onlyValidBoundedPngBytesAreAccepted() {
        val png=testPng()
        assertTrue(DirectPngBytes.valid(png))
        val tampered=png.copyOf()
        tampered[20]=0
        tampered[21]=0
        tampered[22]=0
        tampered[23]=0
        assertFalse(DirectPngBytes.valid(tampered))
        val corrupt=png.copyOf()
        corrupt[corrupt.size-20]=(corrupt[corrupt.size-20].toInt() xor 0x2).toByte()
        assertFalse(DirectPngBytes.valid(corrupt))
        assertFalse(DirectPngBytes.valid(byteArrayOf()))
        assertFalse(DirectPngBytes.valid(ByteArray(DirectPngBytes.MAX_BYTES+1)))
    }
}
