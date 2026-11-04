"""
앙개봇 v0.3.1 안정화 회귀 테스트 — 모든 기능 상세 설명
1. 서버 잠금으로 중복 실행을 거부하는지 확인한다.
2. 서버 로그 크기 미달/초과일 때 누적/보관 정책을 확인한다.
3. 기존 watchdog HEALTH_FAILED/RESTART_REQUESTED 이벤트와 정상 복구 로그를 확인한다.
4. 반복 실패 시 지수 백오프와 회복 시 초기화 상태를 검증한다.
5. watchdog 로그 회전 시 원래 로그 내용의 보존 여부를 검사한다.
6. read-only 진단 출력이 파일과 서비스 비밀키를 변경하지 않음을 검증한다.
7. 실제 SSH 재시작/카톡 발송/파일 삭제 없이 임시 디렉터리와 Mock만 사용한다.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import run_core
import health_watchdog as wd


def load_diagnostic():
    spec = importlib.util.spec_from_file_location('angaebot_diagnostic', SCRIPTS / 'diagnose-autostart.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StabilityTests(unittest.TestCase):
    def test_exclusive_run_lock(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            first = run_core.acquire_lock(root)
            self.assertIsInstance(first, int)
            try:
                second = run_core.acquire_lock(root)
                self.assertIsNone(second)
            finally:
                os.close(first)
            third = run_core.acquire_lock(root)
            self.assertIsInstance(third, int)
            os.close(third)

    def test_rotation_preserves_all_old_server_log_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'logs').mkdir()
            old = (b'OLD_LOG\n' * 32)
            log = root / 'logs' / 'server.log'
            log.write_bytes(old)
            target = run_core.rotate_server_log(root, max_bytes=32)
            self.assertIsNotNone(target)
            self.assertEqual(target.read_bytes(), old)
            self.assertFalse(log.exists())
            log.write_bytes(b'NEW_LOG\n')
            self.assertEqual(log.read_bytes(), b'NEW_LOG\n')
            self.assertEqual(target.read_bytes(), old)

    def test_small_log_not_rotated(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'logs').mkdir()
            (root / 'logs' / 'server.log').write_bytes(b'ok')
            self.assertIsNone(run_core.rotate_server_log(root, 32))
            self.assertEqual((root / 'logs' / 'server.log').read_bytes(), b'ok')

    def test_watchdog_three_failures_and_backoff(self):
        state = wd.WatchdogState()
        events = []
        restarts = []
        def restart():
            restarts.append(True)
            return True
        for moment in (0, 30):
            state.step(False, moment, restart, events.append)
        self.assertEqual(len(restarts), 0)
        state.step(False, 60, restart, events.append)
        self.assertEqual(len(restarts), 1)
        self.assertIn('HEALTH_FAILED', events)
        self.assertIn('RESTART_REQUESTED success=true', events)
        self.assertIn('RESTART_BACKOFF seconds=30', events)
        for moment in (65, 70, 75):
            state.step(False, moment, restart, events.append)
        self.assertEqual(len(restarts), 1)
        state.step(False, 90, restart, events.append)
        self.assertEqual(len(restarts), 2)
        self.assertEqual(state.next_retry, 150)
        state.step(True, 100, restart, events.append)
        self.assertEqual(state.attempts, 0)
        self.assertEqual(state.next_retry, 0)
        self.assertIn('HEALTH_OK', events)

    def test_watchdog_rotation_preserves_original_log(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            logs = root / 'logs'
            logs.mkdir()
            old = 'original_watchdog_log\n' * 6
            (logs / 'watchdog.log').write_text(old, encoding='utf-8')
            with patch.object(wd, 'CORE', root), patch.object(wd, 'WATCHDOG_LOG_MAX_BYTES', 20):
                wd.log('HEALTH_OK')
            copies = list((logs / 'archive').glob('watchdog_*.log'))
            self.assertEqual(len(copies), 1)
            self.assertEqual(copies[0].read_text(encoding='utf-8'), old)
            self.assertIn('HEALTH_OK', (logs / 'watchdog.log').read_text(encoding='utf-8'))

    def test_diagnostics_report_logs_without_modifying(self):
        diag = load_diagnostic()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            logs = root / 'logs'
            logs.mkdir()
            (logs / 'server.log').write_text('private_line\n', encoding='utf-8')
            before = (logs / 'server.log').read_bytes()
            values = diag.log_information(root)
            self.assertTrue(any('server.log=' in value for value in values))
            self.assertFalse(any('private_line' in value for value in values))
            self.assertEqual(before, (logs / 'server.log').read_bytes())


if __name__ == '__main__':
    unittest.main()
