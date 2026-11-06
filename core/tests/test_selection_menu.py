"""
앙개봇 v0.5.5 주식 숫자 선택 메뉴 회귀 테스트 — 검증 기능 전체 안내
1. 메인 메뉴 1~6번, 최근 조회·분석 서브메뉴 생성과 1~10 번호 입력을 검증한다.
18. 주식 메뉴의 기존 1~6번 동작을 유지하면서 7번 상세 시세 보기, 1~8 종목 분석, 0 이전, 독립 채팅방·사용자 격리를 검증한다.
19. '주 7'에 대응하는 메뉴 경로 주식 7의 직접 실행·정확한 모듈 표기·기존 jobs/events 로그를 검증한다.
20. 메모리7 결과 화면에서 숫자 9로 간략↔상세 전환하며 원래 1~8 종목 분석·5분 메뉴·인증·중복방지를 유지한다.
21. 사용자 관심그룹 10종목 번호와 메모리7 전용 숫자 9가 섞이지 않게 검증한다.
22. 주식 메뉴 경로 2→9를 따라가도 중간에 중복 시세 조회를 하지 않고 마지막 상세보기만 한 번 실행한다.
23. 주식 메뉴→간략 시세→9 상세→0 간략→0 주식→0 홈을 실제 HTTP API에서 검증한다.
24. 9를 연속 두 번 눌러 상세↔간략으로 왕복한 후 0은 직전 실제 상세 화면으로 돌아가야 한다.
25. 00은 중간 단계와 무관하게 홈으로 이동하고 방·발신자별 이력·5분 TTL·jobs/events 로그를 지킨다.
26. 종목 분석 결과 화면은 기존 내용 그대로 표시하고 0을 누르면 분석을 선택한 직전 목록으로 되돌아간다.
27. 최근 성공 주식 조회가 없는 화면도 숫자 0으로 주식 메뉴에 복귀하고 00은 홈으로 이동하는지 검증한다.
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
13. 0으로 메인/하위 메뉴 및 그룹 시세에서 이전 화면으로 돌아가고 방·발신자 격리와 만료를 유지하는지 검증한다.
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

    def test_empty_recent_result_zero_returns_to_stock_root(self):
        self.menus.open('방', '나')
        empty = self.menus.choose(self.db, '방', '나', '1')
        self.assertIn('최근 성공한 주식 조회 명령이 없습니다', empty.reply)
        self.assertTrue(empty.menu_active)
        back = self.menus.choose(self.db, '방', '나', '0')
        self.assertIn('📊 주식 메뉴', back.reply)
        self.assertTrue(back.menu_active)
        home = self.menus.choose(self.db, '방', '나', '00')
        self.assertIn('앙개봇 메인 메뉴', home.reply)

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

    def test_memo7_inline_nine_toggles_only_in_memo7_selection(self):
        self.menus.open_quotes('방', '나', WATCHLIST, memory7_view='compact')
        ninth = self.menus.choose(self.db,'방','나','9')
        self.assertEqual(ninth.execute_argument, '메모리7 상세')
        self.assertFalse(ninth.menu_active)
        self.menus.open_quotes('방', '나', WATCHLIST, memory7_view='detail')
        self.assertEqual(self.menus.choose(self.db,'방','나','9').execute_argument,'메모리7')
        self.menus.open_quotes('방', '나', WATCHLIST, memory7_view='compact')
        self.assertEqual(self.menus.choose(self.db,'방','나','1').execute_argument,'분석 005930.KS')
        ten = tuple(Stock('그룹',f'TEST{i}', 'USD', '미국', 'America/New_York')
                    for i in range(10))
        with self.assertRaisesRegex(StockQuoteError,'메모리7'):
            self.menus.open_quotes('방','나', ten, memory7_view='compact')
        self.menus.open_quotes('방','나', ten)
        self.assertEqual(self.menus.choose(self.db,'방','나','9').execute_argument,'분석 TEST8')

    def test_zero_returns_to_root_and_expiry(self):
        self.menus.open('방','나')
        self.assertTrue(self.menus.choose(self.db,'방','나','6').menu_active)
        back=self.menus.choose(self.db,'방','나','0')
        self.assertTrue(back.menu_active)
        self.assertIn('📊 주식 메뉴',back.reply)
        self.assertEqual(self.menus.choose(self.db,'방','나','2').execute_argument,'메모리7')
        with self.assertRaisesRegex(StockQuoteError,'5분'):
            self.menus.choose(self.db,'방','나','0')
        self.menus.open('방','나')
        with self.assertRaisesRegex(StockQuoteError,'5분'):
            self.menus.choose(self.db,'다른방','나','0')
        self.now+=MENU_TTL_SECONDS
        with self.assertRaisesRegex(StockQuoteError,'5분'):
            self.menus.choose(self.db,'방','나','0')

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
            self.assertTrue(item['menu_active'])  # 0으로 직전 분석 종목 목록 복귀
            self.assertEqual(fetched.call_args[0][0].ticker,'005930.KS')
        with closing(sqlite3.connect(self.dbpath)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],4)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],4)

    def test_seventh_stock_menu_detail_uses_legacy_auth_logs_and_analysis_choices(self):
        opened = self.post('메뉴').json()
        self.assertTrue(opened['menu_active'])
        self.assertIn('6. 종목별 분석', opened['reply'])
        self.assertIn('7. 메모리7 시세 상세 보기', opened['reply'])
        with patch('app.main.execute_stock_command', return_value='🔎 메모리7 시세 상세 보기') as renderer:
            detail = self.post('선택 7').json()
            self.assertTrue(detail['ok'])
            self.assertTrue(detail['menu_active'])
            self.assertIn('시세 상세 보기', detail['reply'])
            self.assertEqual(detail['module_source'], 'core.market')
            renderer.assert_called_once_with('주식', '메모리7 상세')
        # 상세 결과의 1~8번은 기존 종목 분석 선택 범위를 그대로 유지한다.
        self.assertFalse(self.post('선택 3',room='다른방').json()['ok'])
        with patch('app.main.fetch_history') as history, patch(
             'app.main.individual_report',return_value='마이크론 분석 결과'):
            selected = self.post('선택 3').json()
            self.assertTrue(selected['ok'])
            self.assertEqual(selected['reply'], '마이크론 분석 결과')
            self.assertEqual(history.call_args.args[0].ticker, 'MU')
        # 메뉴 7번 재진입 후 0(뒤로가기)도 종전 주식 메뉴로 복귀.
        self.assertTrue(self.post('메뉴').json()['ok'])
        with patch('app.main.execute_stock_command', return_value='상세 재조회'):
            self.assertTrue(self.post('선택 7').json()['ok'])
        previous = self.post('선택 0').json()
        self.assertTrue(previous['menu_active'])
        self.assertIn('📊 주식 메뉴',previous['reply'])
        with closing(sqlite3.connect(self.dbpath)) as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM jobs WHERE argument='선택 7' AND ok=1"
            ).fetchone()[0],2)

    def test_seventh_stock_menu_direct_jump_preserves_logging(self):
        with patch('app.main.execute_stock_command', return_value='🔎 메모리7 시세 상세 보기') as renderer:
            self.sequence += 1
            payload = {
                'request_id': f'menus_{self.sequence:011d}',
                'command': '메뉴', 'argument': '경로 주식 7',
                'room': '방', 'sender': '나',
            }
            response = self.client.post('/v1/commands', headers=self.headers, json=payload).json()
            self.assertTrue(response['ok'])
            self.assertTrue(response['menu_active'])
            self.assertEqual(response['module_source'], 'core.market')
            self.assertIn('메모리7 시세 상세 보기', response['reply'])
            renderer.assert_called_once_with('주식', '메모리7 상세')
            repeated = self.client.post('/v1/commands', headers=self.headers, json=payload).json()
            self.assertTrue(repeated['duplicate'])
            self.assertEqual(repeated['module_source'], 'core.market')
        with closing(sqlite3.connect(self.dbpath)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],1)

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
            self.assertTrue(selected['menu_active'])  # 0으로 이전 메모리7 시세표 복귀
            self.assertEqual(selected['reply'],'마이크론 5일 분석')
            self.assertEqual(history.call_args.args[0].ticker,'MU')
            self.assertFalse(self.post('선택 3').json()['ok'])
        with closing(sqlite3.connect(self.dbpath)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],4)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],4)

    def test_zero_from_analysis_result_restores_prior_memory7_quote(self):
        with patch('app.main.execute_stock_command', return_value='💾 메모리7 시세 요약') as renderer:
            self.assertTrue(self.post('메뉴').json()['menu_active'])
            self.assertTrue(self.post('선택 2').json()['menu_active'])
            with patch('app.main.fetch_history') as history, patch(
                 'app.main.individual_report', return_value='마이크론 5일 분석 결과'):
                detail = self.post('선택 3').json()
                self.assertTrue(detail['menu_active'])
                self.assertEqual(detail['reply'], '마이크론 5일 분석 결과')
                self.assertEqual(history.call_args.args[0].ticker, 'MU')
            self.assertFalse(self.post('선택 0', room='타인방').json()['ok'])
            restored = self.post('선택 0').json()
            self.assertTrue(restored['menu_active'])
            self.assertEqual(restored['reply'], '💾 메모리7 시세 요약')
            self.assertEqual(renderer.call_count, 2)
            self.assertIn('주식 메뉴', self.post('선택 0').json()['reply'])

    def test_zero_returns_actual_previous_memo7_view_level_by_level(self):
        def render(_command, argument):
            return ('🔎 메모리7 시세 상세 보기\\n9. ↩ 간략보기'
                    if argument == '메모리7 상세' else
                    '💾 메모리7 시세 요약\\n9. 🔎 상세보기')
        with patch('app.main.execute_stock_command', side_effect=render) as quote:
            opened = self.post('메뉴').json()
            self.assertIn('주식 메뉴', opened['reply'])
            brief = self.post('선택 2').json()
            self.assertIn('시세 요약', brief['reply'])
            self.assertTrue(brief['menu_active'])
            detail = self.post('선택 9').json()
            self.assertIn('상세 보기', detail['reply'])
            self.assertTrue(detail['menu_active'])
            self.assertFalse(self.post('선택 0', sender='다른사람').json()['ok'])
            previous = self.post('선택 0').json()
            self.assertIn('시세 요약', previous['reply'])
            self.assertTrue(previous['menu_active'])
            self.assertEqual(previous['module_source'], 'core.market')
            self.assertEqual(quote.call_count, 3)
            self.assertIn('주식 메뉴', self.post('선택 0').json()['reply'])
            self.assertIn('메인 메뉴', self.post('선택 0').json()['reply'])
        with closing(sqlite3.connect(self.dbpath)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],
                             db.execute('SELECT COUNT(*) FROM events').fetchone()[0])

    def test_zero_from_reverse_ninth_toggle_restores_actual_detail_and_00_home(self):
        with patch('app.main.execute_stock_command', side_effect=lambda _command, argument:
                   '🔎 메모리7 시세 상세 보기' if argument == '메모리7 상세'
                   else '💾 메모리7 시세 요약'):
            self.assertTrue(self.post('메뉴').json()['menu_active'])
            self.assertTrue(self.post('선택 2').json()['menu_active'])
            self.assertIn('상세 보기', self.post('선택 9').json()['reply'])
            self.assertIn('시세 요약', self.post('선택 9').json()['reply'])
            back = self.post('선택 0').json()
            self.assertIn('상세 보기', back['reply'])
            self.assertTrue(back['menu_active'])
            home = self.post('선택 00').json()
            self.assertIn('메인 메뉴', home['reply'])
            self.assertTrue(home['menu_active'])
            self.assertFalse(self.post('선택 9', sender='다른사람').json()['ok'])

    def test_inline_ninth_switches_compact_detail_and_back_without_losing_logs(self):
        def output(command, argument):
            return ('🔎 메모리7 시세 상세 보기\n9. ↩ 간략보기'
                    if argument == '메모리7 상세'
                    else '💾 메모리7 시세 요약\n9. 🔎 상세보기')
        with patch('app.main.execute_stock_command',side_effect=output) as renderer:
            brief = self.post('메모리7').json()
            self.assertTrue(brief['ok'])
            self.assertTrue(brief['menu_active'])
            detail = self.post('선택 9').json()
            self.assertTrue(detail['ok'], detail)
            self.assertIn('상세 보기',detail['reply'])
            self.assertEqual(detail['module_source'],'core.market')
            self.assertTrue(detail['menu_active'])
            back = self.post('선택 9').json()
            self.assertTrue(back['ok'], back)
            self.assertIn('💾 메모리7',back['reply'])
            self.assertTrue(back['menu_active'])
            self.assertEqual(renderer.call_count,3)
        with patch('app.main.fetch_history') as history, patch(
             'app.main.individual_report',return_value='마이크론 분석 결과'):
            selected = self.post('선택 3').json()
            self.assertTrue(selected['ok'])
            self.assertEqual(history.call_args.args[0].ticker,'MU')
            self.assertEqual(selected['reply'],'마이크론 분석 결과')
        with closing(sqlite3.connect(self.dbpath)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],4)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],4)

    def test_direct_jump_stock_two_nine_opens_details_once(self):
        self.sequence += 1
        payload = {
            'request_id': f'menus_{self.sequence:011d}',
            'command': '메뉴',
            'argument': '경로 주식 2 9',
            'room': '방', 'sender': '나',
        }
        with patch('app.main.execute_stock_command', return_value='🔎 메모리7 시세 상세 보기') as renderer:
            response = self.client.post('/v1/commands', headers=self.headers, json=payload).json()
            self.assertTrue(response['ok'], response)
            self.assertEqual(response['module_source'], 'core.market')
            self.assertTrue(response['menu_active'])
            renderer.assert_called_once_with('주식','메모리7 상세')

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
        self.assertTrue(self.post('추가 미국시총10 MU 마이크론').json()['ok'])
        listed=self.post('목록').json()
        self.assertTrue(listed['ok'])
        self.assertTrue(listed['menu_active'])
        self.assertIn('1. 메모리7 8종목',listed['reply'])
        self.assertIn('2. 반도체 0종목',listed['reply'])
        self.assertIn('3. 미국시총10 1종목',listed['reply'])
        self.assertFalse(self.post('선택 2',sender='다른사람').json()['ok'])
        with patch('app.main.execute_stock_command',return_value='메모리7 시세') as quote:
            first=self.post('선택 1').json()
            self.assertTrue(first['ok'])
            self.assertEqual(first['reply'],'메모리7 시세')
            quote.assert_called_once()
        # 메모리7 선택은 기존 8종목 숫자 분석 메뉴를 새로 연다.
        # 따라서 이전 그룹 메뉴가 닫혀도 3번은 종목 선택으로 유효하다.
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

    def test_zero_back_from_groups_and_quote(self):
        self.assertTrue(self.post('그룹생성 반도체').json()['ok'])
        listed=self.post('목록').json()
        self.assertTrue(listed['menu_active'])
        self.assertFalse(self.post('선택 0',sender='다른사람').json()['ok'])
        back=self.post('선택 0').json()
        self.assertTrue(back['menu_active'])
        self.assertIn('📊 주식 메뉴',back['reply'])
        self.assertTrue(self.post('선택 5').json()['menu_active'])
        with patch('app.main.group_report',return_value='반도체 시세'):
            # 그룹에 종목이 없으면 그룹 선택 후 새 종목 선택 메뉴는 열리지 않는다.
            group=self.post('선택 2').json()
            self.assertTrue(group['ok'])
            self.assertEqual(group['reply'],'반도체 시세')
        self.assertFalse(self.post('선택 0').json()['ok'])
        self.assertTrue(self.post('목록').json()['menu_active'])
        self.assertTrue(self.post('선택 0').json()['menu_active'])
        with closing(sqlite3.connect(self.dbpath)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],
                             db.execute('SELECT COUNT(*) FROM events').fetchone()[0])

    def test_zero_from_populated_group_quote_returns_group_list(self):
        self.assertTrue(self.post('그룹생성 반도체').json()['ok'])
        self.assertTrue(self.post('추가 반도체 MU 마이크론').json()['ok'])
        self.assertTrue(self.post('목록').json()['menu_active'])
        with patch('app.main.group_report',return_value='반도체 시세'):
            quote=self.post('선택 2').json()
            self.assertTrue(quote['menu_active'])
            self.assertEqual(quote['reply'],'반도체 시세')
        back=self.post('선택 0').json()
        self.assertTrue(back['ok'])
        self.assertTrue(back['menu_active'])
        self.assertIn('📂 관심그룹',back['reply'])
        root=self.post('선택 0').json()
        self.assertTrue(root['menu_active'])
        self.assertIn('📊 주식 메뉴',root['reply'])
        # 메인 메뉴의 그룹 바로가기는 그룹 목록을 거치지 않았으므로 메인으로 복귀.
        with patch('app.main.group_report',return_value='반도체 시세'):
            direct=self.post('선택 3').json()
            self.assertTrue(direct['menu_active'])
        self.assertIn('📊 주식 메뉴',self.post('선택 0').json()['reply'])

    def test_quote_failure_does_not_offer_selection(self):
        from app.market import StockQuoteError
        with patch('app.main.execute_stock_command',side_effect=StockQuoteError('무료 조회 실패')):
            failed=self.post('메모리7').json()
            self.assertFalse(failed['ok'])
            self.assertFalse(failed['menu_active'])
        self.assertFalse(self.post('선택 1').json()['ok'])


if __name__=='__main__':
    unittest.main()
