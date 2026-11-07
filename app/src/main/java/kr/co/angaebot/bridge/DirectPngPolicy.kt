/*
 * 앙개봇 직접 PNG 전송 인증/페어링 정책 — 전체 기능과 원래 코드 보호
 * 1. MediaSender A/B 실험에서 검증한 1:1 room=sender + 숫자 알림 tag를 정확히 한 쌍으로 묶는다.
 * 2. 실제 pairing 저장은 S20+ 앱 관리 화면의 물리적인 승인 버튼에서만 가능하다.
 * 3. 카카오톡의 '직공유진단'은 후보만 RAM에 5분 보관하며 원격 명령 자체로 승인하지 않는다.
 * 4. 등록된 room/sender/후보 tag 모두 정확하게 같아야 직접 PNG 전송을 허용한다.
 * 5. 기존 BotConfig 허용 목록, 독립 direct PNG 스위치, 이미지 스위치 및 잠금 제한을 추가로 요구한다.
 * 6. 새로운 direct PNG 스위치는 기본 OFF, 등록 대상은 단일 1:1 채팅방만 허용한다.
 * 7. PIN 인증·패턴·비밀번호 자동 해제는 어떤 경우에도 허용하지 않는다.
 * 8. 로그에는 태그의 자릿수/끝 네 자리만 기록하며 전체 식별자는 공개하지 않는다.
 * 9. PNG는 서명/IHDR/컬러타입/크기·파일 용량 및 PNG 청크 CRC를 엄격히 검증한다.
 * 10. 기존 접근성 직접시험/주식/메모/날씨/Python/SQLite/Android 설정은 수정하지 않는다.
 */
package kr.co.angaebot.bridge

internal data class DirectPngBinding(val room: String, val sender: String, val tag: Long)

internal object DirectPngPolicy {
    fun authorized(binding: DirectPngBinding?, room: String, sender: String, tag: String?): Boolean {
        if (binding == null || room.isBlank() || room != sender ||
            room != binding.room || sender != binding.sender) return false
        val candidate = MediaDirectPolicy.candidate(tag, room, sender)
        return candidate != null && binding.tag == candidate
    }

    fun masked(binding: DirectPngBinding?): String = binding?.let {
        it.room + " / " + it.sender + " / " + MediaDirectPolicy.mask(it.tag)
    } ?: "연결된 1:1 채팅방 없음"
}

/** 메모리 임시 진단 → 5분 안에 S20+ 화면에서 실제 누른 경우에만 binding을 허용한다. */
internal object DirectPngPairing {
    private data class Pending(val pairing: DirectPngBinding, val since: Long)
    private var pending: Pending? = null
    private const val VALIDITY_MS=300_000L

    @Synchronized fun stage(tag: String?, room: String, sender: String, nowMs: Long): Boolean {
        val candidate = MediaDirectPolicy.candidate(tag, room, sender)
        pending = if(candidate != null) Pending(DirectPngBinding(room, sender, candidate), nowMs) else null
        return candidate != null
    }
    @Synchronized fun preview(nowMs: Long): DirectPngBinding? {
        val p=pending ?: return null
        return p.pairing.takeIf { nowMs >= p.since && nowMs-p.since<=VALIDITY_MS }
    }
    @Synchronized fun consume(nowMs: Long): DirectPngBinding? {
        val found=preview(nowMs)
        pending=null
        return found
    }
}

/** 순수 PNG 검사: 외부 파일·임의 URL·비정상 이미지의 대화방 전송을 차단한다. */
internal object DirectPngBytes {
    const val MAX_BYTES = 1_200_000
    private val signature = byteArrayOf(137.toByte(),80,78,71,13,10,26,10)
    private val ihdr=byteArrayOf(73,72,68,82)
    private val idat=byteArrayOf(73,68,65,84)
    private val iend=byteArrayOf(73,69,78,68)

    fun valid(content: ByteArray): Boolean {
        if (content.size !in 57..MAX_BYTES || !content.copyOfRange(0,8).contentEquals(signature)) return false
        if (uint(content,8)!=13L || !content.copyOfRange(12,16).contentEquals(ihdr)) return false
        val width=uint(content,16)
        val height=uint(content,20)
        if(width !in 320L..1600L || height !in 180L..1200L) return false
        if((content[24].toInt() and 255)!=8 || (content[25].toInt() and 255) !in listOf(2,6)) return false
        if((content[26].toInt() and 255)!=0 || (content[27].toInt() and 255)!=0 ||
           (content[28].toInt() and 255)!=0) return false

        var index=8
        var chunks=0
        var imageData=false
        while(index+12<=content.size) {
            val length=uint(content,index)
            if(length>MAX_BYTES || length>content.size-index-12) return false
            val next=index+12+length.toInt()
            val type=content.copyOfRange(index+4,index+8)
            if(chunks==0 && (!type.contentEquals(ihdr) || length!=13L)) return false
            val crc=java.util.zip.CRC32()
            crc.update(content,index+4,4+length.toInt())
            if(crc.value != uint(content,next-4)) return false
            if(type.contentEquals(idat)) {
                if(length<1L) return false
                imageData=true
            }
            if(type.contentEquals(iend)) return imageData && length==0L && next==content.size
            index=next
            chunks++
            if(chunks>100) return false
        }
        return false
    }
    private fun uint(b:ByteArray,offset:Int):Long =
        ((b[offset].toLong() and 255L) shl 24) or
        ((b[offset+1].toLong() and 255L) shl 16) or
        ((b[offset+2].toLong() and 255L) shl 8) or
        (b[offset+3].toLong() and 255L)
}
