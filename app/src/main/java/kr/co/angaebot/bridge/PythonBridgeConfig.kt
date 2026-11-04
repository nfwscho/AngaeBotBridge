/*
 * 앙개봇 Android Bridge v0.3.0 — 전체 기능/보안 안내
 * 1. v0.2의 Python 인증 토큰 AES-GCM AndroidKeyStore 암호화 저장을 그대로 유지한다.
 * 2. Python 연결 ON/OFF, 기존 SharedPreferences 이름 및 암호 키 별칭을 유지한다.
 * 3. 기존 설정 저장/읽기/토큰 검증/로그 정책과 허용 채팅방·발신자 설정을 유지한다.
 * 4. 새 '자연어 자동 전달' 설정을 별도 bool로 보존하고 기본값을 OFF로 한다.
 * 5. 자연어 모드를 사용자가 명시적으로 켜기 전에는 모르는 명령을 AI로 전달하지 않는다.
 * 6. 실시간 AI API 인증키는 Android에 저장하지 않고 Termux의 .env에만 저장한다.
 * 7. 기존 설치 앱을 업데이트해도 이전 Python 토큰/설정이 유지되도록 한다.
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
data class PythonBridgeSettings(val enabled: Boolean, val token: String, val freeformEnabled: Boolean = false)

class PythonBridgeConfig(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences("angaebot_python_v02", Context.MODE_PRIVATE)

    fun load(): PythonBridgeSettings {
        val enabled = prefs.getBoolean("enabled", false)
        val stored = prefs.getString("token_encrypted", null)
        val token = if (stored.isNullOrBlank()) "" else decrypt(stored)
        return PythonBridgeSettings(enabled, token, prefs.getBoolean("ai_freeform_enabled", false))
    }

    fun save(enabled: Boolean, tokenInput: String, freeformEnabled: Boolean = false) {
        val token = tokenInput.trim()
        if (enabled) require(token.length >= 32 && token.length <= 256 && token.all { it.isLetterOrDigit() || it in "_-" }) {
            "Python 토큰은 32~256자의 영문/숫자/_/- 이어야 합니다."
        }
        val encrypted = if (token.isBlank()) null else encrypt(token)
        val ok = prefs.edit().putBoolean("enabled", enabled)
            .putString("token_encrypted", encrypted)
            .putBoolean("ai_freeform_enabled", freeformEnabled).commit()
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
