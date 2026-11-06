"""
앙개봇 v0.5.2 관심종목 단위 테스트 — 기존 기능 보존 및 신규 명령 검증 상세 설명
1. 기존 메모리7 종목 8개와 티커/통화는 수정하지 않는다.
2. 주식 그룹생성/목록/그룹삭제 및 별도 stock_groups 테이블 CRUD를 확인한다.
3. 주식 추가/삭제와 한국·미국·일본 종목 정규화 및 원화/달러/엔을 확인한다.
4. 다른 채팅방·발신자의 그룹을 절대 열람하거나 삭제하지 못하는지 검증한다.
5. 중복 종목, 최대 그룹/종목 수, 예약어/악성 티커 및 별칭을 거절하는지 확인한다.
6. 가격 응답은 mock만 사용하고 시세 실패·거래일·표시 순서·그룹 공란을 검증한다.
7. 사용자 명령으로 외부 URL, 임의 셸·파일 명령, 유료 API가 실행되지 않음을 확인한다.
8. 모든 테스트는 임시 SQLite 파일에서만 수행하고 실제 Termux 로그/DB/토큰은 변경하지 않는다.
9. v0.5.1 그룹당 최대 10종목과 고정 미국시총10 프리셋/기존 그룹 보호를 추가 검사한다.
10. v0.5.3 유명 종목의 정확한 한글 이름·동의어 해석, 사용자별 저장 별칭·모호성 및 삭제를 검증한다.
11. 관심종목 시세의 상승 🔺+, 하락 ▽- 표시와 실제 변동률을 검증한다.
12. 카카오톡 관심그룹의 한 줄 간략 시세에서 상승·하락 화살표 뒤 한 글자 공백을 제거하고 그룹 목록/권한/로그를 유지한다.
13. 반도체·미국시총10·사용자 그룹은 한 줄 간략 시세/짧은 시장별 기준시각을 기본으로 하고 99 상세보기에서만 정규장과 제공처 원문을 표시한다.
14. 상세/간략 조회의 그룹 등록·소유자/종목 순서/조회실패/1~10 분석은 그대로 유지한다.
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app.market import WATCHLIST, StockQuoteError, Quote
from app.watchlists import (MAX_GROUPS, MAX_ITEMS, init_schema, resolve_stock, _name,
    execute_group_command, group_report, load_group, is_group_quote_request, command_help)


class WatchlistUnitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = sqlite3.connect(str(Path(self.tmp.name) / 'groups.db'))
        init_schema(self.db)
        self.room = '개인 채팅'
        self.sender = '신뢰 발신자'

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def run_cmd(self, argument, *, room=None, sender=None):
        return execute_group_command(self.db, room or self.room, sender or self.sender, argument)

    def test_watchlist_source_stays_readonly(self):
        self.assertEqual(len(WATCHLIST), 8)
        self.assertEqual([s.ticker for s in WATCHLIST],
                         ['005930.KS', '000660.KS', 'MU', 'SKHY', 'SNDK', '285A.T', 'STX', 'WDC'])
        with self.assertRaises(StockQuoteError):
            self.run_cmd('그룹생성 메모리7')
        with self.assertRaises(StockQuoteError):
            self.run_cmd('추가 메모리7 MU')
        with self.assertRaises(StockQuoteError):
            self.run_cmd('그룹삭제 메모리7 확인')

    def test_create_list_add_read_delete(self):
        self.assertIn('메모리7', self.run_cmd('목록'))
        self.assertIn('그룹 생성', self.run_cmd('그룹생성 반도체'))
        self.assertIn('+', self.run_cmd('추가 반도체 MU 마이크론'))
        self.assertIn('+', self.run_cmd('추가 반도체 005930 삼성전자'))
        rows = load_group(self.db, self.room, self.sender, '반도체')
        self.assertEqual([(s.ticker, s.name) for s in rows],
                         [('MU', '마이크론'), ('005930.KS', '삼성전자')])
        self.assertIn('반도체 2종목', self.run_cmd('목록'))
        self.assertIn('삭제', self.run_cmd('삭제 반도체 MU'))
        self.assertEqual(len(load_group(self.db, self.room, self.sender, '반도체')), 1)
        self.assertIn('삭제', self.run_cmd('그룹삭제 반도체 확인'))
        with self.assertRaises(StockQuoteError):
            load_group(self.db, self.room, self.sender, '반도체')

    def test_scope_isolation(self):
        self.run_cmd('그룹생성 내것')
        self.run_cmd('추가 내것 SKHY')
        for room, sender in [('다른방', self.sender), (self.room, '다른발신자')]:
            with self.assertRaises(StockQuoteError):
                load_group(self.db, room, sender, '내것')
            self.assertNotIn('내것', self.run_cmd('목록', room=room, sender=sender))
            with self.assertRaises(StockQuoteError):
                self.run_cmd('그룹삭제 내것 확인', room=room, sender=sender)
        self.assertEqual(len(load_group(self.db, self.room, self.sender, '내것')), 1)
        for room, sender in [('', self.sender), (self.room, '')]:
            with self.assertRaises(StockQuoteError):
                execute_group_command(self.db, room, sender, '목록')

    def test_empty_group_read_without_http(self):
        self.run_cmd('그룹생성 실험')
        with patch('app.watchlists.fetch_quote') as mock:
            answer = group_report('실험', load_group(self.db, self.room, self.sender, '실험'))
            self.assertIn('비어 있습니다', answer)
            mock.assert_not_called()

    def test_duplicate_names_and_symbols(self):
        self.run_cmd('그룹생성 투자')
        with self.assertRaisesRegex(StockQuoteError, '이미'):
            self.run_cmd('그룹생성 투자')
        self.run_cmd('추가 투자 MU')
        with self.assertRaisesRegex(StockQuoteError, '이미'):
            self.run_cmd('추가 투자 mu 마이크론')
        with self.assertRaisesRegex(StockQuoteError, '없습니다'):
            self.run_cmd('삭제 투자 WDC')

    def test_limits_and_confirmation(self):
        self.run_cmd('그룹생성 첫그룹')
        # 지원하는 정확한 미국 티커만 등록
        for symbol in ('AA', 'BB', 'CC', 'DD', 'EE', 'FF', 'GG', 'HH', 'II', 'JJ'):
            self.run_cmd(f'추가 첫그룹 {symbol}')
        with self.assertRaisesRegex(StockQuoteError, '최대'):
            self.run_cmd('추가 첫그룹 KK')
        with self.assertRaisesRegex(StockQuoteError, '확인'):
            self.run_cmd('그룹삭제 첫그룹')
        self.assertEqual(len(load_group(self.db, self.room, self.sender, '첫그룹')), MAX_ITEMS)
        for index in range(MAX_GROUPS - 1):
            self.run_cmd(f'그룹생성 G{index}')
        with self.assertRaisesRegex(StockQuoteError, '최대'):
            self.run_cmd('그룹생성 추가그룹')

    def test_korean_company_names_and_saved_alias(self):
        expected = {
            '마이크론': 'MU', '삼성전자': '005930.KS', '하이닉스': '000660.KS',
            'SK하이닉스': '000660.KS', 'SK하이닉스ADR': 'SKHY',
            '엔비디아': 'NVDA', '애플': 'AAPL', '구글': 'GOOGL',
            '웨스턴 디지털': 'WDC', '시게이트': 'STX',
            '키오시아': '285A.T', '테슬라': 'TSLA',
        }
        for name, ticker in expected.items():
            with self.subTest(name=name):
                self.assertEqual(resolve_stock(name).ticker, ticker)
        self.run_cmd('그룹생성 반도체')
        self.run_cmd('추가 반도체 NVDA 내GPU')
        from app.watchlists import resolve_saved_alias
        own = resolve_saved_alias(self.db, self.room, self.sender, '내GPU')
        self.assertEqual(own.ticker, 'NVDA')
        self.assertIsNone(resolve_saved_alias(self.db, '다른방', self.sender, '내GPU'))
        self.assertIn('삭제', self.run_cmd('삭제 반도체 내GPU'))
        self.run_cmd('추가 반도체 MU 같은별칭')
        self.run_cmd('그룹생성 미국')
        self.run_cmd('추가 미국 AAPL 같은별칭')
        with self.assertRaisesRegex(StockQuoteError, '여러 종목'):
            resolve_saved_alias(self.db, self.room, self.sender, '같은별칭')

    def test_stock_symbols_validation(self):
        expected = [('삼성전자', '005930.KS', 'KRW'), ('005930', '005930.KS', 'KRW'),
                    ('285A.T', '285A.T', 'JPY'), ('mu', 'MU', 'USD'), ('000660', '000660.KS', 'KRW')]
        for input_ticker, expected_ticker, currency in expected:
            with self.subTest(input_ticker=input_ticker):
                s = resolve_stock(input_ticker)
                self.assertEqual((s.ticker, s.currency), (expected_ticker, currency))
        for bad in ('https://bad.site', '../../bad', 'MU;rm', 'NASDAQ_INDEX', 'B'*200, '000660.KS/evil', '285A.T&foo=1'):
            with self.subTest(value=bad), self.assertRaises(StockQuoteError):
                resolve_stock(bad)
        with self.assertRaises(StockQuoteError):
            resolve_stock('MU', 'hello world')
        for bad in ('메모리7', '그룹생성', 'hello world', 'a/../b'):
            with self.assertRaises(StockQuoteError):
                _name(bad)

    def test_group_quote_real_format_no_http(self):
        self.run_cmd('그룹생성 지수')
        self.run_cmd('추가 지수 005930 삼성전자')
        self.run_cmd('추가 지수 MU 마이크론')
        self.run_cmd('추가 지수 285A.T 키오시아')
        timestamp = datetime(2026,11,4,7,0,tzinfo=timezone.utc)
        def fake(s):
            if s.ticker == '285A.T':
                raise StockQuoteError('provider blocked')
            price, previous = (221500, 219500) if s.currency=='KRW' else (800, 830)
            return Quote(s, price, previous, (price/previous-1)*100, timestamp, timestamp)
        report = group_report('지수', load_group(self.db,self.room,self.sender,'지수'),fetcher=fake)
        self.assertIn('삼성전자 22.1만 🔺+0.91%', report)
        self.assertIn('마이크론 $800 ▽-3.61%', report)
        self.assertIn('키오시아 : 조회 불가', report)
        self.assertIn('1. 삼성전자 ',report)
        self.assertIn('2. 마이크론 ',report)
        self.assertIn('3. 키오시아 : 조회 불가',report)
        self.assertIn('5분 내 1~3',report)
        self.assertIn('📡 KR', report)
        self.assertIn('99. 🔎 상세보기', report)
        self.assertNotIn('시세 출처 · 기준시각:', report)
        self.assertTrue(report.index('삼성전자') < report.index('마이크론') < report.index('키오시아'))
        with self.assertRaisesRegex(StockQuoteError, '모든 시세'):
            group_report('지수', load_group(self.db,self.room,self.sender,'지수'),
                         fetcher=lambda _: (_ for _ in ()).throw(StockQuoteError('blocked')))

    def test_group_detailed_99_retains_full_session_and_source_metadata(self):
        self.run_cmd('그룹생성 반도체')
        self.run_cmd('추가 반도체 005930 삼성전자')
        self.run_cmd('추가 반도체 MU 마이크론')
        stamp = datetime(2026, 11, 6, 5, 0, tzinfo=timezone.utc)
        def fake(stock):
            return Quote(stock, 1000 if stock.currency == 'KRW' else 100,
                         980 if stock.currency == 'KRW' else 98, 2.04, stamp, stamp)
        stocks = load_group(self.db,self.room,self.sender,'반도체')
        compact = group_report('반도체',stocks,fetcher=fake)
        detail = group_report('반도체',stocks,fetcher=fake,detailed=True)
        self.assertIn('99. 🔎 상세보기',compact)
        self.assertIn('99. ↩ 간략보기',detail)
        self.assertIn('시세 출처 · 기준시각:', detail)
        self.assertIn('1. 삼성전자 :', detail)
        self.assertIn('2. 마이크론 :',detail)
        self.assertNotIn('시세 출처 · 기준시각:',compact)
        self.assertNotIn('   └ ',compact)

    def test_group_quote_tenth_row_numbered_no_network(self):
        from app.watchlists import US_MARKET_CAP_PRESET
        self.run_cmd('그룹생성 십종목')
        for ticker, alias in US_MARKET_CAP_PRESET:
            self.run_cmd(f'추가 십종목 {ticker} {alias}')
        stocks = load_group(self.db, self.room, self.sender, '십종목')
        self.assertEqual(len(stocks),10)
        moment = datetime(2026,11,4,15,0,tzinfo=timezone.utc)
        def fake(stock):
            return Quote(stock, 100.0, 95.0, 5.263, moment, moment)
        report=group_report('십종목',stocks,fetcher=fake)
        self.assertIn('1. 엔비디아 ',report)
        self.assertIn('10. 일라이릴리 ',report)
        self.assertIn('5분 내 1~10',report)

    def test_reads_and_writes_do_not_call_network(self):
        with patch('app.watchlists.fetch_quote') as network:
            for cmd in ('목록','그룹생성 반도체','추가 반도체 MU','삭제 반도체 MU','그룹삭제 반도체 확인'):
                self.run_cmd(cmd)
            network.assert_not_called()
        self.assertIn('그룹생성', command_help())
        self.assertIn('주식 분석 마이크론', command_help())
        self.assertTrue(is_group_quote_request('반도체'))
        self.assertFalse(is_group_quote_request('목록'))
        self.assertFalse(is_group_quote_request('추가 반도체 MU'))


if __name__ == '__main__':
    unittest.main()
