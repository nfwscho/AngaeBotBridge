"""
앙개봇 Windows 환경설정 S20+ 병합 배포 회귀 테스트 — 전체 항목
1. Windows BOM/CRLF의 MOLIT_API_KEY를 가져오고 S20+ ANGAE_TOKEN은 보존한다.
2. 기존 AI 및 신규 설정을 적용하면서 S20+ 전용 설정·주석·빈 줄을 유지한다.
3. 변경 전 .env를 백업하고 원본과 백업 권한을 0600으로 설정한다.
4. 동일한 내용으로 반복 배포 시 파일을 다시 쓰지 않는다.
5. 중복 키·잘못된 변수명·명령 치환·누락된 토큰을 거부한다.
6. 원본/입력 파일 부재, 심볼릭 링크, 비정상 인코딩을 안전하게 거부한다.
7. 테스트에서 실제 인증키·GitHub·실기기 연결을 사용하지 않는다.
"""
from __future__ import annotations

import importlib.util
import stat
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "merge-deployment-env.py"
SPEC = importlib.util.spec_from_file_location("angaebot_deploy_env_merge", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HELPER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HELPER)

FAKE_LOCAL_TOKEN = "L" * 64
FAKE_SERVER_TOKEN = "S" * 64
FAKE_MOLIT_KEY = "M" * 64


class TestEnvDeploymentMerge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.remote = self.root / "core" / ".env"
        self.remote.parent.mkdir()
        self.incoming = self.root / "windows" / ".env"
        self.incoming.parent.mkdir()
        self.backup = self.root / "rollback" / ".env"
        self.original = (
            "# existing S20 configuration\n"
            "ANGAE_TOKEN=" + FAKE_SERVER_TOKEN + "\n"
            "ANGAE_AI_ENABLED=0\n"
            "S20_LOCAL_SETTING=preserve_me\n"
            "\n"
        )
        self.remote.write_text(self.original, encoding="utf-8")
        self.incoming.write_bytes((
            "ANGAE_TOKEN=" + FAKE_LOCAL_TOKEN + "\r\n"
            "# Windows settings\r\n"
            "ANGAE_AI_ENABLED=1\r\n"
            "MOLIT_API_KEY=" + FAKE_MOLIT_KEY + "\r\n"
        ).encode("utf-8-sig"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_merge_keeps_s20_token_and_appends_molit_key(self):
        self.assertEqual(HELPER.merge_deployment_env(self.remote, self.incoming, self.backup), 2)
        data = self.remote.read_text(encoding="utf-8")
        self.assertIn("ANGAE_TOKEN=" + FAKE_SERVER_TOKEN + "\n", data)
        self.assertNotIn(FAKE_LOCAL_TOKEN, data)
        self.assertIn("ANGAE_AI_ENABLED=1\n", data)
        self.assertIn("S20_LOCAL_SETTING=preserve_me\n", data)
        self.assertIn("MOLIT_API_KEY=" + FAKE_MOLIT_KEY + "\n", data)
        self.assertNotIn("\r", data)
        self.assertTrue(data.startswith("# existing S20 configuration\n"))
        self.assertEqual(self.backup.read_text(encoding="utf-8"), self.original)
        self.assertEqual(stat.S_IMODE(self.remote.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.backup.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.backup.parent.stat().st_mode), 0o700)

    def test_redeploy_identical_input_is_noop(self):
        HELPER.merge_deployment_env(self.remote, self.incoming, self.backup)
        self.backup.unlink()
        before = self.remote.read_bytes()
        self.assertEqual(HELPER.merge_deployment_env(self.remote, self.incoming, self.backup), 0)
        self.assertEqual(self.remote.read_bytes(), before)
        self.assertFalse(self.backup.exists())

    def test_duplicate_remote_entries_are_replaced_once(self):
        self.remote.write_text(
            "ANGAE_TOKEN=" + FAKE_SERVER_TOKEN + "\nANGAE_AI_ENABLED=0\nANGAE_AI_ENABLED=2\n",
            encoding="utf-8"
        )
        HELPER.merge_deployment_env(self.remote, self.incoming, self.backup)
        self.assertEqual(self.remote.read_text(encoding="utf-8").count("ANGAE_AI_ENABLED="), 1)

    def test_bad_input_does_not_change_remote(self):
        cases = [
            "MOLIT_API_KEY",
            "BROKEN-KEY=value",
            "MOLIT_API_KEY=test\nMOLIT_API_KEY=test2\n",
            "MOLIT_API_KEY=$(bad-command)",
            ("MOLIT_API_KEY=$" + "{INSECURE}"),
            ("MOLIT_API_KEY=" + chr(96) + "bad-command" + chr(96)),
            "MOLIT_API_KEY=first\nSOMETHING=abc\ninvalid line",
            "\n# only comments\n",
        ]
        for value in cases:
            with self.subTest(value=value[:24]):
                self.incoming.write_text(value, encoding="utf-8")
                with self.assertRaises(HELPER.DeploymentEnvError):
                    HELPER.merge_deployment_env(self.remote, self.incoming, self.backup)
                self.assertEqual(self.remote.read_text(encoding="utf-8"), self.original)
                self.assertFalse(self.backup.exists())

    def test_missing_server_token_rejected(self):
        self.remote.write_text("ANGAE_AI_ENABLED=0\n", encoding="utf-8")
        with self.assertRaises(HELPER.DeploymentEnvError):
            HELPER.merge_deployment_env(self.remote, self.incoming, self.backup)
        self.assertEqual(self.remote.read_text(encoding="utf-8"), "ANGAE_AI_ENABLED=0\n")

    def test_existing_backup_never_overwritten(self):
        self.backup.parent.mkdir()
        self.backup.write_text("KEEP BACKUP", encoding="utf-8")
        with self.assertRaises(HELPER.DeploymentEnvError):
            HELPER.merge_deployment_env(self.remote, self.incoming, self.backup)
        self.assertEqual(self.backup.read_text(encoding="utf-8"), "KEEP BACKUP")
        self.assertEqual(self.remote.read_text(encoding="utf-8"), self.original)

    def test_missing_or_invalid_incoming_and_symlinks(self):
        self.incoming.unlink()
        with self.assertRaises(HELPER.DeploymentEnvError):
            HELPER.merge_deployment_env(self.remote, self.incoming, self.backup)
        self.incoming.symlink_to(self.remote)
        with self.assertRaises(HELPER.DeploymentEnvError):
            HELPER.merge_deployment_env(self.remote, self.incoming, self.backup)
        self.incoming.unlink()
        self.incoming.write_bytes(b"\xff\xfe\x00\x00")
        with self.assertRaises(HELPER.DeploymentEnvError):
            HELPER.merge_deployment_env(self.remote, self.incoming, self.backup)
        self.assertEqual(self.remote.read_text(encoding="utf-8"), self.original)


if __name__ == "__main__":
    unittest.main()
