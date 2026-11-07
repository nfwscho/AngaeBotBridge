/*
 * 앙개봇 MP4 직접공유 파일 준비/검증 — 전체 기능 및 안전 규칙
 * 1. 앱 자체 제작한 2.5초 H.264 샘플 MP4를 assets에서 앱 비공개 캐시에 복사해 직접전송 시험을 지원한다.
 * 2. S20+ 사용자가 Android 시스템 파일 선택기(ACTION_OPEN_DOCUMENT)로 직접 선택한 MP4만 복사한다.
 * 3. 외부 저장소 권한/다운로드 URL/임의 경로는 사용하지 않고 content://만 읽어 앱 전용 캐시에 보관한다.
 * 4. 복사 데이터는 50MiB를 넘으면 즉시 중단하고 임시 파일을 삭제한다.
 * 5. ISO BMFF ftyp/moov/mdat, 영상 트랙, 길이 1~180초 및 영상 해상도를 추가 검증한다.
 * 6. mp4 MIME/읽기 권한은 기존 비공개 ContentProvider를 통해 카카오톡에만 전달한다.
 * 7. 파일명은 무작위 20자리 소문자 UUID/16진수로 생성해 같은 영상의 썸네일 캐시 충돌을 줄인다.
 * 8. 선택한 원본 MP4는 삭제·수정하지 않으며 원본/선택한 파일명은 원격 명령·로그에 공개하지 않는다.
 * 9. 기존 image-reply 파일·PNG 테스트/주식 차트·알림·전송 로그 및 SQLite 데이터는 변경하지 않는다.
 * 10. 검증이 실패하거나 앱 캐시 파일이 사라지면 가짜 동영상 없이 오류로 종료한다.
 */
package kr.co.angaebot.bridge

import android.content.Context
import android.media.MediaMetadataRetriever
import android.net.Uri
import java.io.File
import java.util.UUID

internal sealed interface Mp4ImportOutcome {
    data class Ready(val size: Long, val durationMs: Long) : Mp4ImportOutcome
    data class Failed(val reason: String) : Mp4ImportOutcome
}

internal object DirectMp4Files {
    private const val DIR = "image-reply"
    private const val TEST_ASSET = "angaebot-mp4-test.mp4"
    private val fileNamePattern = Regex("angaebot-video-[0-9a-f]{20}\\.mp4")

    private fun directory(context: Context): File =
        File(context.cacheDir, DIR).also {
            if (!it.isDirectory && !it.mkdirs()) throw IllegalStateException("MP4 캐시 폴더 생성 실패")
        }

    private fun newName() =
        "angaebot-video-" + UUID.randomUUID().toString().replace("-", "").take(20) + ".mp4"

    private fun privateUri(context: Context, filename: String): Uri {
        if (!DirectMp4Policy.allowedFileName(filename)) throw IllegalArgumentException("비허용 MP4 이름")
        return Uri.Builder().scheme("content")
            .authority(context.packageName + ".imageprovider")
            .appendPath(filename).build()
    }

    private fun cleanOld(context: Context) {
        val cutoff = System.currentTimeMillis() - 72L*60L*60L*1000L
        val selected = DirectMp4Config.selectedFileName(context)
        directory(context).listFiles()?.forEach { f ->
            if (f.isFile && f.name != selected && fileNamePattern.matches(f.name) &&
                f.lastModified() < cutoff) f.delete()
        }
    }

    private fun copyBounded(input: java.io.InputStream, target: File) {
        var total = 0L
        target.outputStream().use { out ->
            val buffer = ByteArray(32 * 1024)
            while (true) {
                val n = input.read(buffer)
                if (n < 0) break
                if (n == 0) continue
                total += n
                if (total > DirectMp4Policy.MAX_BYTES) {
                    throw IllegalArgumentException("50MiB보다 큰 동영상은 허용하지 않습니다.")
                }
                out.write(buffer, 0, n)
            }
        }
    }

    private fun validate(file: File): Long {
        if (!DirectMp4Policy.valid(file)) throw IllegalArgumentException("MP4 구조/크기 검증 실패")
        val retriever = MediaMetadataRetriever()
        try {
            retriever.setDataSource(file.absolutePath)
            val hasVideo = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_HAS_VIDEO)
            val duration = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLongOrNull()
                ?: throw IllegalArgumentException("동영상 길이 확인 불가")
            val width = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_WIDTH)?.toIntOrNull()
                ?: 0
            val height = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_HEIGHT)?.toIntOrNull()
                ?: 0
            if (hasVideo != "yes" || !DirectMp4Policy.acceptedDuration(duration, width, height)) {
                throw IllegalArgumentException("영상 트랙/길이/해상도 기준 미충족 (최대 180초)")
            }
            return duration
        } finally {
            retriever.release()
        }
    }

    /** 2.5초 H.264 원본 시험 영상. 직접 승인된 방에서만 보내고 정상 수신 여부는 별도 확인. */
    fun testUri(context: Context): Uri {
        cleanOld(context)
        val name=newName()
        val file=File(directory(context),name)
        try {
            context.assets.open(TEST_ASSET).use { input -> copyBounded(input, file) }
            validate(file)
            return privateUri(context,name)
        } catch (e: Exception) {
            file.delete()
            throw e
        }
    }

    /** 선택한 실제 MP4는 S20+ 사용자가 파일 선택 UI에서 직접 지정한 경우만 저장한다. */
    fun importSelected(context: Context, source: Uri): Mp4ImportOutcome {
        if (source.scheme != "content") return Mp4ImportOutcome.Failed("시스템 파일 선택기의 content URI만 허용합니다.")
        var file: File? = null
        return try {
            cleanOld(context)
            val name=newName()
            file=File(directory(context),name)
            val input=context.contentResolver.openInputStream(source)
                ?: throw IllegalArgumentException("선택한 파일을 읽을 수 없습니다.")
            input.use { copyBounded(it, file) }
            val duration=validate(file)
            val size=file.length()
            if (!DirectMp4Config.saveSelected(context,name,size,duration)) {
                throw IllegalStateException("MP4 설정 저장 실패")
            }
            Mp4ImportOutcome.Ready(size,duration)
        } catch (e: Exception) {
            file?.delete()
            Mp4ImportOutcome.Failed(e.message?.take(160) ?: e.javaClass.simpleName)
        }
    }

    fun selectedUri(context: Context): Uri {
        val name=DirectMp4Config.selectedFileName(context)
            ?: throw IllegalStateException("S20+에서 선택된 MP4 파일이 없습니다.")
        val file=File(directory(context),name)
        validate(file)
        return privateUri(context,name)
    }
}
