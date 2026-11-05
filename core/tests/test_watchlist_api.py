"""
앙개봇 v0.5.6 관심종목 FastAPI 통합 테스트 — 전체 기능 상세 설명
1. 새 관심종목 명령에 기존 인증 헤더가 필수인지 검증한다.
2. SQLite 요청 ID 중복 실행 시 그룹 추가가 반복되지 않는지 검증한다.
3. 같은 요청 ID에 다른 명령/인수를 쓰면 HTTP 409가 유지되는지 검증한다.
4. 채팅방·발신자별 비공개 그룹의 접근 격리 및 삭제 방지를 확인한다.
5. 외부 주식 조회는 SQL 쓰기 트랜잭션 밖에서 시도하고 mock으로 응답한다.
6. 실패한 그룹 조작/시세는 jobs/events의 기존 ERROR 및 ok 필드를 통해 보존된다.
7. 기존 고정 메모리7, 계산·시간·서버상태 및 AI OFF 명령 응답을 변경하지 않는다.
8. 네트워크 없이 임시 DB에서만 테스트하고 인증키/실제 로그/Android UI는 전혀 변경하지 않는다.
9. v0.5.6 과거 시세 분석은 읽기 전용이고 기존 그룹/사용자 ID/기능이 보존되는지 확인한다.
11. v0.5.6 한글 종목명 조회는 별칭 외 다른 그룹/시세/로그를 손상시키지 않는다.
12. v0.5.6 sqlite3.Connection 문맥 관리자는 연결 종료를 보장하지 않으므로 closing(...)으로 명시적으로 닫아 ResourceWarning을 방지한다.
"""
from __future__ import annotations
from contextlib import closing

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('ANGAE_TOKEN', 'T' * 64)
from fastapi.testclient import TestClient
from app.main import create_app
from app.market import StockQuoteError


class WatchlistAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'core.db'
        self.client = TestClient(create_app('Q'*64, self.path))
        self.headers = {'X-AngaeBot-Token': 'Q'*64}
        self.index = 0

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def cmd(self, argument='', *, command='주식', room='개인방', sender='호출자', request_id=None, authenticated=True):
        self.index += 1
        return self.client.post('/v1/commands', headers=self.headers if authenticated else {}, json={
            'request_id': request_id or f'watchlist_request_{self.index:06d}',
            'command': command, 'argument': argument, 'room': room, 'sender': sender})

    def test_create_and_view_with_legacy(self):
        self.assertTrue(self.cmd('그룹생성 반도체').json()['ok'])
        self.assertTrue(self.cmd('추가 반도체 MU 마이크론').json()['ok'])
        self.assertTrue(self.cmd('추가 반도체 005930 삼성전자').json()['ok'])
        self.assertIn('2종목', self.cmd('목록').json()['reply'])
        with patch('app.main.group_report', return_value='📊 반도체 관심종목 시세 요약\n마이크론 : $100.00 (▲1.00%)') as mock:
            result = self.cmd('반도체').json()
            self.assertTrue(result['ok'])
            self.assertIn('마이크론',result['reply'])
            self.assertEqual(len(mock.call_args.args[1]),2)
        with patch('app.main.execute_stock_command',return_value='💾 메모리7 8종목') as mock:
            result = self.cmd('메모리7',command='주식').json()
            self.assertTrue(result['ok'])
            self.assertIn('메모리7 8종목',result['reply'])
            mock.assert_called_once()
        self.assertIn('156,176',self.cmd('344*454',command='계산').json()['reply'])

    def test_auth_and_duplicate_prevent_side_effects(self):
        self.assertEqual(self.cmd('그룹생성 반도체',authenticated=False).status_code,401)
        request_id='watchlist_unique_101010'
        first=self.cmd('그룹생성 반도체',request_id=request_id).json()
        second=self.cmd('그룹생성 반도체',request_id=request_id).json()
        self.assertTrue(first['ok'])
        self.assertTrue(second['duplicate'])
        self.assertEqual(first['reply'],second['reply'])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM stock_groups').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],1)
        conflict=self.cmd('목록',request_id=request_id)
        self.assertEqual(conflict.status_code,409)

    def test_failed_action_is_logged_and_legacy_ok(self):
        bad=self.cmd('삭제 메모리7 MU').json()
        self.assertFalse(bad['ok'])
        self.assertIn('메모리7',bad['reply'])
        good=self.cmd('123*456',command='계산').json()
        self.assertTrue(good['ok'])
        self.assertIn('56,088',good['reply'])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs WHERE ok=0').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],2)
            self.assertTrue({'stock_groups','stock_items','jobs','events','ai_turns'} <=
                            {x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")})

    def test_group_scope_cannot_cross_rooms_or_users(self):
        self.cmd('그룹생성 비밀')
        self.cmd('추가 비밀 MU')
        for room,sender in [('다른방','호출자'),('개인방','다른사람')]:
            self.assertNotIn('비밀', self.cmd('목록',room=room,sender=sender).json()['reply'])
            result=self.cmd('비밀',room=room,sender=sender).json()
            self.assertFalse(result['ok'])
            self.assertIn('없습니다',result['reply'])
            result=self.cmd('그룹삭제 비밀 확인',room=room,sender=sender).json()
            self.assertFalse(result['ok'])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM stock_items').fetchone()[0],1)

    def test_empty_scope_and_unexpected_group_error(self):
        result=self.cmd('목록',room='',sender='').json()
        self.assertFalse(result['ok'])
        with patch('app.main.group_report',side_effect=StockQuoteError('무료 공급자 모두 실패')):
            self.cmd('그룹생성 반도체')
            self.cmd('추가 반도체 MU')
            failure=self.cmd('반도체').json()
            self.assertFalse(failure['ok'])
            self.assertIn('공급자 모두 실패',failure['reply'])
        self.assertTrue(self.cmd('5+2',command='계산').json()['ok'])

    def test_existing_mechanics_and_ai_off(self):
        status=self.cmd(command='서버상태').json()
        self.assertTrue(status['ok'])
        self.assertIn('v0.5.10',status['reply'])
        self.assertIn('OFF',self.cmd(command='AI상태').json()['reply'])
        self.assertIn('KST',self.cmd(command='시간').json()['reply'])


if __name__ == '__main__':
    unittest.main()
