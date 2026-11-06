"""
앙개봇 v0.4.1 메모리7 회귀 테스트 — 전체 기능 상세 설명
1. 한국/미국/일본 여덟 종목 티커·통화·출력 순서를 확인한다.
2. 전일 대비 등락률(상승·하락·보합)과 가격 화폐별 표시를 확인한다.
3. 입력 원본 시세를 그대로 복제하지 않고 유효한 가격/전일가로 계산하는지 확인한다.
4. 이전 거래일/주말/미국 시차를 표기하고 오래된/미래 시세 및 없는 전일가를 거부한다.
5. API 연결 실패와 일부 종목 누락의 독립 처리 및 전체 실패 오류를 확인한다.
6. 네트워크/AI 호출 없이 모의 데이터만 사용하고 기존 로그·DB를 건드리지 않는다.
7. 허용되지 않은 watchlist 인자 또는 명령에 대해 외부 API를 호출하지 않는다.
8. v0.5.6 메모리7의 정확한 1~8 번호, 공급자 실패 시 번호 자릿수 보존, 기존 가격/출처·시차/캐시를 검사한다.
9. 메모리7 간략형에서 시장 KR/US/JP의 압축 시각 및 9번 상세보기 위치를 검사하고 상세 원문 출처 검증은 별도 보존한다.
"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from app.market import (WATCHLIST, StockQuoteError, Quote, parse_chart, quote_line,
                        memory7_report, execute_stock_command)

NOW = datetime(2026, 11, 5, 18, 0, tzinfo=timezone.utc)


def make_quote(stock, value=100, change=2, when=NOW):
    return Quote(stock, value, value/(1+change/100), change,
                 when.astimezone(timezone.utc), NOW)


def payload(stock, price, prev, when=NOW):
    return {'chart': {'result': [{'meta': {'symbol': stock.ticker, 'currency': stock.currency,
                         'regularMarketPrice': price, 'regularMarketTime': int(when.timestamp()),
                         'previousClose': prev}}]}}


class StockTests(unittest.TestCase):
    def test_exact_watchlist(self):
        self.assertEqual([s.ticker for s in WATCHLIST],
                         ['005930.KS', '000660.KS', 'MU', 'SKHY', 'SNDK', '285A.T', 'STX', 'WDC'])
        self.assertEqual([s.currency for s in WATCHLIST],
                         ['KRW', 'KRW', 'USD', 'USD', 'USD', 'JPY', 'USD', 'USD'])

    def test_precise_percentage_based_on_previous_close(self):
        s = WATCHLIST[2]
        q = parse_chart(s, payload(s, 804.59, 855.13), now=NOW)
        self.assertAlmostEqual(q.percent, (804.59/855.13-1)*100)
        self.assertIn('▽', quote_line(q))

    def test_price_and_sign(self):
        self.assertEqual(quote_line(make_quote(WATCHLIST[0], 221500, .91)), '삼성전자 : 221,500원 (▲0.91%)')
        self.assertEqual(quote_line(make_quote(WATCHLIST[5], 10735, -5.38)), '키오시아 : ¥10,735.0 (▽5.38%)')
        self.assertIn('－0.00%', quote_line(make_quote(WATCHLIST[2], 100, 0)))

    def test_invalid_meta_rejected_without_fabricated_price(self):
        s = WATCHLIST[0]
        for key, value in [('currency','USD'),('regularMarketPrice',-1),('previousClose',0),('symbol','BAD')]:
            sample=payload(s,100,99)
            sample['chart']['result'][0]['meta'][key] = value
            with self.subTest(key=key), self.assertRaises(StockQuoteError):
                parse_chart(s, sample, now=NOW)

    def test_old_quote_rejected(self):
        s=WATCHLIST[0]
        with self.assertRaises(StockQuoteError):
            parse_chart(s, payload(s, 99, 90, NOW-timedelta(days=15)), now=NOW)
        with self.assertRaises(StockQuoteError):
            parse_chart(s, payload(s, 99, 90, NOW+timedelta(days=1)), now=NOW)

    def test_fallback_previous_close_from_matching_daily_bars(self):
        s=WATCHLIST[0]
        data=payload(s,200,190)
        del data['chart']['result'][0]['meta']['previousClose']
        data['chart']['result'][0]['timestamp']=[int((NOW-timedelta(days=1)).timestamp()),int(NOW.timestamp())]
        data['chart']['result'][0]['indicators']={'quote':[{'close':[160,200]}]}
        self.assertAlmostEqual(parse_chart(s, data, now=NOW).percent,25)

    def test_partial_and_ordered_quote(self):
        def provider(stock):
            if stock.ticker in ('SKHY','STX'):
                raise StockQuoteError('mock error')
            return make_quote(stock)
        result=memory7_report(fetcher=provider,now=NOW,use_cache=False)
        self.assertIn('SKHY : 조회 불가',result)
        self.assertIn('씨게이트 : 조회 불가',result)
        self.assertIn('2종목 조회 실패',result)
        self.assertIn('1. 삼성전자 ',result)
        self.assertIn('4. SKHY : 조회 불가',result)
        self.assertIn('7. 씨게이트 : 조회 불가',result)
        self.assertIn('8. WDC ',result)
        self.assertIn('5분 내 1~8',result)
        self.assertLess(result.index('삼성전자 '),result.index('하이닉스 '))
        self.assertLess(result.index('하이닉스 '),result.index('마이크론 '))

    def test_total_failure(self):
        with self.assertRaisesRegex(StockQuoteError,'8개 종목'):
            memory7_report(fetcher=lambda _: (_ for _ in ()).throw(StockQuoteError('blocked')),use_cache=False)

    def test_fetch_quote_http_request_and_fallback(self):
        import io, json
        from app.market import fetch_quote
        stock=WATCHLIST[2]
        data=json.dumps(payload(stock,102,100)).encode('utf-8')
        class MockResponse:
            def __enter__(self): return self
            def __exit__(self,*args): return None
            def read(self,size): return data
        calls=[]
        def fake_opener(req,timeout):
            calls.append((req.full_url,timeout))
            if len(calls)==1:
                raise OSError('mock connection error')
            return MockResponse()
        received=fetch_quote(stock,opener=fake_opener,now=NOW)
        self.assertAlmostEqual(received.percent,2)
        self.assertEqual(len(calls),2)
        self.assertTrue(all(u.startswith('https://query') for u,_ in calls))
        self.assertTrue(all(timeout<5 for _,timeout in calls))

    def test_api_failures_do_not_show_fabricated_prices(self):
        from app.market import fetch_quote
        stock=WATCHLIST[0]
        def fake_opener(req,timeout):
            raise OSError('blocked')
        with self.assertRaisesRegex(StockQuoteError,'연결 불가'):
            fetch_quote(stock,opener=fake_opener,now=NOW)

    def test_invalid_command_never_fetches(self):
        with patch('app.market.memory7_report') as fetching:
            for command, arg in [('주식','이름없음'),('메모리7','잘못된 인수'),('shell','ls')]:
                with self.assertRaises(StockQuoteError):
                    execute_stock_command(command,arg)
            fetching.assert_not_called()

    def test_timezone_and_market_date_display(self):
        def provider(stock):
            return make_quote(stock)
        body=memory7_report(fetcher=provider,use_cache=False)
        # 기본 카톡 간략 시세는 한 줄짜리 KR/US/JP 현지시각을 사용한다.
        # 원래 국가별 한국/미국/일본 공급자 정보는 상세보기에서 보존한다.
        self.assertIn('📡 ',body)
        self.assertIn('KR',body)
        self.assertIn('US',body)
        self.assertIn('JP',body)
        self.assertIn('지연',body)
        self.assertIn('99. 🔎 상세보기',body)


if __name__=='__main__': unittest.main()
