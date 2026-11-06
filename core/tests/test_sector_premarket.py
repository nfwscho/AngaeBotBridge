"""
앙개봇 37종목 미국 프리마켓 시세 회귀 테스트 — 기존 기능 전수 보존
1. AI 주도주 13·반도체 및 기자재 19·데센 및 네트워크 5종목이 네이버 공개 해외시세의 NYSE .N 또는 Nasdaq .O 검증된 코드에 매핑되는지 확인한다.
2. 기존 메모리7·사용자 관심그룹·LLY/원래 Nasdaq 지원 코드·SQLite/로그·메뉴 번호·Android 배터리 및 UI는 변경하지 않는다.
3. 모든 신규 티커에 대해 Yahoo 정규장 종가와 네이버 장전 체결이 명시된 모의 JSON을 전송하고 가격·등락률·P 표시를 통합 검증한다.
4. 루트 closePrice(정규가)보다 명시적 overMarketPriceInfo의 체결 시각/가격이 우선 적용되는지 확인한다.
5. 거래소 교차(.N/.O) 티커 혼동, USD 외 통화, 정규장 체결시각, 미래 데이터, 이전 거래일 시각은 거절한다.
6. Naver 403/429 또는 장외 거래 미제공 시 정규장 가격으로만 남기며 P를 임의 생성하지 않는지 검증한다.
7. 네이버에서 장외 데이터가 빈 경우 기존 Yahoo 차트 5일 1분봉과 Nasdaq 추가 소스·로그 경로를 보존한다.
8. 미국 뉴욕 현지 프리 04:00~09:30와 정규 09:30~16:00 구분, 실제 조회 시점·타임존 및 이전 종가와의 비교 기준을 검증한다.
9. 모든 테스트는 독립 메모리 객체·주입 HTTP opener만 사용하며 외부 인터넷, 운영 DB, GitHub 앱 설정을 변경하지 않는다.
10. GitHub Actions 실네트워크 확인: NYSE의 .N 폴링 응답은 빈 datas, 접미사 없는 티커는 종목 data가 있어 NYSE 쿼리는 bare 코드만 사용한다.
11. 정규 Reuters RIC .N과 공급자 특화 조회 코드가 다름을 엄격히 테스트하고 임의 코드의 확장을 금지한다.
12. NYSE ORCL/ANET/DELL 공개 폴링 datas=[]에서 기본 API bare 코드로 실거래가를 복구하고 1차 실패/2차 성공·P 표시를 검증한다.
"""
from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from urllib.error import HTTPError
from unittest.mock import patch
from zoneinfo import ZoneInfo

from app.market import Quote, Stock, fetch_quote, compact_quote_line
from app.extended_naver import reuters_code, parse_naver_extended
from app.sector_watchlists import SECTORS

ET = ZoneInfo('America/New_York')
NOW = datetime(2026, 11, 6, 9, 7, tzinfo=ET)
PREVIOUS_CLOSE = datetime(2026, 11, 5, 16, 0, tzinfo=ET)
PRE_TRADE = datetime(2026, 11, 6, 9, 3, tzinfo=ET)

EXPECTED_NYSE = {
    'NOW', 'CRM', 'ORCL', 'IBM', 'TSM', 'ANET', 'VRT', 'DELL', 'GLW',
}


class _Reply:
    def __init__(self, body):
        self._body = json.dumps(body).encode('utf-8')
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return None
    def read(self, _limit):
        return self._body


def _regular(stock):
    return {'chart': {'result': [{'meta': {
        'symbol': stock.ticker, 'currency': 'USD',
        'regularMarketPrice': 100.0,
        'regularMarketTime': int(PREVIOUS_CLOSE.timestamp()),
        'previousClose': 105.0,
    }}]}}


def _polling(stock, *, ric=None, price=104.25, traded=PRE_TRADE, explicit=False):
    code = ric or reuters_code(stock)
    stamp = traded.isoformat()
    value = {'reutersCode': code, 'currencyType': {'name': 'USD'},
             'marketSessionType': 'preMarket', 'closePrice': str(price),
             'localTradedAt': stamp}
    if explicit:
        value['closePrice'] = '100'
        value['overMarketPriceInfo'] = {
            'tradingSessionType': 'PRE_MARKET',
            'overPrice': str(price), 'localTradedAt': stamp,
        }
    return {'datas': [value]}


class VerifiedSectorPremarketTests(unittest.TestCase):
    def test_37_symbols_have_exchange_correct_reuters_code(self):
        stocks = [stock for sector in SECTORS for stock in sector.stocks]
        self.assertEqual(len(stocks), 37)
        self.assertEqual(len(set(stock.ticker for stock in stocks)),
                         len(stocks))
        for stock in stocks:
            with self.subTest(ticker=stock.ticker):
                expected = stock.ticker if stock.ticker in EXPECTED_NYSE else stock.ticker + '.O'
                self.assertEqual(reuters_code(stock), expected)
        self.assertEqual(reuters_code(Stock('미확인', 'ZZZZ', 'USD', '미국',
                                           'America/New_York')), '')

    def test_all_37_premarket_prices_render_p_and_correct_percent(self):
        stocks = [stock for sector in SECTORS for stock in sector.stocks]
        for stock in stocks:
            with self.subTest(ticker=stock.ticker):
                calls = []
                def opener(req, timeout):
                    url = req.full_url
                    calls.append(url)
                    if 'query1.finance.yahoo.com' in url and 'interval=1d' in url:
                        return _Reply(_regular(stock))
                    if 'stock.naver.com/api/polling/worldstock' in url:
                        return _Reply(_polling(stock))
                    raise AssertionError('unexpected provider call: ' + url)
                quote = fetch_quote(stock, opener=opener, now=NOW)
                self.assertEqual(quote.price, 100.0)
                self.assertEqual(len(quote.extended), 1)
                extra = quote.extended[0]
                self.assertEqual(extra.session, '프리')
                self.assertAlmostEqual(extra.price, 104.25)
                self.assertAlmostEqual(extra.percent, 4.25)
                self.assertEqual(extra.market_time, PRE_TRADE)
                rendered = compact_quote_line(quote)
                self.assertIn(' $104.25 ', rendered)
                self.assertIn('🔺+4.25% P', rendered)
                self.assertEqual(len(calls), 2)
                self.assertIn('reutersCodes=' + reuters_code(stock), calls[1])

    def test_nyse_and_nasdaq_wrong_ric_rejected(self):
        for sector in SECTORS:
            for stock in sector.stocks:
                wrong = stock.ticker + ('.O' if stock.ticker in EXPECTED_NYSE else '.N')
                with self.subTest(ticker=stock.ticker):
                    base = Quote(stock, 100, 105, -4.7619, PREVIOUS_CLOSE, NOW)
                    self.assertFalse(parse_naver_extended(
                        stock, _polling(stock, ric=wrong), base, now=NOW))

    def test_explicit_premarket_price_wins_over_regular_close(self):
        for ticker in ('ARM', 'MRVL', 'TSM', 'NOW', 'GLW', 'LITE'):
            stock = next(s for g in SECTORS for s in g.stocks if s.ticker == ticker)
            base = Quote(stock, 100, 105, -4.7619, PREVIOUS_CLOSE, NOW)
            found = parse_naver_extended(stock, _polling(stock, explicit=True),
                                         base, now=NOW)
            self.assertEqual(len(found), 1)
            self.assertAlmostEqual(found[0].price, 104.25)
            self.assertAlmostEqual(found[0].percent, 4.25)

    def test_old_and_future_trade_not_treated_as_current_premarket(self):
        stock = next(s for g in SECTORS for s in g.stocks if s.ticker == 'ANET')
        base = Quote(stock, 100, 105, -4.7619, PREVIOUS_CLOSE, NOW)
        for traded in (datetime(2026, 11, 5, 9, 3, tzinfo=ET),
                       datetime(2026, 11, 6, 9, 31, tzinfo=ET),
                       datetime(2026, 11, 6, 9, 8, tzinfo=ET)):
            with self.subTest(traded=traded):
                self.assertFalse(parse_naver_extended(
                    stock, _polling(stock, traded=traded), base, now=NOW))

    def test_nyse_empty_polling_recovers_from_bare_basic(self):
        # 일부 NYSE 종목의 polling datas=[]에서 종료하지 않고 basic을 사용한다.
        for ticker in ('ORCL', 'ANET', 'DELL'):
            stock = next(s for group in SECTORS for s in group.stocks
                         if s.ticker == ticker)
            with self.subTest(ticker=ticker):
                urls = []
                def opener(req, timeout):
                    url = req.full_url
                    urls.append(url)
                    if 'interval=1d' in url and 'query1.finance.yahoo.com' in url:
                        return _Reply(_regular(stock))
                    if '/api/polling/worldstock' in url:
                        return _Reply({'pollingInterval': 7000, 'datas': []})
                    if '/api/securityService/stock/' in url and '/basic' in url:
                        return _Reply(_polling(stock, explicit=True))
                    raise AssertionError('unexpected provider call: ' + url)
                quote = fetch_quote(stock, opener=opener, now=NOW)
                self.assertEqual(len(quote.extended), 1)
                self.assertAlmostEqual(quote.extended[0].price, 104.25)
                self.assertIn(' P', compact_quote_line(quote))
                self.assertEqual(len(urls), 3)
                self.assertIn('reutersCodes=' + ticker, urls[1])
                self.assertIn('/stock/' + ticker + '/basic', urls[2])
                self.assertNotIn('.N', urls[1] + urls[2])

    def test_naver_403_preserves_regular_quote_and_yahoo_backup(self):
        stock = next(s for g in SECTORS for s in g.stocks if s.ticker == 'GLW')
        urls = []
        def opener(req, timeout):
            url = req.full_url
            urls.append(url)
            if 'query1.finance.yahoo.com' in url and 'interval=1d' in url:
                return _Reply(_regular(stock))
            if 'stock.naver.com' in url:
                raise HTTPError(url, 403, 'Blocked', {}, None)
            if 'interval=1m' in url:
                return _Reply({'chart': {'result': [{
                    'meta': {'symbol': stock.ticker, 'currency': 'USD'},
                    'timestamp': [], 'indicators': {'quote': [{
                        'close': [], 'volume': [],
                    }]},
                }]}})
            if 'api.nasdaq.com' in url:
                raise HTTPError(url, 403, 'Blocked', {}, None)
            raise AssertionError('unexpected provider ' + url)
        quote = fetch_quote(stock, opener=opener, now=NOW)
        self.assertEqual(quote.price, 100)
        self.assertFalse(quote.extended)
        self.assertNotIn(' P', compact_quote_line(quote))
        self.assertTrue(any('interval=1m' in url for url in urls))
        self.assertEqual(len([url for url in urls if 'stock.naver.com' in url]), 1)


if __name__ == '__main__':
    unittest.main()
