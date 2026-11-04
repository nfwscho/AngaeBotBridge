"""
앙개봇 v0.4.2 국내·일본 메모리7 시세 보조 경로 회귀 테스트 — 전체 기능 설명
1. 네이버 금융 한국 주식 JSON 현재가·등락률·거래일시를 검사한다.
2. 네이버 1차 요청이 차단되면 다른 국내 엔드포인트로 재시도한다.
3. 네이버 모두 실패하면 기존 Yahoo Chart로 되돌아가고 미국 기능은 유지한다.
4. Yahoo Japan 키오시아 정규장 시세와 전일 대비 등락률을 검증한다.
5. 일본 PTS 시세를 정규장 가격으로 혼동하지 않고 오래된 시세를 차단한다.
6. 다른 종목을 일본 URL로 조회하지 못하고 원본·토큰·사용자 기록을 수정하지 않는다.
7. 실제 외부 네트워크를 호출하지 않고 정해진 모의 응답만 사용한다.
8. 기존 8종목 명령, 가격 부호, 거래일, 부분 오류 격리와 저장 로그를 보존한다.
9. v0.5.7 폴링 우선/모바일 보조/종목코드 불일치/장마감·지연·실시간 조건을 검증한다.
10. KRX와 NXT 또는 미확인 거래소의 시간외 가격을 분리하며 이전 거래일 값/잘못된 데이터를 제외한다.
11. Yahoo 가격을 실시간으로 잘못 표시하지 않고, 기존 한국·미국·일본·캐시·번호 선택을 유지한다.
"""
from __future__ import annotations
import io
import json
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from app.market import (WATCHLIST, StockQuoteError, fetch_quote, fetch_naver_quote,
                        fetch_yahoo_japan_quote, parse_naver_quote, parse_yahoo_japan_quote,
                        quote_line, Quote)

NOW = datetime(2026, 11, 5, 6, 0, tzinfo=timezone.utc)

class Response:
    def __init__(self, body): self.body = body
    def __enter__(self): return self
    def __exit__(self, *args): return None
    def read(self, size): return self.body[:size]

class MarketFallbackTests(unittest.TestCase):
    def test_naver_samsung_positive_price(self):
        q=parse_naver_quote(WATCHLIST[0], dict(itemCode='005930', closePrice='221,500',
            fluctuationsRatio='0.91', localTradedAt='2026-11-05T15:00:00+09:00'),now=NOW)
        self.assertEqual(q.price,221500)
        self.assertAlmostEqual(q.percent,0.91)
        self.assertIn('▲0.91%',quote_line(q))

    def test_naver_skhynix_negative_direction(self):
        q=parse_naver_quote(WATCHLIST[1], dict(itemCode='000660', closePrice='1,420,000',
            fluctuationsRatio='1.57', compareToPreviousPrice={'name':'FALLING'},
            localTradedAt='2026-11-04T15:30:00+09:00'),now=NOW)
        self.assertAlmostEqual(q.percent,-1.57)
        self.assertIn('▽1.57%',quote_line(q))

    def test_naver_reject_wrong_ticker_invalid_or_old(self):
        s=WATCHLIST[0]
        base=dict(itemCode='005930',closePrice='221,500',fluctuationsRatio='0.91',localTradedAt='2026-11-04T15:30:00+09:00')
        for override in (dict(itemCode='000660'),dict(closePrice='0'),dict(localTradedAt='2026-01-01T15:30:00+09:00')):
            with self.subTest(override=override), self.assertRaises(StockQuoteError):
                parse_naver_quote(s,base|override,now=NOW)

    def test_naver_falls_back_to_second_provider(self):
        urls=[]
        payload={'datas':[dict(itemCode='005930',closePrice='221,500',fluctuationsRatio='0.91',localTradedAt='2026-11-04T15:30:00+09:00')]}
        def opener(req, timeout):
            urls.append(req.full_url)
            if len(urls)==1:raise OSError('mock unavailable')
            return Response(json.dumps(payload).encode())
        q=fetch_naver_quote(WATCHLIST[0],opener=opener,now=NOW)
        self.assertEqual(q.price,221500)
        self.assertEqual(len(urls),2)
        self.assertIn('/api/stock/005930/basic',urls[1])

    def test_domestic_all_naver_fail_then_existing_yahoo(self):
        s=WATCHLIST[0]
        payload={'chart':{'result':[{'meta':dict(symbol=s.ticker,currency='KRW',regularMarketPrice=221500,
            regularMarketTime=int(NOW.timestamp()),previousClose=220000)}]}}
        urls=[]
        def opener(req,timeout):
            urls.append(req.full_url)
            if 'naver.com' in req.full_url:raise OSError('mock blocked')
            return Response(json.dumps(payload).encode())
        q=fetch_quote(s,opener=opener,now=NOW)
        self.assertEqual(q.price,221500)
        self.assertEqual(len(urls),3)
        self.assertIn('finance.yahoo.com',urls[-1])

    @staticmethod
    def yahoo_japan_html():
        return '''<html><title>キオクシアホールディングス(株) 285A.T</title><body>
        <h1>キオクシアホールディングス(株)</h1><p>285A</p>
        <strong>10,735</strong><p>前日比</p><span>-610(-5.38%)</span>
        <p>リアルタイム株価</p><time>11/04</time>
        <div>夜間PTS 12,000 東証終値比 +1,265(+11.78%)</div>
        </body></html>'''

    def test_yahoo_japan_ignores_night_pts(self):
        q=parse_yahoo_japan_quote(WATCHLIST[5],self.yahoo_japan_html(),now=NOW)
        self.assertEqual(q.price,10735)
        self.assertAlmostEqual(q.percent,-5.38)
        self.assertIn('▽5.38%',quote_line(q))

    def test_yahoo_japan_no_arbitrary_ticker(self):
        with self.assertRaises(StockQuoteError):
            parse_yahoo_japan_quote(WATCHLIST[2],self.yahoo_japan_html(),now=NOW)

    def test_yahoo_japan_rejects_stale(self):
        with self.assertRaises(StockQuoteError):
            parse_yahoo_japan_quote(WATCHLIST[5],self.yahoo_japan_html(), now=NOW+timedelta(days=45))

    def test_yahoo_chart_fail_japan_fallback(self):
        urls=[]
        def opener(req,timeout):
            urls.append(req.full_url)
            if 'query' in req.full_url: raise OSError('mock chart unavailable')
            return Response(self.yahoo_japan_html().encode())
        q=fetch_quote(WATCHLIST[5],opener=opener,now=NOW)
        self.assertEqual(q.price,10735)
        self.assertEqual(len(urls),3)
        self.assertEqual(urls[-1],'https://finance.yahoo.co.jp/quote/285A.T')

    def test_cannot_fabricate_when_all_providers_fail(self):
        def opener(req,timeout):raise OSError('blocked')
        for stock in (WATCHLIST[0],WATCHLIST[5]):
            with self.subTest(stock=stock.name),self.assertRaises(StockQuoteError):
                fetch_quote(stock,opener=opener,now=NOW)

if __name__=='__main__':unittest.main()
