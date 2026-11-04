/*
 * 앙개봇 Android Bridge v0.1 — 전체 프로그램 기능 및 운영 원칙
 * 1. S20+의 보조 카카오톡(com.kakao.talk) 신규 알림만 NotificationListenerService로 수신한다.
 * 2. 기본 OFF이며, 승인된 정확한 채팅방명 + 발신자명 + '앙개야' 호출어가 모두 필요하다.
 * 3. '테스트', '상태', '도움말'을 S20+에서 직접 처리하고 RemoteInput으로 답장을 시도한다.
 * 4. 중복 알림 방지(SQLite), 모든 수신/거절/명령/응답/오류 영구 로그를 제공한다.
 * 5. 관리 UI: 권한 안내, ON/OFF, 호출어, 방/발신자 허용목록, 저장, 오프라인 테스트,
 *    최근 로그/전체 로그 수, TXT 전체 내보내기, 확인 후 로그 삭제, 연결 상태 표시.
 * 6. 비활성화 및 빈 허용목록으로 안전한 초기 상태를 보장하고, 인터넷/SMS 권한 불필요.
 * 7. 카카오톡 알림은 실제 계정/채팅방 고유 ID를 제공하지 않을 수 있어 표시 이름만으로
 *    강한 사용자 인증을 할 수 없다. 개인용 테스트만 허용하고 고위험 명령은 지원하지 않는다.
 * 8. 답장 액션 요청 성공은 상대방 카카오톡 도착 확인이 아니며, 알림 없이는 보낼 수 없다.
 * 9. v0.2.0: 기존 UI/4개 섹션/로그 내보내기/긴급 OFF/로컬 테스트 기능을 그대로 둔다.
 * 10. 새 ②-A Python 연결 섹션에서 인증 토큰을 암호화 저장하고 로컬 연결을 비동기 시험한다.
 * 11. Python 명령은 계산/시간/서버상태에 한정하며 연결 OFF여도 기존 3개 명령은 정상 동작한다.
 */
package kr.co.angaebot.bridge

import android.app.Activity
import android.app.AlertDialog
import android.content.ComponentName
import android.content.Intent
import android.graphics.Color
import android.graphics.Typeface
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.text.InputType
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.concurrent.thread

@Suppress("DEPRECATION")
class MainActivity : Activity() {
    private lateinit var config: BotConfig
    private lateinit var pythonConfig: PythonBridgeConfig
    private lateinit var pythonSwitch: Switch
    private lateinit var pythonTokenInput: EditText
    private lateinit var logs: LogRepository
    private lateinit var powerSwitch: Switch
    private lateinit var roomsInput: EditText
    private lateinit var sendersInput: EditText
    private lateinit var wakeInput: EditText
    private lateinit var statusText: TextView
    private lateinit var logsText: TextView
    private lateinit var testInput: EditText
    private val uiHandler = Handler(Looper.getMainLooper())
    private var visible = false
    private val refreshTask = object : Runnable {
        override fun run() {
            if (visible) {
                updateStatusAndLogs()
                uiHandler.postDelayed(this, 5_000)
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        config = BotConfig(this)
        pythonConfig = PythonBridgeConfig(this)
        logs = LogRepository(this)
        buildUi()
        loadSettings()
        updateStatusAndLogs()
    }

    private fun buildUi() {
        val scroll = ScrollView(this).apply { setFillViewport(true) }
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), dp(18), dp(18), dp(30))
            setBackgroundColor(Color.rgb(245, 248, 251))
        }
        scroll.addView(root)
        setContentView(scroll)

        root.addView(label("🤖 앙개봇 Bridge", 23f, true))
        root.addView(label("Galaxy S20+ · v0.2.0 · 카카오톡 자동응답 + Python 연동", 13f))
        root.addView(space(10))
        statusText = label("상태를 확인하는 중...", 14f)
        root.addView(statusText)
        root.addView(space(10))

        root.addView(section("① 알림 권한"))
        root.addView(button("S20+ 알림 접근 권한 설정 열기") {
            startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
        })
        root.addView(label("카카오톡 알림에 '답장' 액션이 있어야 자동응답이 가능합니다.", 12f))
        root.addView(space(10))

        root.addView(section("② 앙개봇 작동 설정"))
        powerSwitch = Switch(this).apply {
            text = "자동응답 활성화 (기본 OFF)"
            textSize = 16f
            setPadding(0, dp(4), 0, dp(4))
        }
        root.addView(powerSwitch)
        root.addView(label("호출어 (기본: 앙개야)", 14f, true))
        wakeInput = input(singleLine = true, hint = "앙개야")
        root.addView(wakeInput)
        root.addView(label("허용 채팅방 이름 (한 줄에 하나)", 14f, true))
        roomsInput = input(singleLine = false, hint = "S25+와 S20+의 1:1 대화 알림 제목을 입력")
        root.addView(roomsInput)
        root.addView(label("허용 발신자 표시 이름 (한 줄에 하나)", 14f, true))
        sendersInput = input(singleLine = false, hint = "S25+의 카카오톡에서 표시되는 발신자 이름")
        root.addView(sendersInput)
        root.addView(label("허용 여부는 알림의 표시 이름만으로 판단합니다. 계정 신원 인증은 아닙니다.\n먼저 자동응답 OFF 상태에서 S25+로 메시지를 보내고 아래 RECEIVE 로그의 room/sender 값을 복사하세요.", 12f))
        root.addView(button("설정 저장 / ON·OFF 적용") { saveSettings() })
        root.addView(button("긴급 OFF (즉시 적용)") {
            if (config.disableImmediately()) {
                powerSwitch.isChecked = false
                logs.log("WARN", "EMERGENCY_OFF", "사용자가 긴급 OFF 실행")
                Toast.makeText(this, "자동응답을 즉시 중단했습니다.", Toast.LENGTH_SHORT).show()
            } else {
                AlertDialog.Builder(this).setTitle("긴급 OFF 저장 실패")
                    .setMessage("설정 저장에 실패했습니다. 알림 접근 권한을 직접 해제하세요.")
                    .setPositiveButton("확인", null).show()
            }
            updateStatusAndLogs()
        })
        root.addView(space(10))

        root.addView(space(12))
        root.addView(section("②-A Python 명령 엔진 (Termux)"))
        root.addView(label("기존 테스트/상태/도움말은 Android에서 계속 처리합니다. Python ON일 때만 계산/시간/서버상태가 127.0.0.1:8765로 전달됩니다.", 12f))
        pythonSwitch = Switch(this).apply {
            text = "Python 연결 활성화 (기본 OFF)"
            textSize = 16f
            setPadding(0, dp(4), 0, dp(4))
        }
        root.addView(pythonSwitch)
        root.addView(label("Termux .env의 ANGAE_TOKEN (기기에 암호화 저장)", 14f, true))
        pythonTokenInput = input(singleLine = true, hint = "64자 인증 토큰을 복사해서 붙여넣으세요")
        pythonTokenInput.inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
        root.addView(pythonTokenInput)
        root.addView(button("Python 연결 설정 저장") { savePythonSettings() })
        root.addView(button("Python 서버 연결 테스트") { testPythonConnection() })
        root.addView(label("Python 연결은 휴대폰 내부로만 가능합니다. 토큰을 채팅방·로그·GitHub에 올리지 마세요.", 12f))

        root.addView(section("③ 오프라인 명령 파서 진단"))
        root.addView(label("카카오톡을 보내지 않고 앱 내부에서 명령 문법만 시험합니다.", 12f))
        testInput = input(singleLine = true, hint = "앙개야 테스트")
        testInput.setText("앙개야 테스트")
        root.addView(testInput)
        root.addView(button("로컬 테스트 (카카오톡 전송 안 함)") {
            val text = testInput.text.toString()
            val command = CommandParser.parse(text, wakeInput.text.toString())
            val result = if (command is ParseResult.Command) {
                LocalCommandExecutor.execute(command.name, command.argument)
            } else "호출어가 감지되지 않았습니다."
            logs.log("INFO", "LOCAL_TEST", "input=$text result=$result")
            AlertDialog.Builder(this)
                .setTitle("로컬 테스트 결과")
                .setMessage(result)
                .setPositiveButton("확인", null)
                .show()
            updateStatusAndLogs()
        })
        root.addView(space(10))

        root.addView(section("④ 최근 처리 로그"))
        root.addView(label("메시지 내용과 채팅방 표시 이름이 로컬 DB에 기록됩니다. 개인정보가 포함된 내보내기 파일을 보호하세요.", 12f))
        root.addView(button("로그 새로고침") { updateStatusAndLogs() })
        root.addView(button("로그 전체 TXT 내보내기") { exportLogs() })
        root.addView(button("로그/중복기록 전체 삭제 (확인 필요)") { confirmClearLogs() })
        logsText = label("로그 없음", 12f).apply {
            typeface = Typeface.MONOSPACE
            setTextIsSelectable(true)
            setPadding(dp(10), dp(10), dp(10), dp(10))
            setBackgroundColor(Color.WHITE)
        }
        root.addView(logsText)
        root.addView(space(14))
        root.addView(label("※ 이 앱은 첫 단계 프로토타입입니다. 카카오톡 업데이트나 알림 요약/숨김 설정에 따라 명령을 놓칠 수 있습니다.", 12f))

    }

    private fun loadSettings() {
        val values = config.load()
        powerSwitch.isChecked = values.enabled
        wakeInput.setText(values.wakeWord)
        roomsInput.setText(values.allowedRooms.joinToString("\n"))
        sendersInput.setText(values.allowedSenders.joinToString("\n"))

        try {
            val python = pythonConfig.load()
            pythonSwitch.isChecked = python.enabled
            pythonTokenInput.setText(python.token)
        } catch (e: Exception) {
            pythonSwitch.isChecked = false
            pythonTokenInput.setText("")
            logs.log("ERROR", "PYTHON_SETTINGS_FAILED", "${e.javaClass.simpleName}: 저장된 토큰 확인 필요")
        }
    }

    private fun saveSettings() {
        try {
            config.save(
                powerSwitch.isChecked, wakeInput.text.toString(),
                roomsInput.text.toString(), sendersInput.text.toString()
            )
            logs.log("INFO", "SETTINGS_SAVED", "enabled=${powerSwitch.isChecked} rooms=${BotConfig.parseLines(roomsInput.text.toString()).size} senders=${BotConfig.parseLines(sendersInput.text.toString()).size}")
            Toast.makeText(this, "설정을 저장했습니다.", Toast.LENGTH_SHORT).show()
        } catch (e: IllegalArgumentException) {
            powerSwitch.isChecked = config.load().enabled
            AlertDialog.Builder(this).setTitle("저장 불가").setMessage(e.message).setPositiveButton("확인", null).show()
        } catch (e: Exception) {
            AlertDialog.Builder(this).setTitle("오류").setMessage(e.message).setPositiveButton("확인", null).show()
        }
        updateStatusAndLogs()
    }

    /** v0.2.0 설정은 기존 카카오톡 허용 목록과 완전히 별개로 저장한다. */
    private fun savePythonSettings() {
        try {
            pythonConfig.save(pythonSwitch.isChecked, pythonTokenInput.text.toString())
            logs.log("INFO", "PYTHON_SETTINGS_SAVED", "enabled=${pythonSwitch.isChecked} tokenProvided=${pythonTokenInput.text.isNotBlank()}")
            Toast.makeText(this, "Python 설정을 저장했습니다.", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            pythonSwitch.isChecked = try { pythonConfig.load().enabled } catch (_: Exception) { false }
            AlertDialog.Builder(this).setTitle("Python 설정 저장 불가")
                .setMessage(e.message).setPositiveButton("확인", null).show()
        }
        updateStatusAndLogs()
    }

    /** I/O는 UI 스레드에서 수행하지 않는다. 연결 결과만 메인 스레드에 표시한다. */
    private fun testPythonConnection() {
        thread(name = "angaebot-python-health") {
            val outcome = try {
                val python = pythonConfig.load()
                if (!python.enabled) PythonOutcome.Failure("먼저 Python 연결을 ON으로 저장하세요.")
                else PythonBridgeClient.health(python.token)
            } catch (e: Exception) {
                PythonOutcome.Failure("Python 설정 오류: ${e.javaClass.simpleName}")
            }
            when (outcome) {
                is PythonOutcome.Success -> logs.log("INFO", "PYTHON_HEALTH_OK", "local connection verified")
                is PythonOutcome.Failure -> logs.log("ERROR", "PYTHON_HEALTH_FAILED", outcome.reason)
            }
            runOnUiThread {
                AlertDialog.Builder(this).setTitle("Python 연결 시험")
                    .setMessage(when (outcome) {
                        is PythonOutcome.Success -> outcome.reply
                        is PythonOutcome.Failure -> outcome.reason
                    })
                    .setPositiveButton("확인", null).show()
                updateStatusAndLogs()
            }
        }
    }

    private fun updateStatusAndLogs() {
        try {
            val snap = config.load()
            val enabled = isListenerGranted()
            val connected = KakaoNotificationListener.connected
            val total = logs.count()
            statusText.text = buildString {
                append("알림 접근 권한: ").append(if (enabled) "허용" else "미허용").append('\n')
                append("알림 서비스: ").append(if (connected) "연결됨" else "연결 확인 필요").append('\n')
                append("자동응답: ").append(if (snap.enabled) "ON" else "OFF").append('\n')
                append("허용 채팅방: ").append(snap.allowedRooms.size)
                append(" / 허용 발신자: ").append(snap.allowedSenders.size).append('\n')
                append("전체 이벤트 로그: ").append(total).append("건")
                append('\n').append("Python 명령 엔진: ")
                append(try { if (pythonConfig.load().enabled) "ON" else "OFF" } catch (_: Exception) { "설정 오류" })
            }
            val fmt = SimpleDateFormat("MM-dd HH:mm:ss", Locale.KOREA)
            logsText.text = logs.recent(100).joinToString("\n\n") { entry ->
                "${fmt.format(Date(entry.timestamp))} [${entry.level}] ${entry.stage}\n" +
                    "room=${entry.room} / sender=${entry.sender}\n" + entry.detail
            }.ifBlank { "아직 기록된 이벤트가 없습니다." }
        } catch (e: Exception) {
            statusText.text = "로그/상태 표시 오류: ${e.message}"
        }
    }

    private fun isListenerGranted(): Boolean {
        val enabled = Settings.Secure.getString(contentResolver, "enabled_notification_listeners") ?: return false
        val component = ComponentName(this, KakaoNotificationListener::class.java)
        return enabled.split(':').any { ComponentName.unflattenFromString(it) == component }
    }

    private fun exportLogs() {
        val fileName = "GPT_${SimpleDateFormat("yyyyMMdd", Locale.KOREA).format(Date())}_앙개봇_전체로그_v0.2.0.txt"
        val intent = Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "text/plain"
            putExtra(Intent.EXTRA_TITLE, fileName)
        }
        startActivityForResult(intent, EXPORT_LOGS)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == EXPORT_LOGS && resultCode == RESULT_OK) {
            val uri = data?.data ?: return
            thread(name = "AngaeBotLogExport") {
                try {
                    val stream = contentResolver.openOutputStream(uri, "wt")
                        ?: throw IllegalStateException("선택한 문서를 열지 못했습니다.")
                    logs.writeText(stream)
                    runOnUiThread { Toast.makeText(this, "로그 파일 저장 완료", Toast.LENGTH_LONG).show() }
                } catch (e: Exception) {
                    runOnUiThread {
                        AlertDialog.Builder(this).setTitle("로그 내보내기 실패")
                            .setMessage(e.message).setPositiveButton("확인", null).show()
                    }
                }
            }
        }
    }

    private fun confirmClearLogs() {
        AlertDialog.Builder(this)
            .setTitle("전체 로그 삭제")
            .setMessage("명령/오류 로그 및 중복 감지 기록을 모두 삭제합니다. 복구할 수 없습니다. 먼저 TXT로 내보내세요.")
            .setNegativeButton("취소", null)
            .setPositiveButton("모두 삭제") { _, _ ->
                logs.clearAll()
                logs.log("WARN", "LOG_CLEARED", "사용자가 명시적으로 전체 이벤트 로그를 삭제함")
                updateStatusAndLogs()
            }
            .show()
    }

    override fun onResume() {
        super.onResume()
        visible = true
        uiHandler.removeCallbacks(refreshTask)
        uiHandler.post(refreshTask)
    }

    override fun onPause() {
        visible = false
        uiHandler.removeCallbacks(refreshTask)
        super.onPause()
    }

    private fun label(text: String, size: Float, bold: Boolean = false): TextView = TextView(this).apply {
        this.text = text
        textSize = size
        setTextColor(Color.rgb(26, 43, 58))
        if (bold) setTypeface(null, Typeface.BOLD)
        setPadding(0, dp(4), 0, dp(4))
    }

    private fun section(text: String): TextView = label(text, 17f, true).apply {
        setPadding(0, dp(12), 0, dp(6))
    }

    private fun input(singleLine: Boolean, hint: String): EditText = EditText(this).apply {
        this.hint = hint
        textSize = 14f
        setSingleLine(singleLine)
        if (!singleLine) {
            minLines = 2
            maxLines = 5
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_MULTI_LINE
        }
        setBackgroundColor(Color.WHITE)
        setPadding(dp(10), dp(8), dp(10), dp(8))
        val params = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
        params.bottomMargin = dp(8)
        layoutParams = params
    }

    private fun button(text: String, action: () -> Unit): View = Button(this).apply {
        this.text = text
        isAllCaps = false
        setOnClickListener { action() }
    }

    private fun space(height: Int): View = View(this).apply {
        layoutParams = LinearLayout.LayoutParams(1, dp(height))
    }

    private fun dp(px: Int): Int = (px * resources.displayMetrics.density).toInt()

    companion object { private const val EXPORT_LOGS = 1010 }
}
