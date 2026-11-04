"""앙개봇 v0.2.1 watchdog 회귀 테스트: URL 인증, 장애 및 재시작 명령; 기존 기능 테스트와 병행."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import health_watchdog as wd


class WatchdogTests(unittest.TestCase):
    def test_token_is_read_without_logging(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.env').write_text('ANGAE_TOKEN=some_secret_token_for_testing\n', encoding='utf-8')
            with patch.object(wd, 'CORE', root):
                self.assertEqual(wd.token_from_env(), 'some_secret_token_for_testing')

    def test_healthy_authenticated_request(self):
        response = MagicMock()
        response.__enter__.return_value.status = 200
        with patch.object(wd, 'urlopen', return_value=response) as urlopen:
            self.assertTrue(wd.health_ok('secret'))
            req = urlopen.call_args[0][0]
            self.assertEqual(req.get_header('X-angaebot-token'), 'secret')

    def test_unavailable_server(self):
        with patch.object(wd, 'urlopen', side_effect=ConnectionRefusedError()):
            self.assertFalse(wd.health_ok('secret'))

    def test_restart_calls_supervisor(self):
        process = MagicMock(returncode=0)
        with patch.dict('os.environ', {'PREFIX': '/data/data/com.termux/files/usr'}):
            with patch.object(wd.subprocess, 'run', return_value=process) as call:
                self.assertTrue(wd.restart_service())
                args = call.call_args[0][0]
                self.assertEqual(args[1], 'restart')
                self.assertTrue(args[-1].endswith('/var/service/angaebot-core'))


if __name__ == '__main__':
    unittest.main()
