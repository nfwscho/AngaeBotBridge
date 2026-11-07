/*
 * 앙개봇 이미지 회신 테스트 전용 ContentProvider — 전체 기능과 보안 안내
 * 1. Android Bridge가 자체 생성한 PNG/JPEG 테스트 이미지만 카카오톡의 이미지 RemoteInput에 전달한다.
 * 2. 기존 외부 저장소 권한·DB/환경설정/개인 사진·파일과 네트워크는 절대 접근하지 않는다.
 * 3. 허용된 고정 파일 이름과 읽기 모드만 받고, 임의 경로 탐색·쓰기·목록 조회를 거부한다.
 * 4. 실제 파일은 앱 전용 cacheDir의 image-reply에 저장되며 이미지 입력이 명시된 알림에서만 읽기 권한을 준다.
 * 5. 기존 텍스트 RemoteInput/허용목록/중복방지/배터리/SQLite 로그는 그대로 유지한다.
 * 6. MediaSender A/B 실험용으로 고정 2종 PNG만 추가하며 기존 파일명·외부 저장소 차단·읽기 전용 권한은 유지한다.
 * 7. 새 PNG는 파일 자체에 A/B 표식을 넣어 직접 ID 인텐트와 무-ID 대조 실험의 수신 여부를 구별한다.
 */
package kr.co.angaebot.bridge

import android.content.ContentProvider
import android.content.ContentValues
import android.database.Cursor
import android.net.Uri
import android.os.ParcelFileDescriptor
import java.io.File
import java.io.FileNotFoundException

class ImageReplyProvider : ContentProvider() {
    override fun onCreate(): Boolean = true

    override fun getType(uri: Uri): String? = when (uri.pathSegments.singleOrNull()) {
        "angaebot-test.png" -> "image/png"
        "angaebot-test.jpg" -> "image/jpeg"
        "angaebot-direct-a.png", "angaebot-direct-b.png" -> "image/png"
        else -> null
    }

    override fun openFile(uri: Uri, mode: String): ParcelFileDescriptor {
        if (mode != "r") throw FileNotFoundException("read-only image provider")
        val filename = uri.pathSegments.singleOrNull()
        if (filename !in setOf("angaebot-test.png", "angaebot-test.jpg",
                "angaebot-direct-a.png", "angaebot-direct-b.png")) {
            throw FileNotFoundException("unknown image")
        }
        val base = context?.cacheDir ?: throw FileNotFoundException("context unavailable")
        val image = File(File(base, "image-reply"), filename!!)
        if (!image.isFile) throw FileNotFoundException("image not prepared")
        return ParcelFileDescriptor.open(image, ParcelFileDescriptor.MODE_READ_ONLY)
    }

    override fun query(uri: Uri, projection: Array<out String>?, selection: String?,
                       selectionArgs: Array<out String>?, sortOrder: String?): Cursor? = null

    override fun insert(uri: Uri, values: ContentValues?): Uri? =
        throw UnsupportedOperationException("read-only image provider")

    override fun update(uri: Uri, values: ContentValues?, selection: String?,
                        selectionArgs: Array<out String>?): Int =
        throw UnsupportedOperationException("read-only image provider")

    override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?): Int =
        throw UnsupportedOperationException("read-only image provider")
}
