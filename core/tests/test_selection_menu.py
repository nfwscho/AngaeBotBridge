"""
앙개봇 v0.5.5 주식 숫자 선택 메뉴 회귀 테스트 — 검증 기능 전체 안내
1. 메인 메뉴 1~6번, 최근 조회·분석 서브메뉴 생성과 1~10 번호 입력을 검증한다.
2. 기존 jobs 이력을 재활용하고 동일 채팅방·발신자에 한해서만 성공한 읽기 명령을 표시한다.
3. 실패/등록/삭제/그룹삭제/프리셋/AI/외부 명령은 최근 선택에 포함하지 않는다.
4. 방·발신자별 메뉴 격리, 번호 범위 검증, 5분 만료, 기존 코드 및 영구 DB 무변경을 확인한다.
5. FastAPI /v1/commands의 인증·이벤트/jobs 로그·중복 요청 ID 및 구버전 명령 응답을 유지한다.
6. 선택된 그룹/종목은 기존 주식 API 코드 경로를 재사용하고 네트워크는 Mock으로 검사한다.
7. Python 선택 상태는 메모리에서만 유지되며 앱 재시작 후 숫자 허용 여부는 Android가 별도 검사한다.
8. 모든 테스트는 임시 SQLite만 사용하고 기존 운영 DB·로그·Android APK·AI/주문/알림 기능을 건드리지 않는다.
9. sqlite3.Connection은 contextlib.closing으로 끝까지 닫아 ResourceWarning을 발생시키지 않는다.
10. 메모리7 8종목 고정 순서와 실제 그룹 최대 10종목의 번호 선택을 종목 티커로 안전하게 연결한다.
11. 기존 5분 만료·타 채팅방 선택 차단·모의 시세 실패·중복 request_id 및 기존 DB/로그 보존을 검증한다.
12. 관심그룹 목록 번호 1~N이 메모리7 및 실제 그룹으로 연결되는지 API/격리/로그를 검증한다.
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
from app.market import Stock, StockQuoteError, WATCHLIST
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
        with self.assertRaisesRegex(StockQuoteError, '1~10'):
            self.menus.choose(self.db,'방','나','22')
        sub=self.menus.choose(self.db,'방','나','6')
        self.assertTrue(sub.menu_active)
        self.assertIn('마이크론',sub.reply)
        self.assertEqual(self.menus.choose(self.db,'방','나','1').execute_argument,'분석 삼성전자')


    def test_quoted_stocks_use_exact_tickers_and_ten(self):
        self.menus.open_quotes('방','나', WATCHLIST)
        with self.assertRaisesRegex(StockQuoteError,'5분'):
            self.menus.choose(self.db,'다른방','나','3')
        third=self.menus.choose(self.db,'방','나','3')
        self.assertEqual(third.execute_argument,'분석 MU')
        with self.assertRaisesRegex(StockQuoteError,'5분'):
            self.menus.choose(self.db,'방','나','4')
        self.menus.open_quotes('방','나', WATCHLIST)
        self.assertEqual(self.menus.choose(self.db,'방','나','8').execute_argument,'분석 WDC')
        ten=tuple(Stock('같은별명',f'TEST{i}', 'USD','미국','America/New_York') for i in range(10))
        self.menus.open_quotes('방','나', ten)
        self.assertEqual(self.menus.choose(self.db,'방','나','10').execute_argument,'분석 TEST9')
        with self.assertRaisesRegex(StockQuoteError,'1~10'):
            self.menus.choose(self.db,'방','나','11')

    def test_quote_menu_invalid_lengths_and_expiry(self):
        with self.assertRaisesRegex(StockQuoteError,'1~10'):
            self.menus.open_quotes('방','나', tuple())
        with self.assertRaisesRegex(StockQuoteError,'1~10'):
            self.menus.open_quotes('방','나', WATCHLIST+WATCHLIST)
        self.menus.open_quotes('방','나', WATCHLIST)
        self.now+=MENU_TTL_SECONDS
        with self.assertRaisesRegex(StockQuoteError,'5분'):
            self.menus.choose(self.db,'방','나','1')


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


    def test_direct_memo7_quote_then_number_analysis_and_isolation(self):
        with patch('app.main.execute_stock_command',return_value='💾 메모리7 시세 요약') as quote:
            direct=self.post('메모리7').json()
            self.assertTrue(direct['ok'])
            self.assertTrue(direct['menu_active'])
            self.assertIn('시세 요약',direct['reply'])
            quote.assert_called_once()
        with patch('app.main.fetch_history') as history, patch('app.main.individual_report',return_value='마이크론 5일 분석'):
            wrong=self.post('선택 3',room='다른방').json()
            self.assertFalse(wrong['ok'])
            self.assertFalse(wrong['menu_active'])
            selected=self.post('선택 3').json()
            self.assertTrue(selected['ok'])
            self.assertFalse(selected['menu_active'])
            self.assertEqual(selected['reply'],'마이크론 5일 분석')
            self.assertEqual(history.call_args.args[0].ticker,'MU')
            self.assertFalse(self.post('선택 3').json()['ok'])
        with closing(sqlite3.connect(self.dbpath)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],4)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],4)

    def test_root_menu_memo7_quote_then_eighth_analysis(self):
        with patch('app.main.execute_stock_command',return_value='💾 메모리7 시세 요약'):
            self.assertTrue(self.post('메뉴').json()['menu_active'])
            quote=self.post('선택 2').json()
            self.assertTrue(quote['menu_active'])
        with patch('app.main.fetch_history') as history, patch('app.main.individual_report',return_value='웬디 분석'):
            selected=self.post('선택 8').json()
            self.assertTrue(selected['ok'])
            self.assertEqual(history.call_args.args[0].ticker,'WDC')
            self.assertEqual(selected['reply'],'웬디 분석')

    def test_group_tenth_quote_and_selected_analysis(self):
        from app.watchlists import US_MARKET_CAP_PRESET
        self.assertTrue(self.post('그룹생성 십종목').json()['ok'])
        for ticker, alias in US_MARKET_CAP_PRESET:
            self.assertTrue(self.post(f'추가 십종목 {ticker} {alias}').json()['ok'])
        with patch('app.main.group_report',return_value='📊 십종목 관심종목 시세 요약') as group:
            quote=self.post('십종목').json()
            self.assertTrue(quote['ok'])
            self.assertTrue(quote['menu_active'])
            self.assertEqual(len(group.call_args.args[1]),10)
        with patch('app.main.fetch_history') as history, patch('app.main.individual_report',return_value='일라이릴리 분석'):
            selected=self.post('선택 10').json()
            self.assertTrue(selected['ok'])
            self.assertEqual(history.call_args.args[0].ticker,'LLY')
            self.assertEqual(selected['reply'],'일라이릴리 분석')

    def test_legacy_memory7_command_opens_numeric_selection(self):
        request = {'request_id':'legacy_memory7_000123', 'command':'메모리7',
                   'argument':'', 'room':'방', 'sender':'나'}
        with patch('app.main.execute_stock_command',return_value='💾 메모리7 시세 요약'):
            response=self.client.post('/v1/commands',headers=self.headers,json=request).json()
        self.assertTrue(response['ok'])
        self.assertTrue(response['menu_active'])
        with patch('app.main.fetch_history') as history, patch('app.main.individual_report',return_value='하이닉스 분석'):
            selected=self.post('선택 2').json()
            self.assertTrue(selected['ok'])
            self.assertEqual(history.call_args.args[0].ticker,'000660.KS')
            self.assertEqual(selected['reply'],'하이닉스 분석')

    def test_group_list_number_selection_and_scope(self):
        self.assertTrue(self.post('그룹생성 반도체').json()['ok'])
        self.assertTrue(self.post('그룹생성 미국시총10').json()['ok'])
        listed=self.post('목록').json()
        self.assertTrue(listed['ok'])
        self.assertTrue(listed['menu_active'])
        self.assertIn('1. 메모리7 8종목',listed['reply'])
        self.assertIn('2. 반도체 0종목',listed['reply'])
        self.assertIn('3. 미국시총10 0종목',listed['reply'])
        self.assertFalse(self.post('선택 2',sender='다른사람').json()['ok'])
        with patch('app.main.execute_stock_command',return_value='메모리7 시세') as quote:
            first=self.post('선택 1').json()
            self.assertTrue(first['ok'])
            self.assertEqual(first['reply'],'메모리7 시세')
            quote.assert_called_once()
        self.assertFalse(self.post('선택 3').json()['ok'])
        listed=self.post('목록').json()
        self.assertTrue(listed['menu_active'])
        # 빈 그룹도 기존 시세 조회 경로를 재사용한다.
        second=self.post('선택 2').json()
        self.assertTrue(second['ok'])
        self.assertIn('비어 있습니다',second['reply'])
        listed=self.post('목록').json()
        with patch('app.main.group_report',return_value='미국시총10 시세') as report:
            third=self.post('선택 3').json()
            self.assertTrue(third['ok'])
            self.assertEqual(third['reply'],'미국시총10 시세')
            report.assert_called_once()
        with closing(sqlite3.connect(self.dbpath)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],
                             db.execute('SELECT COUNT(*) FROM events').fetchone()[0])

    def test_quote_failure_does_not_offer_selection(self):
        from app.market import StockQuoteError
        with patch('app.main.execute_stock_command',side_effect=StockQuoteError('무료 조회 실패')):
            failed=self.post('메모리7').json()
            self.assertFalse(failed['ok'])
            self.assertFalse(failed['menu_active'])
        self.assertFalse(self.post('선택 1').json()['ok'])


if __name__=='__main__':
    unittest.main()
