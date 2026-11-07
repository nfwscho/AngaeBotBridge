/*
 * 앙개봇 Android Bridge v0.3.0 — 전체 관리 UI 기능/동작 상세 안내
 * 1. v0.2의 S20+ 알림 권한/연결 상태, 허용 채팅방·발신자·호출어 관리, 자동응답 OFF를 유지한다.
 * 2. 기존 ①~④ 화면 순서, ON/OFF, 긴급 OFF, 저장 및 5초 상태·로그 갱신을 유지한다.
 * 3. 기존 Python ②-A 섹션의 토큰 AES-GCM 암호화 저장/연결 시험/UI 비동기 처리를 보존한다.
 * 4. 새 자연어 AI 전송 스위치는 기본 OFF이며 기존 Python ON/OFF와 별도로 저장한다.
 * 5. 기존 로컬 명령 문법 검사, 최근 이벤트 로그 열람, 전체 TXT 내보내기를 유지한다.
 * 6. 기존 로그/중복기록 삭제는 명시적 확인 후에만 실행하고 SQLite 내역을 임의로 제거하지 않는다.
 * 7. 전체 로그 내보내기 파일명은 한글 깨짐 방지를 위해 영문으로 저장하며 내용은 한글 그대로 유지한다.
 * 8. AI 제공자/실제 API 키는 Termux .env에서 설정하여 Android에 비밀키를 복제하지 않는다.
 * 9. 기존 계정 신원 한계, 카카오톡 알림 빠른답장 방식, 응답 결과의 한계를 계속 고지한다.
 * 10. 모든 로컬 로그 단계와 서비스 수명주기, 기존 사용자 설정과 AndroidKeyStore 별칭을 유지한다.
 * v0.4.10 카톡 사용자 명령 정리에 맞춰 관리화면의 도움말·통합 상태 안내만 갱신한다.
 * 기존 ON/OFF, 자연어 선택 스위치, 연결 진단, 인증/로그/DB/알림 관리 UI와 동작은 그대로 보존한다.
 * v0.4.11 부/투/메 및 개인 기록 기능 안내만 갱신하고 기존 UI 조작·명령 파서·로그·연결 시험은 유지한다.
 * v0.4.12 사용자 요청 홈 메뉴 순서 및 부·금·개 단축 안내를 갱신하되 기존 UI/동작/로그를 보존한다.
 * v0.4.14 부동산 실거래 단축 기능 배포에 따른 표시 버전만 변경하고 UI·설정·로그·응답 기능을 보존한다.
 * v0.4.15 이미지 첨부 실험용 버전 표시만 갱신하며 모든 스위치·허용목록·토큰·SQLite 로그·내보내기·관리 UI를 유지한다.
 * v0.4.16은 사용자가 직접 승인하는 Android 접근성 이미지 자동전송 스위치와 접근성 설정 이동 버튼만 별도 섹션에 추가한다.
 * 기존 알림 접근 권한/자동응답/허용 방·발신자/Python/AI/테스트/로그 UI·데이터를 그대로 보존하고 기능은 기본 OFF다.
 * v0.4.17 사진 확인 화면 자동 버튼 클릭을 보완하며 기존 이미지 접근성 스위치/설정 및 앱 사용자 설정은 유지한다.
 * v0.4.18은 인증 불필요 잠금 화면 자동 깨우기 안내만 추가하며 기존 UI/DB/로그/토큰/설정은 전부 보존한다.
 * v0.4.19는 사진 전송 '1 보내기' 버튼 인식 보완 버전만 표시하며 기존 관리 UI·로그·설정·토큰을 보존한다.
 * v0.4.20은 개인 메뉴 5번 해야 할 일 등록·완료·삭제 안내만 추가하며 기존 UI·로그·이미지 전송·토큰을 유지한다.
 * v0.4.21은 '개 5 할일 추가 제목' 명령 안내를 추가하되 기존 관리 UI/설정/이미지 자동전송·로그는 모두 유지한다.
 * v0.4.22 MediaSender 직접 공유 진단은 별도 OFF 기본값과 설정 저장 버튼만 추가하며 기존 UI·로그·토큰·이미지 자동전송을 유지한다.
 * v0.4.23은 '직공유경로확인' 관찰 전용 명령 안내를 추가하며 기존 설정/DB/로그/이미지·텍스트 UI를 보존한다.
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
    private lateinit var aiFreeformSwitch: Switch
    private lateinit var imageAutoSwitch: Switch
    private lateinit var mediaDirectSwitch: Switch
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
        root.addView(label("Galaxy S20+ · v0.4.23 · 카카오톡 자동응답 + Python 연동", 13f))
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
        root.addView(label("카톡 메뉴: 앙(홈) / 부(부동산) / 금(금융·투자) / 개(개인 메모·일정) / 설(설정). 기존 투·메 단축어도 지원합니다. 기록 등록·목록·검색·수정·삭제와 '개 5' 해야 할 일, '할일 추가 제목' 또는 '개 5 할일 추가 제목'은 Python ON에서 사용합니다. 테스트·계산·질문 명령은 비활성화되었습니다.", 12f))
        pythonSwitch = Switch(this).apply {
            text = "Python 연결 활성화 (기본 OFF)"
            textSize = 16f
            setPadding(0, dp(4), 0, dp(4))
        }
        root.addView(pythonSwitch)
        aiFreeformSwitch = Switch(this).apply {
            text = "일반 자연어 질문도 AI로 전달 (기본 OFF)"
            textSize = 15f
            setPadding(0, dp(4), 0, dp(4))
        }
        root.addView(aiFreeformSwitch)
        root.addView(label("앙개야 요약 ... / 앙개야 AI상태 / 앙개야 대화초기화\n기존 선택형 자연어 모드는 별도 설정이며, 직접 '질문' 명령은 비활성화되었습니다. 실시간 검색은 별도 연동이 필요합니다.", 12f))
        root.addView(label("Termux .env의 ANGAE_TOKEN (기기에 암호화 저장)", 14f, true))
        pythonTokenInput = input(singleLine = true, hint = "64자 인증 토큰을 복사해서 붙여넣으세요")
        pythonTokenInput.inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
        root.addView(pythonTokenInput)
        root.addView(button("Python 연결 설정 저장") { savePythonSettings() })
        root.addView(button("Python 서버 연결 테스트") { testPythonConnection() })
        root.addView(label("Python 연결은 휴대폰 내부로만 가능합니다. 토큰을 채팅방·로그·GitHub에 올리지 마세요.", 12f))

        root.addView(space(12))
        root.addView(section("②-B 이미지 사진 자동전송 실험"))
        root.addView(label("기존 텍스트 빠른답장은 그대로 유지합니다. 사진 자동전송은 별도 접근성 서비스를 켜야 합니다.\n잠금 상태, 채팅방 이름 불일치, 공유화면 식별 실패 시 사진 전송을 취소합니다.", 12f))
        imageAutoSwitch = Switch(this).apply {
            text = "카카오톡 실제 사진 자동전송 시험 허용 (기본 OFF)"
            textSize = 15f
            setPadding(0, dp(4), 0, dp(4))
        }
        root.addView(imageAutoSwitch)
        root.addView(button("이미지 전송 실험 설정 저장") {
            val saved = ImageAutoConfig.save(this, imageAutoSwitch.isChecked)
            if (saved) {
                logs.log("INFO", "IMAGE_UI_SETTING_SAVED", "enabled=${imageAutoSwitch.isChecked}")
                Toast.makeText(this, "이미지 실험 설정을 저장했습니다.", Toast.LENGTH_SHORT).show()
            } else {
                imageAutoSwitch.isChecked = ImageAutoConfig.enabled(this)
                Toast.makeText(this, "설정 저장 실패", Toast.LENGTH_LONG).show()
            }
            updateStatusAndLogs()
        })
        root.addView(section("②-B-1 MediaSender 직접 공유 진단 · 별도 시험"))
        root.addView(label(
            "기존 사진 자동전송과 독립된 실험이며 기본 OFF입니다.\n" +
            "알림 숫자형 tag를 채팅방 ID 후보로만 사용합니다. 실제 카카오 ID인지는 확인되지 않았습니다.\n" +
            "본인과의 1:1 채팅에서만: 앙개야 이미지 직공유진단 → 별도 ON 저장 → " +
            "5분 이내 앙개야 이미지 직공유경로확인\n" +
            "이 관찰 명령은 전송 버튼을 자동 클릭하지 않고 공유 UI 모양만 기록합니다.\n다른 방 오발송 가능성을 배제할 수 없으므로 테스트 사진만 사용합니다. PIN 잠금은 거부합니다.", 12f))
        mediaDirectSwitch = Switch(this).apply {
            text = "MediaSender 채팅방 직접 공유 시험 허용 (기본 OFF)"
            textSize = 15f
            setPadding(0, dp(4), 0, dp(4))
        }
        root.addView(mediaDirectSwitch)
        root.addView(button("MediaSender 실험 설정 저장") {
            val saved = MediaDirectConfig.save(this, mediaDirectSwitch.isChecked)
            if (saved) {
                logs.log("INFO", "MEDIA_DIRECT_SETTING_SAVED", "enabled=" + mediaDirectSwitch.isChecked)
                Toast.makeText(this, "MediaSender 시험 설정 저장됨", Toast.LENGTH_SHORT).show()
            } else {
                mediaDirectSwitch.isChecked = MediaDirectConfig.enabled(this)
                Toast.makeText(this, "MediaSender 설정 저장 실패", Toast.LENGTH_LONG).show()
            }
            updateStatusAndLogs()
        })
        root.addView(button("이미지 자동전송 접근성 권한 설정 열기") {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        })
        root.addView(label("앱 설정을 ON으로 저장하고 Android 접근성에서 '앙개봇 이미지 공유 실험'을 직접 켜세요.\n시험: '앙개야 이미지 자동시험' (잠금 없는 화면 꺼짐·밀어서 해제는 깨우기 시도, PIN 등 인증 잠금은 거부).\n메시지와 사진 말풍선의 실제 수신 여부는 채팅방에서 확인해야 합니다.", 12f))
        root.addView(space(10))

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
        imageAutoSwitch.isChecked = ImageAutoConfig.enabled(this)
        mediaDirectSwitch.isChecked = MediaDirectConfig.enabled(this)
        wakeInput.setText(values.wakeWord)
        roomsInput.setText(values.allowedRooms.joinToString("\n"))
        sendersInput.setText(values.allowedSenders.joinToString("\n"))

        try {
            val python = pythonConfig.load()
            pythonSwitch.isChecked = python.enabled
            aiFreeformSwitch.isChecked = python.freeformEnabled
            pythonTokenInput.setText(python.token)
        } catch (e: Exception) {
            pythonSwitch.isChecked = false
            aiFreeformSwitch.isChecked = false
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
            pythonConfig.save(pythonSwitch.isChecked, pythonTokenInput.text.toString(), aiFreeformSwitch.isChecked)
            logs.log("INFO", "PYTHON_SETTINGS_SAVED", "enabled=${pythonSwitch.isChecked} tokenProvided=${pythonTokenInput.text.isNotBlank()} aiFreeform=${aiFreeformSwitch.isChecked}")
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
        val fileName = "GPT_${SimpleDateFormat("yyyyMMdd", Locale.KOREA).format(Date())}_AngaeBot_LogExport_v0.3.0.txt"
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
