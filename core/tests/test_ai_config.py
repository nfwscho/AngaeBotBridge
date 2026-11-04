"""앙개봇 v0.3.0 .env 구성/토큰·기존 키·백업 보존 테스트."""
import importlib.util
import os
import stat
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'configure-ai.py'
spec = importlib.util.spec_from_file_location('angaebot_configure_ai', SCRIPT)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_env = module.ENV
        self.old_root = module.ROOT
        module.ROOT = Path(self.tmp.name)
        module.ENV = module.ROOT / '.env'
        module.ENV.write_text('ANGAE_TOKEN=' + 'x' * 64 + '\nCUSTOM_SETTING=keep_me\n', encoding='utf-8')
        os.chmod(module.ENV, 0o600)

    def tearDown(self):
        module.ENV = self.old_env
        module.ROOT = self.old_root
        self.tmp.cleanup()

    def test_token_and_other_variables_preserved(self):
        module.patch_env({'ANGAE_AI_ENABLED': '1', 'ANGAE_AI_PROVIDER': 'ollama'})
        content = module.ENV.read_text(encoding='utf-8')
        self.assertIn('ANGAE_TOKEN=' + 'x' * 64, content)
        self.assertIn('CUSTOM_SETTING=keep_me', content)
        self.assertIn('ANGAE_AI_ENABLED=1', content)
        self.assertIn('ANGAE_AI_PROVIDER=ollama', content)
        self.assertEqual(stat.S_IMODE(module.ENV.stat().st_mode), 0o600)
        self.assertEqual(len(list(module.ROOT.glob('.env.backup.*'))), 1)

    def test_repeated_updates_do_not_duplicate(self):
        module.patch_env({'ANGAE_AI_ENABLED': '1'})
        module.patch_env({'ANGAE_AI_ENABLED': '0'})
        self.assertEqual(module.ENV.read_text().count('ANGAE_AI_ENABLED='),1)
        self.assertEqual(module.read_env()['ANGAE_AI_ENABLED'],'0')

if __name__ == '__main__': unittest.main()
