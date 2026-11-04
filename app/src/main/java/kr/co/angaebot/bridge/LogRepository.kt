/*
 * 앙개봇 Android Bridge v0.2.0 — 전체 기능 설명
 * 카카오톡 신규 알림 수신/권한 검사/호출어 판별/중복 차단/명령 실행/빠른 답장 시도와
 * 각 단계의 예외를 SQLite에 기록한다. 관리 UI는 기록 전체 내보내기, 최근 기록 열람,
 * 명시적인 전체 삭제 및 통계를 제공한다. 아무 로그도 자동 삭제하지 않는다.
 * 이 파일은 SQLite 저장소 및 최근 알림 중복 방지의 영속화를 담당한다.
 * v0.2.0 확장: Python 연결은 별도 구성·인증 모듈에서만 처리하고 이 파일의 기존 기능과 로그는 유지한다.
 */
package kr.co.angaebot.bridge

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.io.OutputStream
import java.io.OutputStreamWriter

private const val DB_NAME = "angaebot_bridge_v01.db"

data class BotLog(
    val timestamp: Long,
    val level: String,
    val stage: String,
    val room: String,
    val sender: String,
    val detail: String
)

class LogRepository(context: Context) : SQLiteOpenHelper(context.applicationContext, DB_NAME, null, 1) {
    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL("""
            CREATE TABLE logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time INTEGER NOT NULL,
                level TEXT NOT NULL,
                stage TEXT NOT NULL,
                room TEXT NOT NULL,
                sender TEXT NOT NULL,
                detail TEXT NOT NULL
            )
        """.trimIndent())
        db.execSQL("CREATE INDEX idx_logs_time ON logs(event_time DESC)")
        db.execSQL("""
            CREATE TABLE seen (
                fingerprint TEXT PRIMARY KEY,
                first_seen INTEGER NOT NULL
            )
        """.trimIndent())
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        // v0.1에서는 스키마 변경 없음. 향후 로그 보존형 마이그레이션으로 확장한다.
    }

    @Synchronized
    fun log(level: String, stage: String, detail: String, room: String = "", sender: String = "") {
        val values = ContentValues().apply {
            put("event_time", System.currentTimeMillis())
            put("level", level)
            put("stage", stage)
            put("room", room)
            put("sender", sender)
            put("detail", detail)
        }
        writableDatabase.insertOrThrow("logs", null, values)
    }

    /** 2분 내의 동일 이벤트 재전달은 하나로 취급. 실제 동일 텍스트 재명령도 막힐 수 있다. */
    @Synchronized
    fun claim(fingerprint: String, now: Long = System.currentTimeMillis(), ttlMs: Long = 120_000): Boolean {
        val db = writableDatabase
        db.beginTransaction()
        try {
            db.rawQuery("SELECT first_seen FROM seen WHERE fingerprint=?", arrayOf(fingerprint)).use { cursor ->
                if (cursor.moveToFirst()) {
                    if (now - cursor.getLong(0) < ttlMs) {
                        db.setTransactionSuccessful()
                        return false
                    }
                }
            }
            val values = ContentValues().apply {
                put("fingerprint", fingerprint)
                put("first_seen", now)
            }
            db.insertWithOnConflict("seen", null, values, SQLiteDatabase.CONFLICT_REPLACE)
            db.setTransactionSuccessful()
            return true
        } finally {
            db.endTransaction()
        }
    }

    @Synchronized
    fun recent(limit: Int = 100): List<BotLog> {
        val data = ArrayList<BotLog>()
        readableDatabase.query(
            "logs", arrayOf("event_time", "level", "stage", "room", "sender", "detail"),
            null, null, null, null, "id DESC", limit.coerceIn(1, 1000).toString()
        ).use { c ->
            while (c.moveToNext()) {
                data.add(BotLog(c.getLong(0), c.getString(1), c.getString(2), c.getString(3), c.getString(4), c.getString(5)))
            }
        }
        return data
    }

    @Synchronized
    fun count(): Long = readableDatabase.rawQuery("SELECT COUNT(*) FROM logs", null).use { c ->
        if (c.moveToFirst()) c.getLong(0) else 0
    }

    /** 전체 로그를 UTF-8 OutputStream에 순차 기록: 대용량 로그에서도 메모리에 전부 쌓지 않는다. */
    @Synchronized
    fun writeText(output: OutputStream) {
        val formatter = SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.KOREA)
        OutputStreamWriter(output, Charsets.UTF_8).buffered().use { writer ->
            writer.write("앙개봇 Bridge v0.1 로그 전체 내보내기\n")
            readableDatabase.rawQuery("SELECT event_time, level, stage, room, sender, detail FROM logs ORDER BY id ASC", null).use { c ->
                while (c.moveToNext()) {
                    writer.write(formatter.format(Date(c.getLong(0))))
                    writer.write(" [${c.getString(1)}] [${c.getString(2)}]")
                    writer.write(" room=${c.getString(3)} sender=${c.getString(4)}")
                    writer.write(" detail=${c.getString(5).replace("\n", "\\n")}\n")
                }
            }
        }
    }

    @Synchronized
    fun clearAll() {
        writableDatabase.delete("logs", null, null)
        writableDatabase.delete("seen", null, null)
    }
}
