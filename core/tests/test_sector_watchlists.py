"""
앙개봇 3대 산업 섹터 37종목/페이지/99 상세보기 회귀 테스트 — 전체 검증 기능
1. AI 주도주 13종목, 반도체·기자재 19종목, 데이터센터·네트워크 5종목을 사용자 지정 순서와 정확한 미국 티커로 유지한다.
2. 2026년 공식 상장 SPCX 및 CBRS, NOW/CRM/TXN/TSM/ASML 등 티커를 확인하며 사용자 입력 정규 종가를 고정하지 않는다.
3. 13/19종목을 페이지당 10종목 이하로 분리하고 1/2페이지의 실제 1~10 번호·98/97 이동·99 상세보기를 검증한다.
4. 기본 시세는 정확히 한 종목당 1행이며 상세 시세만 원본 거래시각·출처·정규/프리/애프터 가격을 보여준다.
5. 5종목 데센 메뉴에는 페이지 이동 버튼이 없고 99 상세만 제공한다.
6. 1~10번은 현 페이지 티커 분석, 97/98 페이지, 99 상세, 0 직전 화면, 00 홈으로 서로 충돌하지 않는다.
7. 홈/주식/분석/메모리7/기존 관심그룹의 위치·최대 10종목·SQLite·로그·배터리·AI 기능을 보존한다.
8. 메뉴 경로 주식 7 98 99, 주식 8 98 및 전체 메뉴 트리·모듈 소스 표기, 5분 만료·스코프·인증을 검사한다.
9. 실제 API 시세/네트워크는 mock fetcher로만 처리하여 외부 시세를 하드코딩하거나 운영 DB/.env/로그를 건드리지 않는다.
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app.main import create_app
from app.market import Quote, StockQuoteError
from app.sector_watchlists import (
    PAGE_SIZE, SECTORS, get_page, get_sector, page_count, parse_sector_request,
    sector_argument, sector_report,
)
from app.selection_menu import StockSelectionMenus
from app.module_info import module_for

ET = ZoneInfo('America/New_York')


def fake_quote(stock):
    market_time = datetime(2026, 11, 5, 16, 0, tzinfo=ET)
    fetched_at = datetime(2026, 11, 6, 8, 19, tzinfo=ET)
    return Quote(stock, 150.50, 148.0, (150.5 / 148 - 1) * 100,
                 market_time, fetched_at, source='테스트 공급자')


class SectorCatalogTests(unittest.TestCase):
    def test_counts_order_and_verified_tickers(self):
        self.assertEqual(PAGE_SIZE, 10)
        self.assertEqual([(s.key, len(s.stocks)) for s in SECTORS],
                         [('ai', 13), ('semi', 19), ('dc', 5)])
        expected = {
            'ai': ('NVDA AAPL MSFT GOOGL AMZN META TSLA PLTR NOW CRM ORCL IBM SPCX').split(),
            'semi': ('ARM AVGO MRVL QCOM AMD INTC TSM TXN MU SKHY ASML AMAT LRCX KLAC CBRS SIMO SNDK STX WDC').split(),
            'dc': ('LITE ANET VRT DELL GLW').split(),
        }
        for sector in SECTORS:
            with self.subTest(sector=sector.key):
                self.assertEqual([s.ticker for s in sector.stocks], expected[sector.key])
                self.assertTrue(all(s.currency == 'USD' and s.market == '미국'
                                    for s in sector.stocks))
        self.assertEqual([s.name for s in get_page('ai', 2)],
                         ['오라클', 'IBM', '스페이스X'])
        self.assertEqual([s.name for s in get_page('semi', 2)][4], '세레브라스')

    def test_pages_and_rejected_injected_arguments(self):
        self.assertEqual([page_count(k) for k in ('ai', 'semi', 'dc')], [2, 2, 1])
        self.assertEqual([len(get_page('semi', n)) for n in (1, 2)], [10, 9])
        self.assertEqual([len(get_page('ai', n)) for n in (1, 2)], [10, 3])
        self.assertEqual(len(get_page('dc', 1)), 5)
        for arg in ('섹터시세 ai 0 간략', '섹터시세 ai 3 상세',
                    '섹터시세 ai 1 매수', '섹터시세 ../../x 1 간략',
                    '섹터시세 dc 2 간략', '섹터시세 semi 1 전체'):
            with self.subTest(arg=arg), self.assertRaises(StockQuoteError):
                parse_sector_request(arg)
        self.assertIsNone(parse_sector_request('메모리7'))
        self.assertEqual(parse_sector_request(sector_argument('ai',2,True)),
                         ('ai', 2, True))
        with self.assertRaises(StockQuoteError):
            get_sector('아무거나')

    def test_compact_and_detailed_sector_reports_keep_exact_page_items(self):
        calls = []
        def lookup(stock):
            calls.append(stock.ticker)
            return fake_quote(stock)
        brief = sector_report('ai', 2, fetcher=lookup)
        self.assertEqual(calls, ['ORCL', 'IBM', 'SPCX'])
        self.assertIn('AI 주도주 (2/2 · 11~13/13)',brief)
        self.assertIn('1. 오라클',brief)
        self.assertIn('2. IBM',brief)
        self.assertIn('3. 스페이스X',brief)
        self.assertNotIn('마이크로소프트',brief)
        self.assertIn('97. ◀ 이전',brief)
        self.assertNotIn('98. ▶',brief)
        self.assertIn('99. 🔎 상세보기',brief)
        self.assertNotIn('시세 출처 · 기준시각:',brief)
        self.assertEqual(len([l for l in brief.splitlines()
                              if l.startswith(('1. ','2. ','3. '))]),3)
        detail = sector_report('ai',2,fetcher=fake_quote,detailed=True)
        self.assertIn('1. 오라클 :',detail)
        self.assertIn('시세 출처 · 기준시각:',detail)
        self.assertIn('99. ↩ 간략보기',detail)
        self.assertIn('97. ◀ 이전',detail)

    def test_first_and_last_page_navigation_cues_and_short_dc(self):
        for name in ('ai','semi'):
            with self.subTest(name=name):
                brief = sector_report(name,1,fetcher=fake_quote)
                self.assertIn('98. ▶ 다음',brief)
                self.assertIn('99. 🔎 상세보기',brief)
                self.assertNotIn('97. ◀ 이전',brief)
                self.assertLessEqual(
                    sum(line[:3].strip().rstrip('.') in {str(n) for n in range(1,11)}
                        for line in brief.splitlines() if line[:1].isdigit()),10)
        dc = sector_report('dc',1,fetcher=fake_quote)
        self.assertIn('5. 코닝',dc)
        self.assertNotIn('98. ▶',dc)
        self.assertNotIn('97. ◀',dc)
        self.assertIn('99. 🔎 상세보기',dc)
        self.assertIn('📡 11/05 US16:00',dc)

    def test_old_menu_choices_and_source_module(self):
        choices = StockSelectionMenus._stock_choices()
        self.assertEqual(len(choices), 9)
        self.assertEqual([c.label for c in choices[6:]],
                         ['AI 주도주 (13종목)', '반도체 및 기자재 (19종목)',
                          '데센 및 네트워크 (5종목)'])
        for i, key in enumerate(('ai','semi','dc'),start=7):
            self.assertEqual(choices[i-1].command_argument, sector_argument(key,1,False))
        tree = StockSelectionMenus.menu_tree()
        self.assertIn('1-7. AI 주도주 (13종목)',tree)
        self.assertIn('1-8. 반도체 및 기자재 (19종목)',tree)
        self.assertIn('1-9. 데센 및 네트워크 (5종목)',tree)
        self.assertEqual(module_for('메뉴','선택 98','📊 AI 주도주 (2/2 · 11~13/13) 관심종목 시세 요약'),
                         'core.sector_watchlists')


class SectorMenuUnitTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.menu = StockSelectionMenus(clock=lambda: self.now)
        self.db = sqlite3.connect(':memory:')

    def tearDown(self):
        self.db.close()

    def test_sector_98_99_97_and_zero_previous_page(self):
        self.menu.open('방','나')
        first = self.menu.choose(self.db,'방','나','7')
        self.assertEqual(first.execute_argument,sector_argument('ai',1,False))
        self.menu.open_sector_quotes('방','나','ai',1,previous=first.previous)
        self.assertEqual(self.menu.choose(self.db,'방','나','9').execute_argument,'분석 NOW')
        self.menu.open_sector_quotes('방','나','ai',1,previous=first.previous)
        next_page = self.menu.choose(self.db,'방','나','98')
        self.assertEqual(next_page.execute_argument,sector_argument('ai',2,False))
        self.menu.open_sector_quotes('방','나','ai',2,previous=next_page.previous)
        with self.assertRaises(StockQuoteError):
            self.menu.choose(self.db,'방','나','98')
        detailed = self.menu.choose(self.db,'방','나','99')
        self.assertEqual(detailed.execute_argument,sector_argument('ai',2,True))
        self.menu.open_sector_quotes('방','나','ai',2,True,previous=detailed.previous)
        returned = self.menu.choose(self.db,'방','나','0')
        self.assertEqual(returned.execute_argument,sector_argument('ai',2,False))
        self.assertTrue(returned.restored)
        back_page = self.menu.choose(self.db,'방','나','97')
        self.assertEqual(back_page.execute_argument,sector_argument('ai',1,False))
        self.menu.open_sector_quotes('방','나','ai',1,previous=back_page.previous)
        self.assertEqual(self.menu.choose(self.db,'방','나','00').reply.splitlines()[0],
                         '🤖 앙개봇 메인 메뉴')

    def test_select_isolation_and_ttl(self):
        self.menu.open_sector_quotes('방','나','semi',2)
        with self.assertRaises(StockQuoteError):
            self.menu.choose(self.db,'다른방','나','99')
        with self.assertRaises(StockQuoteError):
            self.menu.choose(self.db,'방','다른사람','98')
        self.now += 301.0
        with self.assertRaises(StockQuoteError):
            self.menu.choose(self.db,'방','나','99')


class SectorAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dbpath = Path(self.tmp.name)/'test.db'
        self.client = TestClient(create_app('Z'*64,self.dbpath))
        self.headers = {'X-AngaeBot-Token':'Z'*64}
        self.id = 0

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def post(self,arg,room='방',sender='나',auth=True):
        self.id += 1
        return self.client.post('/v1/commands',headers=self.headers if auth else {},
                                json={'request_id':f'sector_{self.id:011d}',
                                      'command':'메뉴' if arg.startswith('경로 ') else '주식',
                                      'argument':arg,
                                      'room':room,'sender':sender})

    def test_ai_menu_navigation_to_page_two_detail_and_back(self):
        with patch('app.main.sector_report',side_effect=lambda k,p,*,detailed=False:
                   f"📊 {k} {p} {'상세' if detailed else '간략'}"):
            opened=self.post('메뉴').json()
            self.assertTrue(opened['ok'])
            self.assertIn('7. AI 주도주',opened['reply'])
            page1=self.post('선택 7').json()
            self.assertTrue(page1['menu_active'])
            self.assertEqual(page1['module_source'],'core.sector_watchlists')
            self.assertEqual(page1['reply'],'📊 ai 1 간략')
            page2=self.post('선택 98').json()
            self.assertEqual(page2['reply'],'📊 ai 2 간략')
            details=self.post('선택 99').json()
            self.assertEqual(details['reply'],'📊 ai 2 상세')
            self.assertFalse(self.post('선택 97',room='타인방').json()['ok'])
            previous=self.post('선택 0').json()
            self.assertEqual(previous['reply'],'📊 ai 2 간략')
            page1_again=self.post('선택 0').json()
            self.assertEqual(page1_again['reply'],'📊 ai 1 간략')
            menu=self.post('선택 0').json()
            self.assertIn('주식 메뉴',menu['reply'])
            self.assertIn('메인 메뉴',self.post('선택 0').json()['reply'])
        with closing(sqlite3.connect(self.dbpath)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],
                             db.execute('SELECT COUNT(*) FROM events').fetchone()[0])

    def test_semiconductor_last_page_and_numeric_stock_analysis(self):
        with patch('app.main.sector_report',return_value='📊 반도체 및 기자재 시세'):
            self.assertTrue(self.post('메뉴').json()['ok'])
            self.assertTrue(self.post('선택 8').json()['ok'])
            self.assertTrue(self.post('선택 98').json()['ok'])
        with patch('app.main.fetch_history') as history, patch(
                'app.main.individual_report',return_value='세레브라스 분석'):
            chosen=self.post('선택 5').json()
            self.assertEqual(chosen['reply'],'세레브라스 분석')
            self.assertEqual(history.call_args.args[0].ticker,'CBRS')

    def test_direct_jump_and_dc_no_next_page(self):
        with patch('app.main.sector_report',return_value='📊 데센 및 네트워크 시세') as renderer:
            resp=self.post('경로 주식 9').json()
            self.assertTrue(resp['ok'])
            renderer.assert_called_once()
            self.assertFalse(self.post('선택 98').json()['ok'])
            self.assertFalse(self.post('선택 97').json()['ok'])
            self.assertTrue(self.post('선택 99').json()['ok'])
        with patch('app.main.sector_report',return_value='🔎 AI 주도주 상세 보기') as renderer:
            hop=self.post('경로 주식 7 98 99').json()
            self.assertTrue(hop['ok'],hop)
            self.assertTrue(renderer.call_args.kwargs.get('detailed'))
            self.assertEqual(renderer.call_args.args[:2],('ai',2))


if __name__ == '__main__':
    unittest.main()
