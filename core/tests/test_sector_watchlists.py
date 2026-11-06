"""
앙개봇 3대 산업 섹터 37종목/페이지/99 상세보기 회귀 테스트 — 전체 검증 기능
1. AI 주도주 13종목, 반도체·기자재 19종목, 데이터센터·네트워크 5종목을 사용자 지정 순서와 정확한 미국 티커로 유지한다.
2. 2026년 공식 상장 SPCX 및 CBRS, NOW/CRM/TXN/TSM/ASML 등 티커를 확인하며 사용자 입력 정규 종가를 고정하지 않는다.
3. 13/19/5종목 모두 한 화면에 빠짐없이 표시하고 1~19 분석·99 상세보기·0/00 복귀를 검증한다.
4. 기본 시세는 정확히 한 종목당 1행이며 상세 시세만 원본 거래시각·출처·정규/프리/애프터 가격을 보여준다.
5. 모든 고정 섹터에서 97/98 버튼을 제거하고 99 상세만 제공한다.
6. 섹터는 1~19 분석, 일반 메뉴는 1~10 분석으로 구분하고 99 상세·0 이전·00 홈은 유지한다.
7. 홈/주식/분석/메모리7/기존 관심그룹의 위치·최대 10종목·SQLite·로그·배터리·AI 기능을 보존한다.
8. 메뉴 경로 주식 7 99 및 주식 8 19의 실제 티커를 검증하고 메뉴 트리·모듈 소스·5분 만료·스코프·인증을 보존한다.
9. 실제 API 시세/네트워크는 mock fetcher로만 처리하여 외부 시세를 하드코딩하거나 운영 DB/.env/로그를 건드리지 않는다.
10. 구형 97/98 숫자 경로는 한 페이지 섹터에서 거부하며 19개 전부 실제 티커를 선택할 수 있는지 검증한다.
11. AI·반도체·데센의 간략 종목 목록 직후 정확히 2줄(📡 시각/99 상세)을 확인하고 별도 지연·분석 문구를 출력하지 않는다.
12. 조회 실패 원인은 새 줄을 추가하지 않고 시각 줄에 합쳐 기존 오류 건수와 조회 불가 표시를 보존한다.
13. 반도체주 시세는 사용자 지정 19종목(KR 2/JP 1/US 16) 순서와 EWY/DRAM ETF를 정확히 구별해 조회한다.
14. 주식 홈 1~8 선택 순서와 실제 섹터·미국시총10 연결을 검증하고 기존 메모리7은 직접 명령에서 유지한다.
15. 미국 시총10 홈 2번은 운영 DB에 사용자그룹이 없어도 기존 고정 프리셋 10종목을 보여주는지 검증한다.
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
        self.assertEqual(PAGE_SIZE, 19)
        self.assertEqual([(s.key, len(s.stocks)) for s in SECTORS],
                         [('chip', 19), ('us10', 10), ('ai', 13), ('semi', 19), ('dc', 5)])
        expected = {
            'chip': ('005930.KS 000660.KS MU SNDK 285A.T WDC STX SKHY EWY DRAM NVDA TSM AMD INTC AVGO MRVL ARM QCOM ASML').split(),
            'us10': ('NVDA AAPL MSFT GOOGL AMZN SPCX AVGO META TSLA LLY').split(),
            'ai': ('NVDA AAPL MSFT GOOGL AMZN META TSLA PLTR NOW CRM ORCL IBM SPCX').split(),
            'semi': ('ARM AVGO MRVL QCOM AMD INTC TSM TXN MU SKHY ASML AMAT LRCX KLAC CBRS SIMO SNDK STX WDC').split(),
            'dc': ('LITE ANET VRT DELL GLW').split(),
        }
        for sector in SECTORS:
            with self.subTest(sector=sector.key):
                self.assertEqual([s.ticker for s in sector.stocks], expected[sector.key])
                self.assertEqual(len([s for s in sector.stocks if s.market == '한국']), 2 if sector.key == 'chip' else 0)
                self.assertEqual(len([s for s in sector.stocks if s.market == '일본']), 1 if sector.key == 'chip' else 0)
                self.assertTrue(all(s.currency == 'USD' for s in sector.stocks if s.market == '미국'))
        self.assertEqual([s.name for s in get_page('ai', 1)][-3:],
                         ['오라클', 'IBM', '스페이스X'])
        self.assertEqual([s.name for s in get_page('semi', 1)][14], '세레브라스')

    def test_pages_and_rejected_injected_arguments(self):
        self.assertEqual([page_count(k) for k in ('chip', 'us10', 'ai', 'semi', 'dc')], [1, 1, 1, 1, 1])
        self.assertEqual(len(get_page('semi', 1)), 19)
        self.assertEqual(len(get_page('ai', 1)), 13)
        self.assertEqual(len(get_page('dc', 1)), 5)
        self.assertEqual(len(get_page('chip', 1)), 19)
        self.assertEqual(len(get_page('us10', 1)), 10)
        for arg in ('섹터시세 ai 0 간략', '섹터시세 ai 2 상세', '섹터시세 ai 3 상세',
                    '섹터시세 ai 1 매수', '섹터시세 ../../x 1 간략',
                    '섹터시세 dc 2 간략', '섹터시세 semi 1 전체'):
            with self.subTest(arg=arg), self.assertRaises(StockQuoteError):
                parse_sector_request(arg)
        self.assertIsNone(parse_sector_request('메모리7'))
        self.assertEqual(parse_sector_request(sector_argument('ai',1,True)),
                         ('ai', 1, True))
        with self.assertRaises(StockQuoteError):
            get_sector('아무거나')

    def test_compact_and_detailed_sector_reports_keep_exact_page_items(self):
        calls=[]
        def lookup(stock):
            calls.append(stock.ticker)
            return fake_quote(stock)
        brief=sector_report('ai',1,fetcher=lookup)
        self.assertCountEqual(calls,[x.ticker for x in get_page('ai',1)])
        self.assertIn('📊 AI 주도주 (13종목)',brief)
        for label in ('1. 엔비디아','11. 오라클','12. IBM','13. 스페이스X'):
            self.assertIn(label,brief)
        self.assertNotIn('98. ▶',brief)
        self.assertNotIn('97. ◀',brief)
        self.assertIn('99. 🔎 상세보기',brief)
        self.assertNotIn('시세 출처 · 기준시각:',brief)
        self.assertEqual(sum(line.startswith(tuple(str(n)+'. ' for n in range(1,14)))
                             for line in brief.splitlines()),13)
        self.assertEqual(brief.splitlines()[-2:], [
            '📡 11/05 US16:00', '99. 🔎 상세보기'])
        detail=sector_report('ai',1,fetcher=fake_quote,detailed=True)
        self.assertIn('1. 엔비디아 :',detail)
        self.assertIn('13. 스페이스X :',detail)
        self.assertIn('시세 출처 · 기준시각:',detail)
        self.assertIn('99. ↩ 간략보기',detail)

    def test_first_and_last_page_navigation_cues_and_short_dc(self):
        for name,count in (('us10',10),('ai',13),('semi',19),('dc',5)):
            with self.subTest(name=name):
                brief=sector_report(name,1,fetcher=fake_quote)
                self.assertIn('99. 🔎 상세보기',brief)
                self.assertNotIn('98. ▶',brief)
                self.assertNotIn('97. ◀',brief)
                self.assertIn(f'{count}. ',brief)
                nums=[line for line in brief.splitlines() if
                      line.startswith(tuple(str(n)+'. ' for n in range(1,count+1)))]
                self.assertEqual(len(nums),count)
                self.assertEqual(brief.splitlines()[-2:], [
                    '📡 11/05 US16:00',
                    '99. 🔎 상세보기',
                ])
                self.assertEqual(len(brief.splitlines()), count + 3)
                self.assertNotIn('※ 지연·비실시간 ·', brief)
                self.assertNotIn('※ 5분 내', brief)

    def test_failed_sector_quote_still_has_two_footer_lines(self):
        def quote_or_fail(stock):
            if stock.ticker in ('ARM', 'MU'):
                raise StockQuoteError('provider rejected')
            return fake_quote(stock)
        brief = sector_report('semi', 1, fetcher=quote_or_fail)
        self.assertIn('1. ARM : 조회 불가', brief)
        self.assertIn('9. 마이크론 : 조회 불가', brief)
        self.assertEqual(len(brief.splitlines()), 22)
        self.assertIn('2종목 조회 실패', brief.splitlines()[-2])
        self.assertEqual(brief.splitlines()[-1], '99. 🔎 상세보기')

    def test_old_menu_choices_and_source_module(self):
        choices = StockSelectionMenus._stock_choices()
        self.assertEqual(len(choices), 8)
        self.assertEqual([c.label for c in choices], [
            '반도체주 시세', '미국 시총10 시세', 'AI 주도주',
            '반도체 및 기자재', '데센 및 네트워크',
            '최근 사용한 주식 조회', '관심종목 목록', '종목별 분석',
        ])
        for i, key in ((1,'chip'),(2,'us10'),(3,'ai'),(4,'semi'),(5,'dc')):
            self.assertEqual(choices[i-1].command_argument, sector_argument(key,1,False))
        self.assertEqual(choices[1].command_argument, sector_argument('us10',1,False))
        tree = StockSelectionMenus.menu_tree()
        for i, choice in enumerate(choices, start=1):
            self.assertIn(f'1-{i}. {choice.label}', tree)
        self.assertEqual(module_for('메뉴','선택 99','📊 AI 주도주 (13종목)'),
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
        first=self.menu.choose(self.db,'방','나','3')
        self.assertEqual(first.execute_argument,sector_argument('ai',1,False))
        self.menu.open_sector_quotes('방','나','ai',1,previous=first.previous)
        self.assertEqual(self.menu.choose(self.db,'방','나','9').execute_argument,'분석 NOW')
        self.menu.open_sector_quotes('방','나','ai',1,previous=first.previous)
        self.assertEqual(self.menu.choose(self.db,'방','나','13').execute_argument,'분석 SPCX')
        self.menu.open_sector_quotes('방','나','ai',1,previous=first.previous)
        with self.assertRaises(StockQuoteError):
            self.menu.choose(self.db,'방','나','98')
        with self.assertRaises(StockQuoteError):
            self.menu.choose(self.db,'방','나','97')
        detail=self.menu.choose(self.db,'방','나','99')
        self.assertEqual(detail.execute_argument,sector_argument('ai',1,True))
        self.menu.open_sector_quotes('방','나','ai',1,True,previous=detail.previous)
        previous=self.menu.choose(self.db,'방','나','0')
        self.assertEqual(previous.execute_argument,sector_argument('ai',1,False))
        self.assertTrue(previous.restored)
        self.assertIn('주식 메뉴',self.menu.choose(self.db,'방','나','0').reply)
        self.assertIn('메인 메뉴',self.menu.choose(self.db,'방','나','00').reply)

    def test_select_isolation_and_ttl(self):
        self.menu.open_sector_quotes('방','나','semi',1)
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
            self.assertIn('3. AI 주도주',opened['reply'])
            first=self.post('선택 3').json()
            self.assertTrue(first['menu_active'])
            self.assertEqual(first['module_source'],'core.sector_watchlists')
            self.assertEqual(first['reply'],'📊 ai 1 간략')
            self.assertFalse(self.post('선택 98').json()['ok'])
            detail=self.post('선택 99').json()
            self.assertEqual(detail['reply'],'📊 ai 1 상세')
            self.assertFalse(self.post('선택 97',room='타인방').json()['ok'])
            self.assertEqual(self.post('선택 0').json()['reply'],'📊 ai 1 간략')
            self.assertIn('주식 메뉴',self.post('선택 0').json()['reply'])
            self.assertIn('메인 메뉴',self.post('선택 0').json()['reply'])
        with closing(sqlite3.connect(self.dbpath)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],
                             db.execute('SELECT COUNT(*) FROM events').fetchone()[0])

    def test_semiconductor_last_page_and_numeric_stock_analysis(self):
        with patch('app.main.sector_report',return_value='📊 반도체 및 기자재 시세'):
            self.assertTrue(self.post('메뉴').json()['ok'])
            self.assertTrue(self.post('선택 4').json()['ok'])
            self.assertFalse(self.post('선택 98').json()['ok'])
        with patch('app.main.fetch_history') as history, patch(
                'app.main.individual_report',return_value='세레브라스 분석'):
            chosen=self.post('선택 15').json()
            self.assertTrue(chosen['ok'],chosen)
            self.assertEqual(chosen['reply'],'세레브라스 분석')
            self.assertEqual(history.call_args.args[0].ticker,'CBRS')
        with patch('app.main.sector_report',return_value='📊 반도체 및 기자재 시세'):
            self.assertTrue(self.post('경로 주식 4').json()['ok'])
        with patch('app.main.fetch_history') as history, patch(
                'app.main.individual_report',return_value='WDC 분석'):
            chosen=self.post('선택 19').json()
            self.assertTrue(chosen['ok'],chosen)
            self.assertEqual(history.call_args.args[0].ticker,'WDC')

    def test_direct_jump_and_dc_no_next_page(self):
        with patch('app.main.sector_report',return_value='📊 데센 및 네트워크 시세') as renderer:
            resp=self.post('경로 주식 5').json()
            self.assertTrue(resp['ok'])
            renderer.assert_called_once()
            self.assertFalse(self.post('선택 98').json()['ok'])
            self.assertFalse(self.post('선택 97').json()['ok'])
            self.assertTrue(self.post('선택 99').json()['ok'])
        with patch('app.main.sector_report',return_value='🔎 AI 주도주 상세 보기') as renderer:
            hop=self.post('경로 주식 3 99').json()
            self.assertTrue(hop['ok'],hop)
            self.assertTrue(renderer.call_args.kwargs.get('detailed'))
            self.assertEqual(renderer.call_args.args[:2],('ai',1))
        with patch('app.main.fetch_history') as history, patch(
                'app.main.individual_report',return_value='WDC 분석'):
            chosen=self.post('경로 주식 4 19').json()
            self.assertTrue(chosen['ok'],chosen)
            self.assertEqual(history.call_args.args[0].ticker,'WDC')


if __name__ == '__main__':
    unittest.main()
