/*
 * 앙개봇 이미지 회신 테스트 전용 ContentProvider — 전체 기능과 보안 안내
 * 1. Android Bridge가 자체 생성한 PNG/JPEG 테스트 이미지만 카카오톡의 이미지 RemoteInput에 전달한다.
 * 2. 기존 외부 저장소 권한·DB/환경설정/개인 사진·파일과 네트워크는 절대 접근하지 않는다.
 * 3. 허용된 고정 파일 이름과 읽기 모드만 받고, 임의 경로 탐색·쓰기·목록 조회를 거부한다.
 * 4. 실제 파일은 앱 전용 cacheDir의 image-reply에 저장되며 이미지 입력이 명시된 알림에서만 읽기 권한을 준다.
 * 5. 기존 텍스트 RemoteInput/허용목록/중복방지/배터리/SQLite 로그는 그대로 유지한다.
 * 6. MediaSender A/B 실험용으로 고정 2종 PNG만 추가하며 기존 파일명·외부 저장소 차단·읽기 전용 권한은 유지한다.
 * 7. 새 PNG는 파일 자체에 A/B 표식을 넣어 직접 ID 인텐트와 무-ID 대조 실험의 수신 여부를 구별한다.
 * 8. v0.4.25는 오직 앱이 발급한 20자리 16진수 랜덤 PNG만 신규 경로로 허용해 파일명 재사용/흰색 미리보기 충돌을 방지한다.
 * 9. 기존 읽기 전용/앱 비공개 캐시/외부 파일·경로 탐색 금지/Android 설정 및 모든 이미지 로그를 유지한다.
 * 10. v0.4.25에서 카카오톡이 미리보기 생성 시 요청하는 OpenableColumns DISPLAY_NAME/SIZE를 실제 파일 기준으로 조회한다.
 * 11. URI 스키마/파일명 화이트리스트·파일 존재 여부 검사를 공유하고 기존 쓰기/외부 파일 접근 차단을 보존한다.
 * 12. v0.4.26은 S20+ 앱이 발급한 난수 이름의 MP4 파일만 추가하고 MIME video/mp4·파일 크기를 제공한다.
 * 13. 이미지와 영상 모두 앱 캐시의 읽기 전용 파일만 제공하며 외부 URI·쓰기·임의 경로·기존 로그는 유지한다.
 */
package kr.co.angaebot.bridge

import android.content.ContentProvider
import android.content.ContentValues
import android.database.Cursor
import android.database.MatrixCursor
import android.provider.OpenableColumns
import android.net.Uri
import android.os.ParcelFileDescriptor
import java.io.File
import java.io.FileNotFoundException

class ImageReplyProvider : ContentProvider() {
    override fun onCreate(): Boolean = true

    override fun getType(uri: Uri): String? {
        val name = uri.pathSegments.singleOrNull() ?: return null
        return when {
            name == "angaebot-test.jpg" -> "image/jpeg"
            DirectMp4Policy.allowedFileName(name) -> "video/mp4"
            name in setOf("angaebot-test.png", "angaebot-direct-a.png", "angaebot-direct-b.png") ||
                isUniqueProductionPng(name) -> "image/png"
            else -> null
        }
    }

    private fun isUniqueProductionPng(name: String): Boolean =
        name.matches(Regex("angaebot-prod-[0-9a-f]{20}\\.png"))

    private fun allowedFile(uri: Uri): File? {
        val name=uri.pathSegments.singleOrNull() ?: return null
        if(getType(uri)==null) return null
        val base=context?.cacheDir ?: return null
        val file=File(File(base,"image-reply"),name)
        return file.takeIf { it.isFile &&
            (getType(uri) != "video/mp4" || it.length() in 48L..DirectMp4Policy.MAX_BYTES) }
    }

    override fun openFile(uri: Uri, mode: String): ParcelFileDescriptor {
        if (mode != "r") throw FileNotFoundException("read-only media provider")
        val filename = uri.pathSegments.singleOrNull()
        if (filename !in setOf("angaebot-test.png", "angaebot-test.jpg",
                "angaebot-direct-a.png", "angaebot-direct-b.png") &&
            (filename == null ||
                (!isUniqueProductionPng(filename) && !DirectMp4Policy.allowedFileName(filename)))) {
            throw FileNotFoundException("unknown image")
        }
        val base = context?.cacheDir ?: throw FileNotFoundException("context unavailable")
        val image = File(File(base, "image-reply"), filename!!)
        if (!image.isFile) throw FileNotFoundException("media not prepared")
        return ParcelFileDescriptor.open(image, ParcelFileDescriptor.MODE_READ_ONLY)
    }

    override fun query(uri: Uri, projection: Array<out String>?, selection: String?,
                       selectionArgs: Array<out String>?, sortOrder: String?): Cursor? {
        val file=allowedFile(uri) ?: return null
        val cols=(projection?.toList() ?: listOf(
            OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE)).toTypedArray()
        val values=cols.map { col ->
            when(col) {
                OpenableColumns.DISPLAY_NAME -> file.name
                OpenableColumns.SIZE -> file.length()
                else -> null
            }
        }.toTypedArray()
        return MatrixCursor(cols).apply { addRow(values) }
    }

    override fun insert(uri: Uri, values: ContentValues?): Uri? =
        throw UnsupportedOperationException("read-only image provider")

    override fun update(uri: Uri, values: ContentValues?, selection: String?,
                        selectionArgs: Array<out String>?): Int =
        throw UnsupportedOperationException("read-only image provider")

    override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int =
        throw UnsupportedOperationException("read-only image provider")
}
