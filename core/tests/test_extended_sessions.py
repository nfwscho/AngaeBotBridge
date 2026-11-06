"""
앙개봇 프리/정규/애프터 시세 회귀 테스트 — 전체 테스트 기능
1. Yahoo 1분봉에서 동일 거래일 프리/애프터 실제 거래량 확인 시 각각 다른 가격을 읽는다.
2. 각 세션 등락률 기준은 프리=직전 정규 종가, 애프터=당일 정규장 가격으로 검증한다.
3. 잘못된 티커·통화·미래/전일 분봉·거래량 없는 분봉·정규장 분봉은 거부한다.
4. Nasdaq 공개 보조 세션은 장상태·시간·티커 검증 후에만 채택한다.
5. Yahoo 정규 시세 조회와 1분봉 장외 조회의 실제 함수 연결을 모의 HTTP로 검사한다.
6. 국내 네이버 동일 응답 갱신시각이 정규/장외 필드에 들어와도 유효한 장외 체결을 보존한다.
7. 한국 장외 응답을 KRX 본장 실시간으로 오인하지 않으며 거래소 미확인은 그대로 노출한다.
8. 메모리7·관심그룹 목록의 세션별 가격, 기존 번호/요약/로그 구조 보존을 확인한다.
9. 추가 네트워크 호출 없이 시각과 응답을 주입해 실행한다.
10. 미국 네이버 해외 폴링과 basic 응답의 .O 티커·USD·프리/애프터 세션·날짜·시각 검증을 추가한다.
11. Yahoo/나스닥 기존 복구 테스트는 네이버 경로를 모의 비활성화하고 원래 호출 흐름을 검증한다.
12. 네이버 해외 프리장 결과가 확인되면 Yahoo 추가 조회 없이 해당 체결가를 표시하는 실제 연결을 검증한다.
13. 네이버 국내 장외 closePrice를 KRX 종가로 표시하지 않고 Yahoo 정규가가 명시 확인된 때만 분리한다.
"""
from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone, timedelta
from io import BytesIO
from unittest.mock import patch
from zoneinfo import ZoneInfo

from app.extended_sessions import parse_yahoo, parse_nasdaq, session_of
from app.extended_naver import parse_naver_extended, fetch_naver_extended
from app.market import (Quote, WATCHLIST, fetch_quote, parse_chart, parse_naver_quote,
                        parse_nasdaq_quote, compact_quote_line, quote_line, memory7_report)

ET = ZoneInfo('America/New_York')
REG = datetime(2026, 11, 6, 15, 59, tzinfo=ET)
NOW = datetime(2026, 11, 6, 17, 10, tzinfo=ET)


def regular():
    stock = WATCHLIST[2]
    return Quote(stock, 100.0, 98.0, (100 / 98 - 1) * 100, REG, NOW)


def yahoo_chart(pre_price=99.0, aft_price=101.0, symbol='MU', volume=100):
    pre = datetime(2026, 11, 6, 8, 15, tzinfo=ET)
    midday = datetime(2026, 11, 6, 12, 15, tzinfo=ET)
    aft = datetime(2026, 11, 6, 17, 5, tzinfo=ET)
    return {'chart': {'result': [{
        'meta': {'currency': 'USD', 'symbol': symbol},
        'timestamp': [int(d.timestamp()) for d in (pre, midday, aft)],
        'indicators': {'quote': [{'close': [pre_price, 100.0, aft_price],
                                   'volume': [volume, volume, volume]}]},
    }]}}


def naver_after_payload():
    return {
        'itemCode': '005930',
        'closePrice': '190,100', 'fluctuationsRatio': '-5.66',
        'compareToPreviousPrice': {'name': 'FALLING'},
        'marketStatus': 'OPEN', 'marketSessionType': 'afterMarket',
        'localTradedAt': '2026-11-06T17:26:56.316571+09:00',
        'overMarketPriceInfo': {
            'tradingSessionType': 'AFTER_MARKET', 'overMarketStatus': 'OPEN',
            'overPrice': '190,000', 'fluctuationsRatio': '-5.71',
            'compareToPreviousPrice': {'name': 'FALLING'},
            # 기존 코드는 정규 가격의 갱신 시각과 비교해 이 정상 체결가를 누락함.
            'localTradedAt': '2026-11-06T17:26:56.316500+09:00',
        }
    }


class _Response:
    def __init__(self, payload):
        self.data = json.dumps(payload).encode('utf-8')
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return None
    def read(self, _):
        return self.data


class ExtendedSessionTests(unittest.TestCase):
    def test_market_sessions_use_new_york_dst_timezone(self):
        self.assertEqual(session_of(datetime(2026, 7, 6, 4, 0, tzinfo=ET)), '프리')
        self.assertEqual(session_of(datetime(2026, 11, 6, 9, 30, tzinfo=ET)), '')
        self.assertEqual(session_of(datetime(2026, 11, 6, 16, 0, tzinfo=ET)), '애프터')
        self.assertEqual(session_of(datetime(2026, 11, 7, 17, 0, tzinfo=ET)), '')

    def test_yahoo_distinct_pre_and_after_vs_correct_reference(self):
        found = parse_yahoo(WATCHLIST[2], yahoo_chart(), regular(), now=NOW)
        self.assertEqual([r.session for r in found], ['프리', '애프터'])
        self.assertAlmostEqual(found[0].percent, (99 / 98 - 1) * 100)
        self.assertAlmostEqual(found[1].percent, 1.0)
        self.assertEqual(found[1].market_time.hour, 17)

    def test_reject_wrong_symbol_volume_future_and_previous_day(self):
        self.assertEqual(parse_yahoo(WATCHLIST[2], yahoo_chart(symbol='AAPL'), regular(), now=NOW), ())
        self.assertEqual(parse_yahoo(WATCHLIST[2], yahoo_chart(volume=0), regular(), now=NOW), ())
        old = yahoo_chart()
        old['chart']['result'][0]['timestamp'] = [
            int((datetime(2026, 11, 5, 17, 0, tzinfo=ET) + timedelta(minutes=i)).timestamp())
            for i in range(3)]
        self.assertEqual(parse_yahoo(WATCHLIST[2], old, regular(), now=NOW), ())
        self.assertEqual(parse_yahoo(WATCHLIST[2], yahoo_chart(), regular(),
                                     now=NOW - timedelta(days=1)), ())

    def test_nasdaq_secondary_only_in_explicit_market_session(self):
        record = {
            'symbol': 'MU', 'assetClass': 'STOCKS', 'marketStatus': 'After-Hours',
            'primaryData': {'lastSalePrice': '$100.00', 'netChange': '$2.00',
                            'percentageChange': '2.04%',
                            'lastTradeTimestamp': 'Nov 06, 2026 03:59 PM ET'},
            'secondaryData': {'lastSalePrice': '$101.50',
                              'lastTradeTimestamp': 'Nov 06, 2026 05:04 PM ET'}
        }
        quote = parse_nasdaq_quote(WATCHLIST[2], {'data': record}, now=NOW)
        self.assertEqual(quote.extended[0].session, '애프터')
        self.assertAlmostEqual(quote.extended[0].percent, 1.5)
        record['marketStatus'] = 'Closed'
        self.assertFalse(parse_nasdaq_quote(WATCHLIST[2], {'data': record}, now=NOW).extended)
        record['marketStatus'] = 'After-Hours'
        record['secondaryData']['lastTradeTimestamp'] = 'Nov 06, 2026 02:04 PM ET'
        self.assertFalse(parse_nasdaq_quote(WATCHLIST[2], {'data': record}, now=NOW).extended)

    def test_yahoo_fetch_keeps_original_regular_quote(self):
        r = regular()
        daily = {'chart': {'result': [{'meta': {
            'symbol': 'MU', 'currency': 'USD', 'regularMarketPrice': r.price,
            'regularMarketTime': int(REG.timestamp()), 'previousClose': 98.0}}]}}
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            return _Response(yahoo_chart() if 'interval=1m' in req.full_url else daily)
        with patch('app.extended_naver.fetch_naver_extended', return_value=()):
            fetched = fetch_quote(WATCHLIST[2], opener=opener, now=NOW)
        self.assertEqual(fetched.price, 100.0)
        self.assertEqual([x.session for x in fetched.extended], ['프리', '애프터'])
        self.assertEqual(len(calls), 2)
        self.assertIn('includePrePost=true', calls[1])
        rendered = compact_quote_line(fetched)
        self.assertIn('[정규]', rendered)
        self.assertIn('프리 $99.00', rendered)
        self.assertIn('애프터 $101.00', rendered)
        self.assertIn('ET', quote_line(fetched))

    def test_nasdaq_fills_current_after_when_yahoo_only_has_pre(self):
        r = regular()
        daily = {'chart': {'result': [{'meta': {
            'symbol': 'MU', 'currency': 'USD', 'regularMarketPrice': r.price,
            'regularMarketTime': int(REG.timestamp()), 'previousClose': 98.0}}]}}
        intraday = yahoo_chart(volume=100)
        intraday['chart']['result'][0]['indicators']['quote'][0]['volume'] = [100, 100, 0]
        nasdaq = {'data': {
            'symbol': 'MU', 'assetClass': 'STOCKS', 'marketStatus': 'After-Hours',
            'primaryData': {'lastSalePrice': '$100.00', 'netChange': '$2.00',
                            'percentageChange': '2.04%',
                            'lastTradeTimestamp': 'Nov 06, 2026 03:59 PM ET'},
            'secondaryData': {'lastSalePrice': '$101.50',
                              'lastTradeTimestamp': 'Nov 06, 2026 05:04 PM ET'}
        }}
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            if 'api.nasdaq.com' in req.full_url:
                return _Response(nasdaq)
            if 'interval=1m' in req.full_url:
                return _Response(intraday)
            return _Response(daily)
        with patch('app.extended_naver.fetch_naver_extended', return_value=()):
            quote = fetch_quote(WATCHLIST[2], opener=opener, now=NOW)
        self.assertEqual([x.session for x in quote.extended], ['프리', '애프터'])
        self.assertEqual(quote.extended[1].source, '나스닥 웹')
        self.assertAlmostEqual(quote.extended[1].price, 101.50)
        self.assertEqual(len(calls), 3)

    def test_naver_us_premarket_session_from_polled_payload(self):
        early = datetime(2026, 11, 6, 4, 15, tzinfo=ET)
        previous = datetime(2026, 11, 5, 16, 0, tzinfo=ET)
        base = Quote(WATCHLIST[2], 100.0, 98.0, 2.04, previous, early)
        stamp = datetime(2026, 11, 6, 4, 12, tzinfo=ET).isoformat()
        raw = {'pollingInterval': 7000, 'datas': [{
            'reutersCode': 'MU.O', 'currencyType': {'name': 'USD'},
            'marketSessionType': 'preMarket', 'closePrice': '101.50', 'localTradedAt': stamp,
            'overMarketPriceInfo': {'tradingSessionType': 'PRE_MARKET',
                                    'overPrice': '101.50', 'localTradedAt': stamp}
        }]}
        found = parse_naver_extended(WATCHLIST[2], raw, base, now=early)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].session, '프리')
        self.assertEqual(found[0].source, '네이버 해외')
        self.assertAlmostEqual(found[0].price, 101.50)
        self.assertAlmostEqual(found[0].percent, 1.5)
        self.assertEqual(parse_naver_extended(WATCHLIST[3], raw, base, now=early), ())
        broken = json.loads(json.dumps(raw))
        broken['datas'][0]['localTradedAt'] = '2026-11-05T16:00:00-05:00'
        broken['datas'][0]['overMarketPriceInfo']['localTradedAt'] = broken['datas'][0]['localTradedAt']
        self.assertFalse(parse_naver_extended(WATCHLIST[2], broken, base, now=early))

    def test_naver_us_premarket_fetch_prevents_yahoo_after_failure(self):
        early = datetime(2026, 11, 6, 4, 15, tzinfo=ET)
        previous = datetime(2026, 11, 5, 16, 0, tzinfo=ET)
        daily = {'chart': {'result': [{'meta': {
            'symbol': 'MU', 'currency': 'USD', 'regularMarketPrice': 100.0,
            'regularMarketTime': int(previous.timestamp()), 'previousClose': 98.0}}]}}
        payload = {'datas': [{'reutersCode':'MU.O', 'marketSessionType': 'preMarket',
                             'closePrice':'101.50', 'localTradedAt': '2026-11-06T04:12:00-05:00',
                             'currencyType': {'name': 'USD'}}]}
        urls = []
        def opener(req, timeout):
            urls.append(req.full_url)
            return _Response(payload if 'stock.naver.com' in req.full_url else daily)
        fetched = fetch_quote(WATCHLIST[2], opener=opener, now=early)
        self.assertEqual(len(urls), 2)
        self.assertIn('reutersCodes=MU.O', urls[1])
        self.assertEqual(fetched.price, 100.0)
        self.assertEqual(fetched.extended[0].session, '프리')
        self.assertIn('프리 $101.50', compact_quote_line(fetched))

    def test_naver_us_rejects_wrong_or_unverified_inputs(self):
        early = datetime(2026, 11, 6, 4, 15, tzinfo=ET)
        reg = Quote(WATCHLIST[2], 100, 98, 2, datetime(2026, 11, 5, 16, tzinfo=ET), early)
        item = {'reutersCode':'MU.O', 'marketSessionType':'preMarket',
                'closePrice':'101.50', 'localTradedAt':'2026-11-06T04:13:00-05:00'}
        for mutate in ({'reutersCode':'AAPL.O'},
                       {'currency':'KRW'}, {'closePrice':'0'},
                       {'localTradedAt':'2026-11-06T15:00:00-05:00'},
                       {'localTradedAt':'2026-11-06T09:31:00-05:00'}):
            with self.subTest(mutate=mutate):
                self.assertEqual(parse_naver_extended(WATCHLIST[2], {'datas':[item | mutate]},
                                                      reg, now=early), ())
        self.assertEqual(parse_naver_extended(WATCHLIST[2], {'datas':[{
            k:v for k,v in item.items() if k != 'marketSessionType'}]}, reg, now=early), ())

    def test_naver_domestic_after_price_never_assumed_regular_close(self):
        korean_now = datetime(2026, 11, 6, 17, 28, tzinfo=timezone(timedelta(hours=9)))
        base = {'datas': [naver_after_payload()], 'time': '20261106172656'}
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            if 'polling.finance' in req.full_url:
                return _Response(base)
            raise OSError('Yahoo not available')
        from app.market import StockQuoteError
        quote = fetch_quote(WATCHLIST[0], opener=opener, now=korean_now)
        self.assertIn('정규장 종가 미확인', compact_quote_line(quote))
        self.assertIn('190,000원', compact_quote_line(quote))
        self.assertNotIn('[정규]', compact_quote_line(quote))
        self.assertTrue(any('yahoo' in url for url in calls))

    def test_naver_domestic_regular_verified_from_separate_yahoo(self):
        korean_now = datetime(2026, 11, 6, 17, 28, tzinfo=timezone(timedelta(hours=9)))
        base = {'datas': [naver_after_payload()], 'time': '20261106172656'}
        market_close = datetime(2026, 11, 6, 15, 30, tzinfo=timezone(timedelta(hours=9)))
        daily = {'chart': {'result': [{'meta': {
            'symbol': '005930.KS', 'currency': 'KRW', 'regularMarketPrice': 188600,
            'regularMarketTime': int(market_close.timestamp()), 'previousClose': 201500}}]}}
        def opener(req, timeout):
            return _Response(base if 'polling.finance' in req.full_url else daily)
        quote = fetch_quote(WATCHLIST[0], opener=opener, now=korean_now)
        self.assertEqual(quote.domestic.regular_price, 188600)
        body = compact_quote_line(quote)
        self.assertIn('18.9만', body)
        self.assertIn('190,000원', body)
        self.assertIn('[정규·별도 확인]', body)

    def test_korean_after_time_is_not_regular_trade_time(self):
        korean_now = datetime(2026, 11, 6, 17, 28, tzinfo=timezone(timedelta(hours=9)))
        stock = WATCHLIST[0]
        q = parse_naver_quote(stock, naver_after_payload(), now=korean_now,
                              provider='폴링', snapshot_time=korean_now)
        self.assertIsNotNone(q.domestic.after_market)
        self.assertEqual(q.domestic.after_market.price, 190000)
        self.assertIn('장외', compact_quote_line(q) if '장외' in compact_quote_line(q)
                      else quote_line(q))
        self.assertIn('거래소 미확인', compact_quote_line(q))
        from app.market import _domestic_status_label
        self.assertNotIn('네이버 실시간표시', _domestic_status_label(q))

    def test_memory7_has_visible_extended_but_same_numbering(self):
        extended = parse_yahoo(WATCHLIST[2], yahoo_chart(), regular(), now=NOW)
        from dataclasses import replace
        def supplier(stock):
            value = regular()
            value = replace(value, stock=stock)
            return replace(value, extended=extended) if stock.ticker == 'MU' else value
        report = memory7_report(fetcher=supplier, use_cache=False)
        self.assertIn('3. 마이크론', report)
        self.assertIn('   └ 애프터 $101.00', report)
        self.assertIn('8. WDC', report)


if __name__ == '__main__':
    unittest.main()
