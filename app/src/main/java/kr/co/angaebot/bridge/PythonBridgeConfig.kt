/*
 * 앙개봇 Android Bridge v0.2.0 — 전체 프로그램 기능 및 Python 설정 보호
 * 1) 기존 카카오톡 알림 수신/명령 추출/허용 채팅방+발신자/호출어/자동답장 기능은 유지한다.
 * 2) 기존 SQLite 로그/중복 감지/모든 UI/로그 내보내기/긴급 OFF 기능을 그대로 유지한다.
 * 3) Python 연결은 기본 OFF이며 기존 '테스트/상태/도움말'은 항상 Android 로컬에서 처리한다.
 * 4) 연결을 ON으로 설정한 경우 '계산/시간/서버상태'만 S20+의 127.0.0.1:8765로 전달한다.
 * 5) API 토큰은 AndroidKeyStore AES-GCM으로 암호화해 앱 내부 SharedPreferences에 보관한다.
 * 6) 토큰을 콘솔, 응답, SQLite 로그에 기록하지 않고 Android 백업도 비활성화한다.
 * 7) 허용 목록의 표시 이름은 강력한 계정 인증이 아니므로 원격 PC/파일 명령은 허용하지 않는다.
 */
package kr.co.angaebot.bridge

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** 별도 보조 설정: 기존 BotConfig의 키/기본값/저장 흐름을 변경하지 않는다. */
data class PythonBridgeSettings(val enabled: Boolean, val token: String)

class PythonBridgeConfig(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences("angaebot_python_v02", Context.MODE_PRIVATE)

    fun load(): PythonBridgeSettings {
        val enabled = prefs.getBoolean("enabled", false)
        val stored = prefs.getString("token_encrypted", null)
        val token = if (stored.isNullOrBlank()) "" else decrypt(stored)
        return PythonBridgeSettings(enabled, token)
    }

    fun save(enabled: Boolean, tokenInput: String) {
        val token = tokenInput.trim()
        if (enabled) require(token.length >= 32 && token.length <= 256 && token.all { it.isLetterOrDigit() || it in "_-" }) {
            "Python 토큰은 32~256자의 영문/숫자/_/- 이어야 합니다."
        }
        val encrypted = if (token.isBlank()) null else encrypt(token)
        val ok = prefs.edit().putBoolean("enabled", enabled)
            .putString("token_encrypted", encrypted).commit()
        check(ok) { "Python 설정 저장에 실패했습니다." }
    }

    private fun secretKey(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val existing = store.getKey(KEY_ALIAS, null) as? SecretKey
        if (existing != null) return existing
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        generator.init(KeyGenParameterSpec.Builder(KEY_ALIAS,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setUserAuthenticationRequired(false)
            .build())
        return generator.generateKey()
    }

    private fun encrypt(text: String): String {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, secretKey())
        val data = cipher.doFinal(text.toByteArray(Charsets.UTF_8))
        return Base64.encodeToString(cipher.iv, Base64.NO_WRAP) + ":" + Base64.encodeToString(data, Base64.NO_WRAP)
    }

    private fun decrypt(text: String): String {
        val parts = text.split(':', limit = 2)
        check(parts.size == 2) { "저장된 Python 인증키 형식이 올바르지 않습니다." }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, secretKey(), GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP)))
        return String(cipher.doFinal(Base64.decode(parts[1], Base64.NO_WRAP)), Charsets.UTF_8)
    }

    private companion object { const val KEY_ALIAS = "angaebot_bridge_python_token_v02" }
}
