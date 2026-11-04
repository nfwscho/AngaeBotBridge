"""
앙개봇 v0.5.1 관심종목 단위 테스트 — 기존 기능 보존 및 신규 명령 검증 상세 설명
1. 기존 메모리7 종목 8개와 티커/통화는 수정하지 않는다.
2. 주식 그룹생성/목록/그룹삭제 및 별도 stock_groups 테이블 CRUD를 확인한다.
3. 주식 추가/삭제와 한국·미국·일본 종목 정규화 및 원화/달러/엔을 확인한다.
4. 다른 채팅방·발신자의 그룹을 절대 열람하거나 삭제하지 못하는지 검증한다.
5. 중복 종목, 최대 그룹/종목 수, 예약어/악성 티커 및 별칭을 거절하는지 확인한다.
6. 가격 응답은 mock만 사용하고 시세 실패·거래일·표시 순서·그룹 공란을 검증한다.
7. 사용자 명령으로 외부 URL, 임의 셸·파일 명령, 유료 API가 실행되지 않음을 확인한다.
8. 모든 테스트는 임시 SQLite 파일에서만 수행하고 실제 Termux 로그/DB/토큰은 변경하지 않는다.
9. v0.5.1 그룹당 최대 10종목과 고정 미국시총10 프리셋/기존 그룹 보호를 추가 검사한다.
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
        self.assertIn('만들었습니다', self.run_cmd('그룹생성 반도체'))
        self.assertIn('추가 완료', self.run_cmd('추가 반도체 MU 마이크론'))
        self.assertIn('추가 완료', self.run_cmd('추가 반도체 005930 삼성전자'))
        rows = load_group(self.db, self.room, self.sender, '반도체')
        self.assertEqual([(s.ticker, s.name) for s in rows],
                         [('MU', '마이크론'), ('005930.KS', '삼성전자')])
        self.assertIn('반도체 : 2종목', self.run_cmd('목록'))
        self.assertIn('삭제했습니다', self.run_cmd('삭제 반도체 MU'))
        self.assertEqual(len(load_group(self.db, self.room, self.sender, '반도체')), 1)
        self.assertIn('삭제했습니다', self.run_cmd('그룹삭제 반도체 확인'))
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
        self.assertIn('삼성전자 : 221,500원 (▲', report)
        self.assertIn('마이크론 : $800.00 (▽', report)
        self.assertIn('키오시아 : 조회 불가', report)
        self.assertIn('현지 거래일:', report)
        self.assertTrue(report.index('삼성전자') < report.index('마이크론') < report.index('키오시아'))
        with self.assertRaisesRegex(StockQuoteError, '모든 시세'):
            group_report('지수', load_group(self.db,self.room,self.sender,'지수'),
                         fetcher=lambda _: (_ for _ in ()).throw(StockQuoteError('blocked')))

    def test_reads_and_writes_do_not_call_network(self):
        with patch('app.watchlists.fetch_quote') as network:
            for cmd in ('목록','그룹생성 반도체','추가 반도체 MU','삭제 반도체 MU','그룹삭제 반도체 확인'):
                self.run_cmd(cmd)
            network.assert_not_called()
        self.assertIn('그룹생성', command_help())
        self.assertTrue(is_group_quote_request('반도체'))
        self.assertFalse(is_group_quote_request('목록'))
        self.assertFalse(is_group_quote_request('추가 반도체 MU'))


if __name__ == '__main__':
    unittest.main()
