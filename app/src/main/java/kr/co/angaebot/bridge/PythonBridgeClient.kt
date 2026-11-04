/*
 * 앙개봇 Android Bridge v0.4.0 — 전체 기능/네트워크 안내
 * 1. v0.2 Python 연결/상태검사/토큰 인증/중복 request_id/JSON 처리 기능을 보존한다.
 * 2. 계산·시간·서버상태의 기존 타임아웃과 오류 처리·반환 형식을 유지한다.
 * 3. 질문·요약·AI상태·대화초기화 명령을 기존 FastAPI /v1/commands로 전달한다.
 * 4. AI 입력은 최대 1000자로 제한하고 비 AI 인수는 기존 160자 제한을 유지한다.
 * 5. AI 질문만 읽기 제한 시간을 25초로 늘려 응답을 기다리며 기존 명령은 4초로 유지한다.
 * 6. 기존 Android 내 127.0.0.1:8765 고정 접속, HTTP 상태별 오류, 로그인 키 비노출을 유지한다.
 * 7. Android에서 직접 OpenAI/Ollama에 접속하거나 AI 키/질문을 외부 저장소에 기록하지 않는다.
 * 8. v0.4.0: 상세상태·통계·최근오류·가동시간을 기존 로컬 인증 FastAPI로 전달한다.
 * 9. 기존 모든 요청/결과/오류 코드 및 로그 사용 방식을 보존하고 추가 명령만 허용한다.
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
    val supportedCommands = setOf("계산", "시간", "서버상태", "질문", "요약", "AI상태", "대화초기화", "상세상태", "통계", "최근오류", "가동시간")
    private val aiCommands = setOf("질문", "요약")

    fun health(token: String): PythonOutcome = request("GET", "/v1/health", token, null)

    fun execute(token: String, requestId: String, name: String, argument: String, room: String, sender: String): PythonOutcome {
        if (name !in supportedCommands) return PythonOutcome.Failure("지원하지 않는 Python 명령")
        val payload = JSONObject()
            .put("request_id", requestId)
            .put("command", name)
            .put("argument", argument.take(if (name in aiCommands) 1000 else 160))
            .put("room", room.take(100))
            .put("sender", sender.take(100))
        return request("POST", "/v1/commands", token, payload, name in aiCommands)
    }

    private fun request(method: String, path: String, token: String, payload: JSONObject?, isAi: Boolean = false): PythonOutcome {
        if (token.length < 32) return PythonOutcome.Failure("Python 인증 토큰이 설정되지 않았습니다.")
        var connection: HttpURLConnection? = null
        try {
            connection = (URL(BASE + path).openConnection() as HttpURLConnection).apply {
                requestMethod = method
                connectTimeout = 2_000
                readTimeout = if (isAi) 25_000 else 4_000
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
