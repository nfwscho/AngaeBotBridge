"""
앙개봇 실거래 인증키 보호 회귀 테스트 — 전체 테스트 범위
1. 기존 core/.env의 ANGAE_TOKEN·AI 설정·주석·줄바꿈이 그대로 유지되는지 검증한다.
2. MOLIT_API_KEY 신규 추가 및 기존 값 교체가 정확히 한 번 수행되는지 검사한다.
3. 잘못된 키·빈 입력·심볼릭 링크·없는 .env를 거부하고 기존 값을 변경하지 않는다.
4. 실제 발급된 키 대신 고정 가짜 테스트 키만 사용해 외부 네트워크·GitHub 비밀에 접속하지 않는다.
5. 키 설정 뒤 파일 권한이 소유자 전용 0600인지 검증한다.
6. PowerShell SSH 래퍼는 실제 S20+와 접속하지 않고 GitHub Actions에서 별도 문법 검사를 받는다.
7. 기존 DB·로그·Android UI·카카오톡 응답·개인 메모·시세 기능은 변경하지 않는다.
"""
from __future__ import annotations

import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "configure-real-estate-key.py"
SPEC = importlib.util.spec_from_file_location("angae_real_estate_key_config", SCRIPT)
assert SPEC and SPEC.loader
CONFIG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONFIG)
FAKE_KEY = "X" * 64
SECOND_KEY = "Y" * 64


class TestRealEstateKeyConfiguration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = Path(self.temp.name) / ".env"
        self.initial = "ANGAE_TOKEN=local_fake_auth\nANGAE_AI_ENABLED=0\n# existing config\n"
        self.env.write_text(self.initial, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_add_preserves_all_other_config(self):
        CONFIG.configure_env(self.env, FAKE_KEY)
        result = self.env.read_text(encoding="utf-8")
        self.assertTrue(result.startswith(self.initial))
        self.assertEqual(result.count("MOLIT_API_KEY="), 1)
        self.assertTrue(result.endswith("MOLIT_API_KEY=" + FAKE_KEY + "\n"))
        self.assertEqual(stat.S_IMODE(self.env.stat().st_mode), 0o600)

    def test_replace_and_deduplicate_preserves_crlf(self):
        content = "ANGAE_TOKEN=local_fake_auth\r\nMOLIT_API_KEY=old_fake_key\r\n# note\r\nMOLIT_API_KEY=other_old_key\r\nANGAE_AI_ENABLED=1\r\n"
        self.env.write_bytes(content.encode("utf-8"))
        CONFIG.configure_env(self.env, SECOND_KEY)
        result = self.env.read_bytes().decode("utf-8")
        self.assertEqual(result.count("MOLIT_API_KEY="), 1)
        self.assertIn("MOLIT_API_KEY=" + SECOND_KEY + "\r\n", result)
        self.assertIn("# note\r\nANGAE_AI_ENABLED=1\r\n", result)
        self.assertIn("ANGAE_TOKEN=local_fake_auth\r\n", result)

    def test_missing_newline_is_preserved_and_key_added(self):
        self.env.write_text("ANGAE_TOKEN=local_fake_auth", encoding="utf-8")
        CONFIG.configure_env(self.env, FAKE_KEY)
        self.assertEqual(self.env.read_text(encoding="utf-8"),
                         "ANGAE_TOKEN=local_fake_auth\nMOLIT_API_KEY=" + FAKE_KEY + "\n")

    def test_bad_secret_never_modifies_file(self):
        for invalid in ("", "bad", "with space in key", "bad!symbols" * 10, "Z" * 501):
            with self.assertRaises(CONFIG.KeyConfigurationError):
                CONFIG.configure_env(self.env, invalid)
            self.assertEqual(self.env.read_text(encoding="utf-8"), self.initial)

    def test_missing_file_and_symlink_are_rejected(self):
        self.env.unlink()
        with self.assertRaises(CONFIG.KeyConfigurationError):
            CONFIG.configure_env(self.env, FAKE_KEY)
        actual = Path(self.temp.name) / "target.env"
        actual.write_text(self.initial, encoding="utf-8")
        self.env.symlink_to(actual)
        with self.assertRaises(CONFIG.KeyConfigurationError):
            CONFIG.configure_env(self.env, FAKE_KEY)
        self.assertEqual(actual.read_text(encoding="utf-8"), self.initial)


if __name__ == "__main__":
    unittest.main()
