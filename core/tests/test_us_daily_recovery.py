"""
앙개봇 Python Core v0.5.10 미국 시세 재발 방지 및 일봉 복구 회귀 테스트 — 전체 기능 명세
1. 미국 Yahoo/나스닥 현재가가 HTTP 403·429·유효성 오류로 실패해도 나스닥 확정 일봉 2개로 보완한다.
2. 나스닥 일봉 API가 실패하면 독립된 네이버 해외 주식 차트의 최근 확정 일봉 2개로 보완한다.
3. 마이크론(MU), 샌디스크(SNDK), 웨스턴디지털(WDC), 씨게이트(STX) 등 고정된 나스닥 상장 티커만 사용한다.
4. 최근 확정 거래일 종가, 이전 실제 거래일 종가, 전일 대비 %, 미국 동부 거래시각을 검증한다.
5. 2026-11-04 미국 정규장 종료 후 KST 오전 데이터는 실시간이 아닌 최근 정규장 종가로 명확히 표시한다.
6. 장중 미확정 당일 일봉은 거부하며 가격·날짜·티커 불일치, 한 개 일봉, 오래된 데이터, 위장 응답을 모두 거부한다.
7. 원래 Yahoo 정상 경로는 변함없고 한국 네이버·키오시아 일본 경로는 미국 보조 URL에 접근하지 않는다.
8. 기존 메모리7·사용자 그룹의 번호 선택과 출력/출처 요약, 배터리 표시 및 모든 SQLite/AI 로그를 유지한다.
9. 실제 네트워크·개인 DB·키·카카오톡 없이 인젝션된 HTTP 모의 응답으로 호출 순서/오류/복구를 검증한다.
10. 마지막 공급자까지 실패해도 가짜 값을 표시하지 않으며 기존 US_QUOTE_FAILED 진단 로그를 유지한다.
11. 새로운 Android 권한/앱 재설치/유료 API·주기적 감시/매매/예약 실행을 추가하지 않는다.
"""
from __future__ import annotations
import json
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from urllib.error import HTTPError

from app.market import (WATCHLIST, StockQuoteError, fetch_quote,
                        fetch_nasdaq_daily_quote, fetch_naver_us_daily_quote,
                        parse_nasdaq_daily_quote, parse_naver_us_daily_quote,
                        market_source_summary, quote_line)

NOW = datetime(2026,11,5,2,8,tzinfo=timezone.utc)  # KST 11:08, NY 11/04 21:08

class Response:
    def __init__(self, obj): self.raw=json.dumps(obj).encode()
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,sz): return self.raw[:sz]

def nasdaq_daily(stock=WATCHLIST[2]):
    return {'data': {'symbol': stock.ticker, 'tradesTable': {'rows': [
        {'date':'11/04/2026','close':'$776.15','volume':'14,100'},
        {'date':'11/03/2026','close':'$795.23','volume':'21,000'},
        {'date':'11/02/2026','close':'$804.22','volume':'30,000'},
    ]}}}

def naver_daily(stock=WATCHLIST[2]):
    return {'reutersCode':stock.ticker+'.O','priceInfos':[
        {'localDate':'20261104','closePrice':776.15},
        {'localDate':'20261103','closePrice':795.23},
        {'localDate':'20261102','closePrice':804.22},
    ]}

class UsDailyRecoveryTests(unittest.TestCase):
    def test_nasdaq_historical_last_two_finalized_closes(self):
        s=WATCHLIST[2]
        q=parse_nasdaq_daily_quote(s,nasdaq_daily(s),now=NOW)
        self.assertEqual(q.price,776.15)
        self.assertEqual(q.previous_close,795.23)
        self.assertAlmostEqual(q.percent,(776.15/795.23-1)*100)
        self.assertEqual(q.market_time.strftime('%Y-%m-%d %H:%M'),'2026-11-04 16:00')
        self.assertEqual(q.source,'나스닥 확정 종가')
        self.assertIn('실시간 아님',quote_line(q))
        summary='\n'.join(market_source_summary([q]))
        self.assertIn('나스닥 확정 종가',summary)
        self.assertIn('최근 정규장 확정 종가(실시간 아님)',summary)

    def test_yahoo_and_nasdaq_info_fail_historical_fallback_succeeds(self):
        s=WATCHLIST[4]
        urls=[]
        def opener(req,timeout):
            urls.append(req.full_url)
            if '/historical?' in req.full_url:
                return Response(nasdaq_daily(s))
            raise HTTPError(req.full_url,429,'blocked',{},None)
        with self.assertLogs('app.market',level='INFO') as log:
            q=fetch_quote(s,opener=opener,now=NOW)
        self.assertEqual(q.source,'나스닥 확정 종가')
        self.assertEqual(len(urls),3)
        self.assertTrue(urls[-1].endswith('/historical?assetclass=stocks&limit=10'))
        self.assertIn('US_QUOTE_FALLBACK_OK ticker=SNDK',log.output[0])

    def test_naver_overseas_daily_fallback_when_nasdaq_history_denied(self):
        s=WATCHLIST[2]
        urls=[]
        def opener(req,timeout):
            urls.append(req.full_url)
            if 'api.stock.naver.com/chart/foreign/item/' in req.full_url:
                return Response(naver_daily(s))
            raise HTTPError(req.full_url,403,'blocked',{},None)
        result=fetch_quote(s,opener=opener,now=NOW)
        self.assertEqual(result.source,'네이버 해외 확정 종가')
        self.assertAlmostEqual(result.price,776.15)
        self.assertEqual(len(urls),4)
        self.assertEqual(urls[-1], 'https://api.stock.naver.com/chart/foreign/item/MU.O?periodType=dayCandle')
        self.assertIn('네이버 해외 확정 종가','\n'.join(market_source_summary([result])))

    def test_supports_four_user_stocks(self):
        for stock in (WATCHLIST[2],WATCHLIST[4],WATCHLIST[6],WATCHLIST[7]):
            with self.subTest(stock=stock.ticker):
                q=parse_naver_us_daily_quote(stock,naver_daily(stock),now=NOW)
                self.assertEqual(q.stock.ticker,stock.ticker)
                self.assertEqual(q.source,'네이버 해외 확정 종가')

    def test_do_not_fetch_naver_for_unverified_or_japanese_ticker(self):
        for s in (WATCHLIST[3],WATCHLIST[0],WATCHLIST[5]):
            with self.subTest(stock=s.ticker),self.assertRaises(StockQuoteError):
                fetch_naver_us_daily_quote(s,opener=lambda *a:None,now=NOW)

    def test_nasdaq_ticker_and_data_validations(self):
        s=WATCHLIST[2]
        for mutate in (lambda x:x.update(data=dict(symbol='AAPL',tradesTable=x['data']['tradesTable'])),
                       lambda x:x['data'].update(tradesTable={'rows':[{'date':'11/04/2026','close':'$1'}]}),
                       lambda x:x['data']['tradesTable']['rows'][0].update(close='-100'),
                       lambda x:x['data']['tradesTable']['rows'][0].update(date='2026-11-04')):
            data=nasdaq_daily(s)
            mutate(data)
            # invalid single row or wrong format might have older two valid rows -> date invalid is ignored and remaining 2 accepted.
            if len(data['data']['tradesTable']['rows'])==1 or data['data']['symbol']=='AAPL':
                with self.assertRaises(StockQuoteError):parse_nasdaq_daily_quote(s,data,now=NOW)
            else:
                q=parse_nasdaq_daily_quote(s,data,now=NOW)
                self.assertEqual(q.market_time.date().isoformat(),'2026-11-03')

    def test_no_intraday_unfinished_close(self):
        s=WATCHLIST[2]
        early=datetime(2026,11,4,19,0,tzinfo=timezone.utc)  # 14:00 ET
        q=parse_nasdaq_daily_quote(s,nasdaq_daily(s),now=early)
        self.assertEqual(q.market_time.date().isoformat(),'2026-11-03')
        with self.assertRaises(StockQuoteError):
            parse_nasdaq_daily_quote(s,{'data':{'symbol':s.ticker,'tradesTable':{'rows':[
                {'date':'11/04/2026','close':'$123.00'}, {'date':'11/03/2026','close':'$777.00'}]}}},now=early)

    def test_stale_or_conflicting_daily_data_refused(self):
        s=WATCHLIST[2]
        for data in (
            {'data':{'symbol':s.ticker,'tradesTable':{'rows':[
                {'date':'10/05/2026','close':'$22'}, {'date':'10/04/2026','close':'$21'}]}}},
            {'data':{'symbol':s.ticker,'tradesTable':{'rows':[
                {'date':'11/04/2026','close':'$776'}, {'date':'11/04/2026','close':'$775'},
                {'date':'11/03/2026','close':'$780'}]}}},
        ):
            with self.subTest(data=data),self.assertRaises(StockQuoteError):
                parse_nasdaq_daily_quote(s,data,now=NOW)

    def test_provider_failures_preserved_diagnostics_and_no_fabricated_values(self):
        s=WATCHLIST[2]
        urls=[]
        def opener(req,timeout):
            urls.append(req.full_url)
            raise HTTPError(req.full_url,429,'blocked',{},None)
        with self.assertLogs('app.market',level='WARNING') as logs:
            with self.assertRaisesRegex(StockQuoteError,'미국 무료 시세 제공처'):
                fetch_quote(s,opener=opener,now=NOW)
        self.assertEqual(len(urls),4)
        self.assertIn('Nasdaq daily:나스닥 일봉 HTTP 429',logs.output[0])
        self.assertIn('Naver overseas daily:네이버 해외 일봉 HTTP 429',logs.output[0])

    def test_naver_chart_rejects_wrong_reuters_code(self):
        s=WATCHLIST[2]
        data=naver_daily(s);data['reutersCode']='AAPL.O'
        with self.assertRaisesRegex(StockQuoteError,'종목코드 불일치'):
            parse_naver_us_daily_quote(s,data,now=NOW)

    def test_nasdaq_history_uses_bounded_header_only(self):
        s=WATCHLIST[2]
        urls=[]
        def opener(req,timeout):
            urls.append(req.full_url)
            return Response(nasdaq_daily(s))
        q=fetch_nasdaq_daily_quote(s,opener=opener,now=NOW)
        self.assertEqual(q.source,'나스닥 확정 종가')
        self.assertEqual(urls, ['https://api.nasdaq.com/api/quote/MU/historical?assetclass=stocks&limit=10'])

if __name__=='__main__':unittest.main()
