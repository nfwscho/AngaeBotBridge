"""
앙개봇 v0.5.5 주식 숫자 선택 메뉴 회귀 테스트 — 검증 기능 전체 안내
1. 메인 메뉴 1~6번, 최근 조회·분석 서브메뉴 생성과 1~9 번호 입력을 검증한다.
2. 기존 jobs 이력을 재활용하고 동일 채팅방·발신자에 한해서만 성공한 읽기 명령을 표시한다.
3. 실패/등록/삭제/그룹삭제/프리셋/AI/외부 명령은 최근 선택에 포함하지 않는다.
4. 방·발신자별 메뉴 격리, 번호 범위 검증, 5분 만료, 기존 코드 및 영구 DB 무변경을 확인한다.
5. FastAPI /v1/commands의 인증·이벤트/jobs 로그·중복 요청 ID 및 구버전 명령 응답을 유지한다.
6. 선택된 그룹/종목은 기존 주식 API 코드 경로를 재사용하고 네트워크는 Mock으로 검사한다.
7. Python 선택 상태는 메모리에서만 유지되며 앱 재시작 후 숫자 허용 여부는 Android가 별도 검사한다.
8. 모든 테스트는 임시 SQLite만 사용하고 기존 운영 DB·로그·Android APK·AI/주문/알림 기능을 건드리지 않는다.
9. sqlite3.Connection은 contextlib.closing으로 끝까지 닫아 ResourceWarning을 발생시키지 않는다.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('ANGAE_TOKEN', 'T'*64)
from fastapi.testclient import TestClient
from app.main import create_app
from app.market import StockQuoteError
from app.selection_menu import StockSelectionMenus, MENU_TTL_SECONDS


class MenuSelectionUnitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = sqlite3.connect(str(Path(self.temp.name) / 'stock.db'))
        self.db.executescript('''CREATE TABLE jobs (
            request_id TEXT PRIMARY KEY, command TEXT, argument TEXT, room TEXT,
            sender TEXT, result TEXT, ok INTEGER, created_at INTEGER);
            CREATE TABLE stock_groups (room TEXT, sender TEXT, name TEXT);''')
        self.now = 10.0
        self.menus = StockSelectionMenus(clock=lambda: self.now)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def record(self, id, command, argument, room='방', sender='나', ok=1):
        self.db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)',
                        (id,command,argument,room,sender,'결과',ok,1))

    def test_menu_and_number_and_expiry(self):
        opened = self.menus.open('방', '나')
        self.assertTrue(opened.menu_active)
        self.assertIn('1. 최근 사용한 주식 조회', opened.reply)
        result = self.menus.choose(self.db, '방','나','2')
        self.assertEqual(result.execute_argument, '메모리7')
        self.assertFalse(result.menu_active)
        with self.assertRaisesRegex(StockQuoteError, '5분'):
            self.menus.choose(self.db,'방','나','2')
        self.menus.open('방','나')
        self.now += MENU_TTL_SECONDS
        with self.assertRaisesRegex(StockQuoteError, '5분'):
            self.menus.choose(self.db,'방','나','2')

    def test_recent_filter_and_scope(self):
        self.record('a','주식','분석 삼성전자')
        self.record('b','주식','삭제 반도체 MU')
        self.record('c','주식','분석 마이크론')
        self.record('d','주식','분석 삼성전자')
        self.record('e','주식','분석 엔비디아',sender='다른사람')
        self.record('f','주식','분석 하이닉스',room='다른방')
        self.record('g','주식','그룹생성 반도체')
        self.record('h','주식','메모리7',ok=0)
        self.record('i','주식','목록')
        self.record('j','계산','123*456')
        self.menus.open('방','나')
        sub=self.menus.choose(self.db,'방','나','1')
        self.assertTrue(sub.menu_active)
        self.assertIn('1. 목록',sub.reply)
        self.assertIn('2. 분석 삼성전자',sub.reply)
        self.assertIn('3. 분석 마이크론',sub.reply)
        self.assertNotIn('엔비디아',sub.reply)
        self.assertNotIn('하이닉스',sub.reply)
        self.assertNotIn('삭제',sub.reply)
        self.assertEqual(self.menus.choose(self.db,'방','나','2').execute_argument,'분석 삼성전자')

    def test_submenu_and_invalid_number_and_wrong_sender(self):
        self.menus.open('방','나')
        with self.assertRaisesRegex(StockQuoteError, '메뉴'):
            self.menus.choose(self.db,'방','다른사람','1')
        with self.assertRaisesRegex(StockQuoteError, '없는 번호'):
            self.menus.choose(self.db,'방','나','9')
        with self.assertRaisesRegex(StockQuoteError, '1~9'):
            self.menus.choose(self.db,'방','나','22')
        sub=self.menus.choose(self.db,'방','나','6')
        self.assertTrue(sub.menu_active)
        self.assertIn('마이크론',sub.reply)
        self.assertEqual(self.menus.choose(self.db,'방','나','1').execute_argument,'분석 삼성전자')


class MenuSelectionAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dbpath = Path(self.tmp.name)/'api.db'
        self.client=TestClient(create_app('Q'*64,self.dbpath))
        self.headers={'X-AngaeBot-Token': 'Q'*64}
        self.sequence=0

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def post(self,argument,room='방',sender='나',request_id=None,auth=True):
        self.sequence+=1
        return self.client.post('/v1/commands',headers=self.headers if auth else {},json={
            'request_id':request_id or f'menus_{self.sequence:011d}',
            'command':'주식','argument':argument,'room':room,'sender':sender})

    def test_menu_auth_and_menu_active_metadata(self):
        self.assertEqual(self.post('메뉴',auth=False).status_code,401)
        self.assertFalse(self.post('선택 1').json()['ok'])
        first=self.post('메뉴').json()
        self.assertTrue(first['ok'])
        self.assertTrue(first['menu_active'])
        self.assertIn('최근 사용한',first['reply'])
        analysis=self.post('선택 6').json()
        self.assertTrue(analysis['menu_active'])
        with patch('app.main.fetch_history') as fetched, patch('app.main.individual_report',return_value='분석 보고서'):
            item=self.post('선택 1').json()
            self.assertTrue(item['ok'])
            self.assertEqual(item['reply'],'분석 보고서')
            self.assertFalse(item['menu_active'])
            self.assertEqual(fetched.call_args[0][0].ticker,'005930.KS')
        with closing(sqlite3.connect(self.dbpath)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],4)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],4)

    def test_recent_reexecution_dedup_and_isolation(self):
        with patch('app.main.fetch_history') as fetched, patch('app.main.individual_report',return_value='마이크론 5일 분석'):
            self.assertTrue(self.post('분석 마이크론').json()['ok'])
            self.assertTrue(self.post('메뉴').json()['ok'])
            recent=self.post('선택 1').json()
            self.assertTrue(recent['menu_active'])
            self.assertIn('분석 마이크론',recent['reply'])
            self.assertFalse(self.post('선택 1',sender='다른사람').json()['ok'])
            ident='menus_dedup_case_1'
            executed=self.post('선택 1',request_id=ident).json()
            self.assertTrue(executed['ok'])
            self.assertEqual(executed['reply'],'마이크론 5일 분석')
            repeated=self.post('선택 1',request_id=ident).json()
            self.assertTrue(repeated['duplicate'])
            self.assertEqual(fetched.call_count,2)
            self.assertFalse(self.post('선택 1').json()['ok'])
        with closing(sqlite3.connect(self.dbpath)) as db:
            args=[r[0] for r in db.execute('SELECT argument FROM jobs ORDER BY rowid').fetchall()]
            self.assertEqual(args[:4], ['분석 마이크론','메뉴','선택 1','선택 1'])
            self.assertEqual(len(args),6)  # 상대방 실패/마지막 닫힌 메뉴 실패 포함, 중복 미기록


if __name__=='__main__':
    unittest.main()
