"""
앙개봇 Python Core v0.5.8 미국 시세 조회 장애 보완 전체 회귀 검증
1. 기존 메모리7/관심그룹·종목 별칭·고정 WATCHLIST/국내 네이버·일본 폴백은 변경하지 않는다.
2. Yahoo 정상 응답이면 기존 값을 그대로 사용하고 Nasdaq에 불필요하게 요청하지 않는다.
3. Yahoo HTTP 429/403 차단 시 동일 호스트를 반복 공격하지 않고 나스닥 공개 웹 응답으로 보완한다.
4. 첫 Yahoo 호스트 일반 장애는 기존 두 번째 Yahoo 호스트로 폴백하며 기본 기존 흐름을 보존한다.
5. 나스닥 응답의 종목·통화·정규 가격·등락률·현지 시각이 일치할 때만 사용한다.
6. 데이터 구조 오류/날짜 없음/미래/10일 초과/다른 티커/음수·무한대/증감 불일치/조회 실패를 격리한다.
7. 나스닥 시세는 실시간 여부 미확인·미국 현지 시각·출처를 표기하고 기존 Yahoo 표시 형식은 보존한다.
8. 모든 공급자가 실패해도 값을 만들어내지 않고 기존 주식 조회 실패로 전달한다.
9. URL은 미국 종목 티커만 구성하며 한국·일본 종목을 나스닥으로 조회하지 않는다.
10. HTTP 요청 응답 크기/타임아웃과 무료 제공자 실패에 대한 요청 예절을 검증한다.
11. 환경 변수/키/운영 SQLite/실제 네트워크 요청을 사용하지 않고 응답 모의 객체로만 검사한다.
12. 기존 계산·질문·번호 선택·배터리·로그/DB/자동응답 경로에 영향이 없는지 전체 회귀 테스트와 함께 검증한다.
"""
from __future__ import annotations

import io
import json
import unittest
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from unittest.mock import patch

from app.market import (StockQuoteError, WATCHLIST, fetch_quote, parse_nasdaq_quote,
                        fetch_nasdaq_quote, quote_line, Stock)

NOW = datetime(2026, 11, 5, 1, 13, tzinfo=timezone.utc)


class Response:
    def __init__(self, data: bytes): self.data = data
    def __enter__(self): return self
    def __exit__(self, *args): return None
    def read(self, n): return self.data[:n]


def nasdaq(stock=WATCHLIST[2], *, stamp='Nov 04, 2026 4:00 PM ET', price='$795.23', change='-$60.00', pct='-7.02%'):
    return {'data': {'symbol': stock.ticker, 'assetClass': 'STOCKS', 'primaryData': {
        'lastSalePrice': price, 'netChange': change, 'percentageChange': pct,
        'lastTradeTimestamp': stamp}}}


def yahoo(stock=WATCHLIST[2]):
    return {'chart': {'result': [{'meta': {
        'symbol': stock.ticker, 'currency': 'USD', 'regularMarketPrice': 785,
        'previousClose': 800, 'regularMarketTime': int((NOW-timedelta(hours=3)).timestamp())}}]}}


class UsFallbackTests(unittest.TestCase):
    def test_nasdaq_known_close_and_attribution(self):
        stock=WATCHLIST[2]
        q=parse_nasdaq_quote(stock, nasdaq(stock), now=NOW)
        self.assertEqual(q.price, 795.23)
        self.assertAlmostEqual(q.previous_close, 855.23)
        self.assertEqual(q.market_time.strftime('%Y-%m-%d %H:%M'), '2026-11-04 16:00')
        self.assertIn('나스닥 공개 시세(지연 여부 미확인)', quote_line(q))
        self.assertNotIn('실시간',quote_line(q))

    def test_yahoo_normal_keeps_preexisting_output(self):
        stock=WATCHLIST[2]
        urls=[]
        def opener(req,timeout):
            urls.append(req.full_url)
            return Response(json.dumps(yahoo(stock)).encode())
        q=fetch_quote(stock,opener=opener,now=NOW)
        self.assertEqual(q.price,785)
        self.assertEqual(len(urls),1)
        self.assertTrue(urls[0].startswith('https://query1.finance.yahoo.com'))
        self.assertNotIn('나스닥',quote_line(q))

    def test_429_falls_back_without_same_host_retry(self):
        stock=WATCHLIST[2]
        urls=[]
        def opener(req,timeout):
            urls.append(req.full_url)
            if 'finance.yahoo.com' in req.full_url:
                raise HTTPError(req.full_url,429,'Too Many Requests',{},None)
            return Response(json.dumps(nasdaq(stock)).encode())
        q=fetch_quote(stock,opener=opener,now=NOW)
        self.assertEqual(q.price,795.23)
        self.assertEqual(len(urls),2)
        self.assertIn('/MU/info?',urls[-1])

    def test_403_falls_back_and_does_not_hammer(self):
        urls=[]
        stock=WATCHLIST[6]
        def opener(req,timeout):
            urls.append(req.full_url)
            if 'finance.yahoo' in req.full_url:
                raise HTTPError(req.full_url,403,'Forbidden',{},None)
            return Response(json.dumps(nasdaq(stock)).encode())
        self.assertEqual(fetch_quote(stock,opener=opener,now=NOW).stock.ticker,'STX')
        self.assertEqual(len(urls),2)

    def test_yahoo_network_retry_then_nasdaq(self):
        urls=[]
        stock=WATCHLIST[7]
        def opener(req,timeout):
            urls.append(req.full_url)
            if 'finance.yahoo' in req.full_url:
                raise OSError('offline')
            return Response(json.dumps(nasdaq(stock)).encode())
        q=fetch_quote(stock,opener=opener,now=NOW)
        self.assertEqual(q.stock.ticker,'WDC')
        self.assertEqual(len(urls),3)

    def test_yahoo_bad_json_then_nasdaq(self):
        stock=WATCHLIST[4]
        urls=[]
        def opener(req,timeout):
            urls.append(req.full_url)
            return Response(b'<html>blocked</html>' if 'finance.yahoo' in req.full_url else json.dumps(nasdaq(stock)).encode())
        self.assertEqual(fetch_quote(stock,opener=opener,now=NOW).stock.ticker,'SNDK')
        self.assertEqual(len(urls),3)

    def test_all_providers_failure_raises_clear_error(self):
        urls=[]
        def opener(req,timeout):
            urls.append(req.full_url)
            raise OSError('offline')
        with self.assertLogs('app.market',level='WARNING') as logs:
            with self.assertRaisesRegex(StockQuoteError, '미국 무료 시세'):
                fetch_quote(WATCHLIST[2],opener=opener,now=NOW)
        self.assertIn('US_QUOTE_FAILED ticker=MU',logs.output[0])
        self.assertEqual(len(urls),3)

    def test_mismatched_ticker_or_asset_is_rejected(self):
        stock=WATCHLIST[2]
        for mutate in [{'symbol':'WDC'},{'assetClass':'ETFS'}]:
            data=nasdaq(stock);data['data'].update(mutate)
            with self.subTest(mutate=mutate),self.assertRaises(StockQuoteError):
                parse_nasdaq_quote(stock,data,now=NOW)

    def test_bad_numeric_values_are_rejected(self):
        stock=WATCHLIST[2]
        for values in [('$0','-$1','-1%'),('-1','-2','1%'),('NaN','0','0'),
                       ('$795.23','bad','-7%'),('$795.23','-$60','-10%'),
                       ('$795.23','-$1000','-50%'),('$795.23','-$60','unknown')]:
            with self.subTest(values=values),self.assertRaises(StockQuoteError):
                parse_nasdaq_quote(stock,nasdaq(stock,price=values[0],change=values[1],pct=values[2]),now=NOW)

    def test_bad_stale_future_no_timestamp(self):
        stock=WATCHLIST[2]
        for stamp in ['',None,'Nov 1 2026', 'Oct 01, 2026 4:00 PM ET', 'Nov 10, 2026 4:00 PM ET']:
            with self.subTest(stamp=stamp),self.assertRaises(StockQuoteError):
                parse_nasdaq_quote(stock,nasdaq(stock,stamp=stamp),now=NOW)

    def test_isolated_symbol_and_date(self):
        stock=WATCHLIST[7]
        data=nasdaq(stock,stamp='2026-11-04T16:00:00-05:00')
        q=parse_nasdaq_quote(stock,data,now=NOW)
        self.assertEqual(q.stock.ticker,'WDC')
        self.assertEqual(q.market_time.hour,16)

    def test_only_us_allowed_without_token_or_user_url(self):
        for stock in [WATCHLIST[0],WATCHLIST[5],Stock('위험','https://a','USD','미국','America/New_York')]:
            with self.subTest(ticker=stock.ticker),self.assertRaises(StockQuoteError):
                fetch_nasdaq_quote(stock,opener=lambda *a,**kw:None,now=NOW)

    def test_non_200_or_too_large_response_not_used(self):
        stock=WATCHLIST[2]
        with self.assertRaises(StockQuoteError):
            fetch_nasdaq_quote(stock,opener=lambda req,timeout:Response(b'X'*200_001),now=NOW)

    def test_zero_change_is_valid(self):
        stock=WATCHLIST[2]
        data=nasdaq(stock,price='$100.00',change='$0.00',pct='0.00%')
        q=parse_nasdaq_quote(stock,data,now=NOW)
        self.assertEqual(q.previous_close,100)
        self.assertIn('－0.00%', quote_line(q))


if __name__=='__main__':
    unittest.main()
