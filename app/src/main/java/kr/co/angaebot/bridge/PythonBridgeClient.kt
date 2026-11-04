/*
 * 앙개봇 Bridge v0.2.0 — 전체 기능/네트워크 연동 설명
 * 1) 기존 Kakao NotificationListenerService, RemoteInput 빠른 답장, 모든 SQLite 이벤트 로그를 유지한다.
 * 2) 기존 명령 '테스트/상태/도움말'을 Android 단독으로 처리하고 새 명령만 Python에 전달한다.
 * 3) S20+ 내부 loopback의 FastAPI 서버(127.0.0.1:8765)로만 접속한다.
 * 4) X-AngaeBot-Token 헤더로 인증하고, HTTP connect/read 타임아웃을 설정한다.
 * 5) 요청 ID를 전달해 Python 서버 SQLite에서 동일 명령 재실행을 방지한다.
 * 6) 네트워크/JSON/인증 실패는 명확한 예외로 전달하며 로그에는 인증키를 절대 쓰지 않는다.
 * 7) 외부 웹서버/IP 변경, 임의 셸/파일/PC 제어, 별도 카카오톡 발송은 지원하지 않는다.
 */
package kr.co.angaebot.bridge

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

sealed interface PythonOutcome {
    data class Success(val reply: String, val duplicate: Boolean, val commandOk: Boolean) : PythonOutcome
    data class Failure(val reason: String) : PythonOutcome
}

object PythonBridgeClient {
    private const val BASE = "http://127.0.0.1:8765"
    val supportedCommands = setOf("계산", "시간", "서버상태")

    fun health(token: String): PythonOutcome = request("GET", "/v1/health", token, null)

    fun execute(token: String, requestId: String, name: String, argument: String, room: String, sender: String): PythonOutcome {
        if (name !in supportedCommands) return PythonOutcome.Failure("지원하지 않는 Python 명령")
        val payload = JSONObject()
            .put("request_id", requestId)
            .put("command", name)
            .put("argument", argument.take(160))
            .put("room", room.take(100))
            .put("sender", sender.take(100))
        return request("POST", "/v1/commands", token, payload)
    }

    private fun request(method: String, path: String, token: String, payload: JSONObject?): PythonOutcome {
        if (token.length < 32) return PythonOutcome.Failure("Python 인증 토큰이 설정되지 않았습니다.")
        var connection: HttpURLConnection? = null
        try {
            connection = (URL(BASE + path).openConnection() as HttpURLConnection).apply {
                requestMethod = method
                connectTimeout = 2_000
                readTimeout = 4_000
                setRequestProperty("X-AngaeBot-Token", token)
                setRequestProperty("Accept", "application/json")
                if (payload != null) {
                    doOutput = true
                    setRequestProperty("Content-Type", "application/json; charset=utf-8")
                }
            }
            if (payload != null) {
                connection.outputStream.use { it.write(payload.toString().toByteArray(Charsets.UTF_8)) }
            }
            val status = connection.responseCode
            if (status !in 200..299) {
                return PythonOutcome.Failure(when (status) {
                    401 -> "Python 인증 실패: Android와 Termux의 토큰을 확인하세요."
                    409 -> "Python 요청 ID 충돌: 중복 요청 데이터를 확인하세요."
                    else -> "Python HTTP 오류: $status"
                })
            }
            val json = connection.inputStream.bufferedReader(Charsets.UTF_8).use { reader ->
                val result = reader.readText()
                if (result.length > 16_000) return PythonOutcome.Failure("Python 응답이 너무 깁니다.")
                JSONObject(result)
            }
            if (path == "/v1/health") {
                val version = json.optString("version", "unknown")
                return PythonOutcome.Success("🐍 Python 연결 정상 (v$version)", false, json.optBoolean("ok", false))
            }
            val reply = json.optString("reply", "")
            if (reply.isBlank()) return PythonOutcome.Failure("Python 응답에 내용이 없습니다.")
            return PythonOutcome.Success(reply.take(1800), json.optBoolean("duplicate", false), json.optBoolean("ok", false))
        } catch (e: java.net.ConnectException) {
            return PythonOutcome.Failure("Python 서버에 연결되지 않습니다. Termux 실행 상태를 확인하세요.")
        } catch (e: java.net.SocketTimeoutException) {
            return PythonOutcome.Failure("Python 서버 응답 시간 초과")
        } catch (e: Exception) {
            return PythonOutcome.Failure("Python 통신 오류: ${e.javaClass.simpleName}")
        } finally {
            connection?.disconnect()
        }
    }
}
