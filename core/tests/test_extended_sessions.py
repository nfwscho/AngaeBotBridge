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
14. Yahoo 정규 종가가 차단됐을 때 KRX 당일 일봉만 정규가로 복구하고 어제 일봉은 거절하는 검증을 추가한다.
15. 네이버 공개 해외 폴링이 빈 응답이면 basic으로 복구하고 403/429일 때 동일 호스트 재시도를 금지한다.
16. Yahoo 분봉이 없는 경우에도 preMarketPrice/postMarketPrice와 체결시각 검증으로 장외 데이터를 복원한다.
17. 한국 Naver 루트 closePrice만 있는 프리/애프터 세션을 본장 종가로 오인하지 않고 별도 체결가로 표시한다.
18. 미국 네이버 루트 closePrice와 검증된 overPrice가 다를 때 명시적 장외 가격을 우선 사용한다.
19. 메모리7 기본 1행 대표세션과 7번 상세 다중행, 장외 정규장대비 비교기준을 각각 검사한다.
20. 카카오톡 간략표시의 프리/애프터 한 글자 P/A 및 9번 상세보기·9번 간략보기 전환 안내를 검증한다.
21. P/A 한 줄 시세의 삼각형과 등락률 사이 공백 제거 회귀를 검증한다.
22. 공식 신규 나스닥 상장 SPCX.O와 뉴욕증권거래소 LLY.N 네이버 해외 코드 매핑을 구별해 프리/애프터 가격을 채택한다.
23. 2026-11-06 미국 프리장 시각에서 SPCX/LLY 프리 체결이 있으면 정규장만 표시하지 않고 P를 노출한다.
24. Yahoo 정규장 차트 403으로 Nasdaq 정규가를 사용했어도 Yahoo 장외 1분봉이 정상이라면 검증 후 프리 가격을 복구한다.
25. 티커 오염·프리 체결시각 불일치·미지원 심볼에는 P를 만들지 않으며 기존 무료 공급자 장애/정규가 폴백을 보존한다.
26. 실제 네이버 NYSE 폴링은 .N으로 빈 응답, 접미사 없는 LLY/TSM/NOW로 정상 데이터를 제공하므로 Reuters 공식 RIC와 조회 코드를 구분한다.
27. NYSE bare 티커 역시 허용된 상장목록에서만 요청하고 다른 코드·전일/미래 체결을 거절하는 검증은 그대로 유지한다.
28. 한국 금요일 11/06 장후체결을 토요일 11/07 00:14에 조회할 때 KRX 일봉 기준일은 11/06, 표시 A 및 정규장 대비 %를 유지한다.
29. KRX 정규 기준가 복구가 전부 실패한 경우에도 실제 장후 A 표시는 남기고 등락률을 추측하지 않는다.
30. 주말을 넘어 월요일 정규장이 시작되면 금요일 장후 A가 새로운 현재가로 보이지 않는지 확인한다.
31. 다음금융 2026-11-06 정규 일봉 188,700/1,132,000원과 전일종가 검증 후 토요일 00:14에도 삼성/하이닉스 장후 A 상승률을 올바르게 표시한다.
32. 네이버 KRX dayCandle의 20:00 closePrice가 공식 15:30 KRX 종가와 다르면 명시적 정규장 필드가 없는 한 기준가로 복구하지 않는다.
33. Yahoo/다음금융 장애 시 실제 장외가는 보존하고 종가를 추측하지 않으며 기존 로그·시세 메뉴·미국·일본 종목은 유지한다.
"""
from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone, timedelta
from io import BytesIO
from unittest.mock import patch
from zoneinfo import ZoneInfo

from app.extended_sessions import parse_yahoo, parse_nasdaq, session_of
from app.extended_naver import parse_naver_extended, fetch_naver_extended, reuters_code
from app.market import (Stock, Quote, WATCHLIST, fetch_quote, parse_chart, parse_naver_quote,
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

    def test_yahoo_session_metadata_prices_require_explicit_trade_time(self):
        data = {'chart': {'result': [{
            'meta': {'symbol': 'MU', 'currency': 'USD',
                     'preMarketPrice': 99.25,
                     'preMarketTime': int(datetime(2026, 11, 6, 8, 15, tzinfo=ET).timestamp()),
                     'postMarketPrice': 102.50,
                     'postMarketTime': int(datetime(2026, 11, 6, 17, 5, tzinfo=ET).timestamp())}
        }]}}
        result = parse_yahoo(WATCHLIST[2], data, regular(), now=NOW)
        self.assertEqual([entry.session for entry in result], ['프리', '애프터'])
        self.assertEqual([entry.source for entry in result], ['Yahoo 메타', 'Yahoo 메타'])
        self.assertEqual([entry.price for entry in result], [99.25, 102.50])
        del data['chart']['result'][0]['meta']['postMarketTime']
        self.assertEqual([entry.session for entry in parse_yahoo(WATCHLIST[2], data, regular(), now=NOW)], ['프리'])
        data['chart']['result'][0]['meta']['preMarketTime'] = int(
            datetime(2026, 11, 5, 8, 15, tzinfo=ET).timestamp())
        self.assertFalse(parse_yahoo(WATCHLIST[2], data, regular(), now=NOW))

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
        self.assertEqual(rendered, '마이크론 $101.00 🔺+1.00% A')
        self.assertNotIn('\n', rendered)
        detail = quote_line(fetched)
        self.assertIn('[정규]', detail)
        self.assertIn('프리 $99.00', detail)
        self.assertIn('애프터 $101.00', detail)
        self.assertIn('ET', detail)

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
        raw['datas'][0]['closePrice'] = '100.00'  # 루트 가격이 본장 종가일 수 있다.
        raw['datas'][0]['localTradedAt'] = datetime(2026, 11, 6, 4, 14, tzinfo=ET).isoformat()
        verified = parse_naver_extended(WATCHLIST[2], raw, base, now=early)
        self.assertEqual(verified[0].price, 101.50)  # 명시적 overPrice 우선
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
        self.assertIn('마이크론 $101.50', compact_quote_line(fetched))
        self.assertIn(' P', compact_quote_line(fetched))
        self.assertNotIn('\n', compact_quote_line(fetched))

    def test_naver_us_basic_fallback_after_empty_polling(self):
        early = datetime(2026, 11, 6, 4, 15, tzinfo=ET)
        base = Quote(WATCHLIST[2], 100, 98, 2,
                     datetime(2026, 11, 5, 16, tzinfo=ET), early)
        payload = {'reutersCode': 'MU.O', 'marketSessionType': 'preMarket',
                   'closePrice': '101.75', 'localTradedAt': '2026-11-06T04:14:00-05:00'}
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            return _Response({'datas': []} if 'polling/' in req.full_url else payload)
        got = fetch_naver_extended(WATCHLIST[2], base, opener=opener, now=early,
                                   timeout=2.0, max_bytes=180000, user_agent='Test')
        self.assertEqual([item.price for item in got], [101.75])
        self.assertEqual(len(calls), 2)
        self.assertIn('/api/securityService/stock/MU.O/basic', calls[1])

    def test_naver_us_403_respects_rate_limit_and_regular_quote(self):
        from urllib.error import HTTPError
        early = datetime(2026, 11, 6, 4, 15, tzinfo=ET)
        base = Quote(WATCHLIST[2], 100, 98, 2,
                     datetime(2026, 11, 5, 16, tzinfo=ET), early)
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            raise HTTPError(req.full_url, 403, 'Forbidden', {}, None)
        with self.assertRaisesRegex(ValueError, 'HTTP 403'):
            fetch_naver_extended(WATCHLIST[2], base, opener=opener, now=early,
                                 timeout=2.0, max_bytes=180000, user_agent='Test')
        self.assertEqual(len(calls), 1)

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

    def test_spacex_and_eli_lilly_have_distinct_verified_reuters_codes(self):
        spcx = Stock('스페이스X', 'SPCX', 'USD', '미국', 'America/New_York')
        lly = Stock('일라이릴리', 'LLY', 'USD', '미국', 'America/New_York')
        self.assertEqual(reuters_code(spcx), 'SPCX.O')
        self.assertEqual(reuters_code(lly), 'LLY')
        self.assertEqual(reuters_code(Stock('미상', 'TESTX', 'USD', '미국',
                                          'America/New_York')), '')
        now = datetime(2026, 11, 6, 8, 19, tzinfo=ET)
        close = datetime(2026, 11, 5, 16, 0, tzinfo=ET)
        for stock, ric, previous, price, time_text in (
            (spcx, 'SPCX.O', 123.62, 128.90, '2026-11-06T04:30:00-05:00'),
            (lly, 'LLY', 1364.73, 1346.00, '2026-11-06T06:30:00-05:00'),
        ):
            with self.subTest(stock=stock.ticker):
                regular = Quote(stock, previous, previous + 12,
                                -0.5, close, now)
                body = {'datas': [{'reutersCode': ric,
                                  'currencyType': {'name': 'USD'},
                                  'marketSessionType': 'preMarket',
                                  'closePrice': str(price),
                                  'localTradedAt': time_text}]}
                result = parse_naver_extended(stock, body, regular, now=now)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].session, '프리')
                self.assertAlmostEqual(result[0].price, price)
                self.assertAlmostEqual(result[0].percent,
                                       (price / previous - 1) * 100)
                from dataclasses import replace
                rendered = compact_quote_line(replace(regular, extended=result))
                self.assertIn(' P', rendered)
                self.assertIn(stock.name, rendered)
                body['datas'][0]['reutersCode'] = ('LLY.N' if ric == 'LLY'
                                                  else 'SPCX.N')
                self.assertFalse(parse_naver_extended(stock, body, regular, now=now))

    def test_spacex_premarket_yahoo_bar_survives_regular_quote_provider_fallback(self):
        from urllib.error import HTTPError
        spcx = Stock('스페이스X', 'SPCX', 'USD', '미국', 'America/New_York')
        now = datetime(2026, 11, 6, 8, 19, tzinfo=ET)
        nasdaq = {'data': {'symbol': 'SPCX', 'assetClass': 'STOCKS',
                           'marketStatus': 'Closed',
                           'primaryData': {'lastSalePrice': '$123.62',
                                           'netChange': '-$12.30',
                                           'percentageChange': '-9.05%',
                                           'lastTradeTimestamp': 'Nov 05, 2026 04:00 PM ET'}}}
        chart = yahoo_chart(pre_price=129.46, symbol='SPCX')
        urls = []
        def opener(req, timeout):
            url = req.full_url
            urls.append(url)
            if 'api.nasdaq.com' in url:
                return _Response(nasdaq)
            if 'stock.naver.com' in url:
                return _Response({'datas': []})
            if 'interval=1m' in url:
                return _Response(chart)
            raise HTTPError(url, 403, 'Blocked regular chart only', {}, None)
        quote = fetch_quote(spcx, opener=opener, now=now)
        self.assertEqual(quote.source, '나스닥 웹')
        self.assertEqual(quote.price, 123.62)
        self.assertEqual([entry.session for entry in quote.extended], ['프리'])
        self.assertAlmostEqual(quote.extended[0].price, 129.46)
        self.assertIn('스페이스X $129.46', compact_quote_line(quote))
        self.assertIn(' P', compact_quote_line(quote))
        self.assertTrue(any('interval=1m' in url for url in urls))
        self.assertTrue(any('reutersCodes=SPCX.O' in url for url in urls))

    def test_eli_lilly_prefers_nyse_verified_trade_and_does_not_fake_missing(self):
        lly = Stock('일라이릴리', 'LLY', 'USD', '미국', 'America/New_York')
        now = datetime(2026, 11, 6, 8, 19, tzinfo=ET)
        close = datetime(2026, 11, 5, 16, 0, tzinfo=ET)
        regular = Quote(lly, 1364.73, 1417.99, -3.76, close, now)
        urls = []
        payload = {'datas': [{'reutersCode':'LLY','marketSessionType':'preMarket',
                              'currencyType': {'name':'USD'},
                              'closePrice':'1346.00',
                              'localTradedAt':'2026-11-06T06:30:00-05:00'}]}
        def opener(req, timeout):
            urls.append(req.full_url)
            return _Response(payload)
        found = fetch_naver_extended(lly, regular, opener=opener, now=now,
                                     timeout=1.8, max_bytes=180000, user_agent='Test')
        self.assertEqual(len(urls), 1)
        self.assertIn('reutersCodes=LLY', urls[0])
        self.assertAlmostEqual(found[0].percent,(1346 / 1364.73 - 1)*100)
        from dataclasses import replace
        self.assertIn('일라이릴리 $1,346', compact_quote_line(replace(regular,extended=found)))
        invalid = {'datas': [{'reutersCode':'LLY','marketSessionType':'preMarket',
                              'closePrice':'1346.00',
                              'localTradedAt':'2026-11-05T06:30:00-05:00'}]}
        self.assertFalse(parse_naver_extended(lly,invalid,regular,now=now))

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
        self.assertIn('A 기준가?', compact_quote_line(quote))
        self.assertIn('19.0만', compact_quote_line(quote))
        self.assertIn('190,000원', quote_line(quote))
        self.assertNotIn('\n', compact_quote_line(quote))
        self.assertTrue(any('yahoo' in url for url in calls))

    def test_naver_domestic_daily_candle_fallback_is_separate(self):
        korean_now = datetime(2026, 11, 6, 17, 28, tzinfo=timezone(timedelta(hours=9)))
        base = {'datas': [naver_after_payload()], 'time': '20261106172656'}
        candle = {'priceInfos': [
            {'localDate':'20261105','closePrice':201500},
            {'localDate':'20261106','closePrice':193000,
             'regularClosePrice':188600,
             'regularCloseAt':'2026-11-06T15:30:00+09:00'}
        ]}
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            if 'polling.finance' in req.full_url:
                return _Response(base)
            if 'chart/domestic/item/005930' in req.full_url:
                return _Response(candle)
            raise OSError('blocked')
        quote = fetch_quote(WATCHLIST[0], opener=opener, now=korean_now)
        self.assertEqual(quote.domestic.regular_price, 188600)
        self.assertEqual(quote.domestic.regular_source, '네이버 KRX 일봉')
        self.assertIn(' A', compact_quote_line(quote))
        self.assertIn('19.0만', compact_quote_line(quote))
        self.assertIn('190,000원', quote_line(quote))
        self.assertNotIn('\n', compact_quote_line(quote))
        self.assertTrue(any('chart/domestic/item/005930' in url for url in calls))
        from app.domestic_regular import parse_daily_regular
        self.assertIsNone(parse_daily_regular(
            WATCHLIST[0], {'priceInfos':[{'localDate':'20261105','closePrice':201500}]},
            quote, now=korean_now))

    def test_korean_regular_close_after_midnight_uses_last_market_day(self):
        from app.domestic_regular import parse_daily_regular
        kst = timezone(timedelta(hours=9))
        saturday = datetime(2026, 11, 7, 0, 14, tzinfo=kst)
        base = {'datas': [naver_after_payload()], 'time': '20261106200000'}
        candle = {'code': '005930', 'stockExchangeType': 'KRX',
                  'priceInfos': [{'localDate': '20261105', 'closePrice': 201500},
                                 {'localDate': '20261106', 'closePrice': 190000,
                                  'regularClosePrice': 188600,
                                  'regularCloseAt': '2026-11-06T15:30:00+09:00'}]}
        urls = []
        def opener(req, timeout):
            urls.append(req.full_url)
            if 'polling.finance' in req.full_url:
                return _Response(base)
            if 'chart/domestic/item/005930' in req.full_url:
                return _Response(candle)
            raise OSError('Yahoo unavailable')
        q = fetch_quote(WATCHLIST[0], opener=opener, now=saturday)
        self.assertIsNotNone(q.domestic)
        self.assertEqual(q.domestic.regular_price, 188600)
        self.assertEqual(q.domestic.regular_time.date(),
                         datetime(2026, 11, 6, tzinfo=kst).date())
        self.assertEqual(q.domestic.regular_source, '네이버 KRX 일봉')
        self.assertEqual(compact_quote_line(q), '삼성전자 19.0만 🔺+0.74% A')
        self.assertIn('190,000원', quote_line(q))
        self.assertIn('188,600원', quote_line(q))
        self.assertTrue(any('dayCandle' in url for url in urls))
        # 이후 11/07(휴장일) 일봉을 잘못 끌어오는 동작은 반드시 거부한다.
        invalid = {'priceInfos': [{'localDate': '20261107', 'closePrice': 195000}]}
        self.assertIsNone(parse_daily_regular(WATCHLIST[0], invalid, q, now=saturday))

    def test_korean_official_daum_daily_close_restores_friday_after_midnight(self):
        kst = timezone(timedelta(hours=9))
        saturday = datetime(2026, 11, 7, 0, 14, tzinfo=kst)
        for stock, observed, yesterday, day_close, regular_pct, expected in (
            (WATCHLIST[0], 190000, 201500, 188700, -6.3523573,
             '삼성전자 19.0만 🔺+0.69% A'),
            (WATCHLIST[1], 1180000, 1264000, 1132000, -10.443038,
             '하이닉스 118만 🔺+4.24% A'),
        ):
            with self.subTest(stock=stock.ticker):
                code = stock.ticker.split('.')[0]
                after_pct = (observed / yesterday - 1) * 100
                polling = {'datas': [{
                    'itemCode': code, 'closePrice': str(observed),
                    'fluctuationsRatio': str(after_pct),
                    'compareToPreviousPrice': {'name': 'FALLING'},
                    'marketStatus': 'CLOSE', 'marketSessionType': 'afterMarket',
                    'localTradedAt': '2026-11-06T20:00:00+09:00',
                }], 'time': '20261106200000'}
                records = {'data': [{
                    'symbolCode': 'A' + code, 'exchangeCountry': 'KOREA',
                    'currency': 'KRW', 'date': '2026-11-06 00:00:00',
                    'tradePrice': day_close, 'prevClosingPrice': yesterday,
                    'changeRate': regular_pct / 100,
                }]}
                calls = []
                def opener(req, timeout):
                    calls.append(req.full_url)
                    if 'polling.finance' in req.full_url:
                        return _Response(polling)
                    if 'finance.daum.net/api/quote/' in req.full_url:
                        return _Response(records)
                    raise OSError('Yahoo chart unavailable')
                q = fetch_quote(stock, opener=opener, now=saturday)
                self.assertEqual(q.domestic.regular_price, day_close)
                self.assertEqual(q.domestic.regular_source, '다음금융 정규 일봉')
                self.assertEqual(compact_quote_line(q), expected)
                self.assertIn(' A', compact_quote_line(q))
                self.assertIn('11/06 15:30', quote_line(q))
                self.assertTrue(any('finance.daum.net' in u for u in calls))
                self.assertFalse(any('chart/domestic/item' in u for u in calls))

    def test_naver_day_candle_after_market_final_not_valid_regular_close(self):
        from app.domestic_regular import parse_daily_regular
        kst = timezone(timedelta(hours=9))
        saturday = datetime(2026, 11, 7, 0, 14, tzinfo=kst)
        latest = parse_naver_quote(
            WATCHLIST[0], naver_after_payload(), now=saturday)
        self.assertIsNone(parse_daily_regular(WATCHLIST[0],
                          {'stockExchangeType': 'KRX', 'priceInfos': [
                              {'localDate':'20261106','closePrice':190000}
                          ]}, latest, now=saturday))

    def test_korean_weekend_after_quote_keeps_a_without_invented_percent(self):
        kst = timezone(timedelta(hours=9))
        saturday = datetime(2026, 11, 7, 0, 14, tzinfo=kst)
        base = {'datas': [naver_after_payload()], 'time': '20261106200000'}
        def opener(req, timeout):
            if 'polling.finance' in req.full_url:
                return _Response(base)
            raise OSError('all regular-price providers unavailable')
        q = fetch_quote(WATCHLIST[0], opener=opener, now=saturday)
        self.assertIsNone(q.domestic.regular_price)
        self.assertEqual(compact_quote_line(q), '삼성전자 19.0만 A 기준가?')
        self.assertIn('정규장 기준가 미확인', quote_line(q))

    def test_korean_last_after_expires_before_next_business_day_open(self):
        from app.domestic_regular import last_after_displayable
        kst = timezone(timedelta(hours=9))
        q = parse_naver_quote(WATCHLIST[0], naver_after_payload(),
                              now=datetime(2026, 11, 6, 20, 0, tzinfo=kst))
        after = q.domestic.after_market
        self.assertTrue(last_after_displayable(after,
                        now=datetime(2026, 11, 7, 0, 14, tzinfo=kst)))
        self.assertTrue(last_after_displayable(after,
                        now=datetime(2026, 11, 8, 23, 59, tzinfo=kst)))
        self.assertTrue(last_after_displayable(after,
                        now=datetime(2026, 11, 9, 7, 59, tzinfo=kst)))
        self.assertFalse(last_after_displayable(after,
                         now=datetime(2026, 11, 9, 8, 0, tzinfo=kst)))

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
        self.assertIn('19.0만', body)
        self.assertIn(' A', body)
        self.assertIn('188,600원', quote_line(quote))
        self.assertIn('190,000원', quote_line(quote))
        self.assertNotIn('\n', body)

    def test_korean_session_close_price_without_overmarket_field(self):
        tz = timezone(timedelta(hours=9))
        for session, hour, minute, display in (('afterMarket', 18, 10, '장후'),
                                               ('preMarket', 8, 25, '장전')):
            with self.subTest(session=session):
                now = datetime(2026, 11, 6, hour, minute, tzinfo=tz)
                raw = {'itemCode': '005930', 'closePrice': '193,500',
                       'fluctuationsRatio': '-3.97',
                       'compareToPreviousPrice': {'name': 'FALLING'},
                       'marketStatus': 'OPEN', 'marketSessionType': session,
                       'localTradedAt': now.isoformat()}
                quote = parse_naver_quote(WATCHLIST[0], raw, now=now)
                self.assertIsNotNone(quote.domestic.after_market)
                self.assertEqual(quote.domestic.after_market.session, display)
                self.assertIn('기준가?', compact_quote_line(quote))
                self.assertIn('19.4만', compact_quote_line(quote))
                self.assertIn('193,500원', quote_line(quote))
                self.assertNotIn('\n', compact_quote_line(quote))

    def test_korean_after_time_is_not_regular_trade_time(self):
        korean_now = datetime(2026, 11, 6, 17, 28, tzinfo=timezone(timedelta(hours=9)))
        stock = WATCHLIST[0]
        q = parse_naver_quote(stock, naver_after_payload(), now=korean_now,
                              provider='폴링', snapshot_time=korean_now)
        self.assertIsNotNone(q.domestic.after_market)
        self.assertEqual(q.domestic.after_market.price, 190000)
        self.assertIn('장외', quote_line(q))
        self.assertIn('거래소 미확인', quote_line(q))
        self.assertNotIn('\n', compact_quote_line(q))
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
        self.assertIn('3. 마이크론 $101.00', report)
        self.assertNotIn('   └ ', report)
        self.assertIn('8. WDC', report)
        detail = memory7_report(fetcher=supplier, use_cache=False, detailed=True)
        self.assertIn('   └ 애프터 $101.00', detail)


if __name__ == '__main__':
    unittest.main()
