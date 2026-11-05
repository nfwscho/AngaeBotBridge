"""
앙개봇 v0.6.2 설정 간편 도움말·통합 상태 회귀 테스트 — 기존 기능 보존
1. 설정 8번 도움말은 홈/주식/분야별 메뉴, 통합 상태, 전체 트리, 번호 이동을 간결히 설명한다.
2. 비활성화한 카카오톡 사용자 명령(테스트/ping·계산·질문)을 도움말에 표시하지 않는다.
3. 설정 1번의 Core/감시/SSH·가동시간·실제 배포 브랜치/SHA 통합 조회를 검증한다.
4. 배포정보 누락 시 미확인으로 표시하고 비밀키·사용자 데이터를 노출하지 않는다.
5. 인증·발신자 범위 격리·요청 ID 중복 처리·0/00 복귀와 기존 번호(설 1~7)를 보존한다.
6. 기존 상세상태/서버상태 내부 API와 SQLite jobs/events·AI·주식·배터리/Android UI 기능은 보존한다.
7. 외부 장치/SSH 접속·시세 HTTP·서비스 재시작 없이 임시 SQLite와 mock만 사용한다.
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app
from app.ops import unified_status
from app.selection_menu import StockSelectionMenus


class HelpAndStatusUnitTests(unittest.TestCase):
    def test_short_help_without_retired_commands(self):
        help_text = StockSelectionMenus.help_report()
        self.assertIn('설 1 통합 상태', help_text)
        self.assertIn('설 7 전체 메뉴', help_text)
        self.assertIn('설 8 도움말', help_text)
        self.assertIn('주 분 삼성전자', help_text)
        self.assertLessEqual(len(help_text.splitlines()), 8)
        for retired in ('앙개야 계산', '앙개야 테스트', '앙개야 질문', '서버상태', '상세상태'):
            self.assertNotIn(retired, help_text)

    def test_real_branch_and_services_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'deploy.json'
            file.write_text('{"branch":"feature/menu-settings-20261106","sha":"' + 'b' * 40 + '"}', encoding='utf-8')
            calls = []
            def service(name):
                calls.append(name)
                return '실행 중'
            status = unified_status(91, '0.6.2', services=service,
                                    ssh=lambda: '연결 가능', info_path=file)
            self.assertIn('통합 상태', status)
            self.assertIn('Python Core v0.6.2', status)
            self.assertIn('feature/menu-settings-20261106', status)
            self.assertIn('bbbbbbbbbbbb', status)
            self.assertIn('8022 연결 가능', status)
            self.assertIn('감시 실행 중', status)
            self.assertIn('1분 31초', status)
            self.assertEqual(calls, ['angaebot-core', 'angaebot-watchdog', 'sshd'])
            file.unlink()
            missing = unified_status(0, '0.6.2', services=lambda _: '미설치',
                                     ssh=lambda: '연결 불가', info_path=file)
            self.assertIn('브랜치·커밋 미확인', missing)
            self.assertNotIn('feature/menu-settings', missing)


class HelpAndStatusAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'helpstatus.db'
        self.client = TestClient(create_app('H' * 64, self.path))
        self.headers = {'X-AngaeBot-Token': 'H' * 64}
        self.index = 0

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def post(self, argument, *, sender='나', request_id=None, auth=True):
        self.index += 1
        return self.client.post('/v1/commands', headers=self.headers if auth else {},
                                json={'request_id': request_id or f'helpstatus_{self.index:08d}',
                                      'command': '메뉴', 'argument': argument,
                                      'room': '방', 'sender': sender})

    def test_help_on_settings_8_and_home_7_8(self):
        self.assertEqual(self.post('경로 설정 8', auth=False).status_code, 401)
        a = self.post('경로 설정 8').json()
        self.assertTrue(a['ok'], a)
        self.assertIn('앙개봇 도움말', a['reply'])
        self.assertNotIn('⚙️ 설정·운영 메뉴', a['reply'])
        self.assertEqual(a['module_source'], 'core.menu')
        self.assertTrue(a['menu_active'])
        self.assertIn('앙개봇 메인 메뉴', self.post('선택 0').json()['reply'])
        b = self.post('경로 홈 7 8').json()
        self.assertIn('설 8 도움말', b['reply'])
        self.assertIn('앙개봇 메인 메뉴', self.post('선택 00').json()['reply'])

    def test_status_is_unified_with_source_and_keeps_menu_session(self):
        with patch('app.main.unified_status', return_value='🛠 앙개봇 통합 상태\nCore 정상\n브랜치 기록'):
            packet = self.post('경로 설정 1').json()
        self.assertTrue(packet['ok'], packet)
        self.assertTrue(packet['menu_active'])
        self.assertIn('통합 상태', packet['reply'])
        self.assertEqual(packet['module_source'], 'core.ops')
        self.assertNotIn('⚙️ 설정·운영 메뉴', packet['reply'])
        self.assertIn('전체 메뉴 트리', self.post('선택 7').json()['reply'])
        self.assertIn('앙개봇 메인 메뉴', self.post('선택 0').json()['reply'])

    def test_scope_idempotency_and_logs_preserved(self):
        self.post('설정')
        self.assertFalse(self.post('선택 8', sender='타인').json()['ok'])
        request_id = 'helpstatus_duplicate_001'
        first = self.post('선택 8', request_id=request_id).json()
        duplicate = self.post('선택 8', request_id=request_id).json()
        self.assertTrue(first['ok'])
        self.assertTrue(duplicate['duplicate'])
        self.assertEqual(first['reply'], duplicate['reply'])
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],
                             db.execute('SELECT COUNT(*) FROM events').fetchone()[0])


if __name__ == '__main__':
    unittest.main()
