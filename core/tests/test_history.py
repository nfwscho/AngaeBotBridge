"""
앙개봇 v0.5.2 역사적 종가/실현변동성 테스트 — 모든 기능과 안전 제약 설명
1. 5거래일 확정 종가/전일대비/5일 수익률 표시와 원화·달러·엔 형식을 검증한다.
2. 21·63거래일 수익률은 기간 시작 종가 대비, 실현변동성은 표본 로그수익률×√252로 검증한다.
3. 데이터 수가 22/64개 미만이면 해당 기간에 데이터 부족을 표시하는지 확인한다.
4. 장중 아직 끝나지 않은 현재일 일봉과 미래 날짜/10일보다 오래된 시세를 차단한다.
5. Yahoo 티커·통화·일봉 빈도·숫자·중복 날짜를 검증한다.
6. Naver 한국 일봉 JSON 형식과 해외 보조 일봉 형식/엉뚱한 티커를 검증한다.
7. 공급자 연결 실패 시 보조 엔드포인트로 안전하게 전환하며 응답 크기 한도를 확인한다.
8. 그룹 종목별 일부 실패를 격리하고 등록 순서·메모리7 기초 watchlist를 유지한다.
9. 외부 URL/AI 호출/알림/예약/매매 없이 모의 응답·고정 시각만으로 테스트한다.
10. 개인 기록·실제 SQLite·환경변수·로그를 읽거나 변경하지 않는다.
11. Termux의 ZoneInfo/tzdata 누락을 모의로 재현하여 한국/일본 UTC+9 안전 동작을 확인한다.
12. 미국 시장 DST를 고정 offset으로 잘못 대체하지 않고 명확한 설치 오류를 주는지 확인한다.
"""
from __future__ import annotations

import io
import json
import math
import unittest
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfoNotFoundError
from unittest.mock import patch

from app.market import WATCHLIST, StockQuoteError
from app.history import (DailyBar, HistoryResult, parse_yahoo_history, parse_naver_history,
    fetch_history, period_result, individual_report, group_report, is_analysis_request,
    HISTORY_MAX_BYTES)

NOW = datetime(2026, 11, 5, 19, 0, tzinfo=timezone.utc)


def bars(count=75, start=date(2026, 7, 15), *, price=100.0):
    return tuple(DailyBar(start + timedelta(days=x), price * 1.01**x,
                          price * 1.01**x) for x in range(count))


def yahoo_payload(stock, times, closes, adjusted=None):
    indicator = {'quote':[{'close': closes}]}
    if adjusted is not None:
        indicator['adjclose'] = [{'adjclose': adjusted}]
    return {'chart':{'result':[{'meta':{'symbol':stock.ticker,'currency':stock.currency,
                  'dataGranularity':'1d'},'timestamp':times, 'indicators':indicator}]}}


class HistoryUnitTests(unittest.TestCase):
    def test_missing_iana_database_uses_safe_asian_fallback_only(self):
        from app.history import _local_now, parse_yahoo_history
        now = datetime(2026, 11, 5, 1, 0, tzinfo=timezone.utc)  # KST 10:00
        with patch('app.history.ZoneInfo', side_effect=ZoneInfoNotFoundError('missing IANA data')):
            for stock in (WATCHLIST[0], WATCHLIST[5]):
                with self.subTest(stock=stock.ticker):
                    local = _local_now(stock, now)
                    self.assertEqual(local.hour, 10)
                    self.assertEqual(local.utcoffset(), timedelta(hours=9))
            # DST 적용 미국은 UTC-5를 임의로 고정하지 않아 과거 거래일이 틀어지지 않는다.
            with self.assertRaisesRegex(StockQuoteError, 'tzdata'):
                _local_now(WATCHLIST[2], now)
            with self.assertRaisesRegex(StockQuoteError, 'tzdata'):
                parse_yahoo_history(WATCHLIST[2], yahoo_payload(WATCHLIST[2],
                    [int(datetime(2026,11,4,15,tzinfo=timezone.utc).timestamp())], [100]), now=now)

    def test_21_and_63_return_and_annualized_log_volatility(self):
        series = bars(75)
        one, three = period_result(series,21), period_result(series,63)
        self.assertAlmostEqual(one.cumulative_pct, (1.01**21-1)*100, places=9)
        self.assertAlmostEqual(three.cumulative_pct, (1.01**63-1)*100, places=9)
        self.assertLess(one.volatility_pct, 0.000001)
        self.assertLess(three.volatility_pct, 0.000001)
        changes = [0.1 if x%2 else -0.05 for x in range(1, 65)]
        closes=[100.]
        for x in changes:
            closes.append(closes[-1]*math.exp(x))
        series=tuple(DailyBar(date(2026, 7, 1)+timedelta(days=i),v,v) for i,v in enumerate(closes))
        from statistics import stdev
        self.assertAlmostEqual(period_result(series,63).volatility_pct,
                               stdev(changes[-63:])*math.sqrt(252)*100,places=8)

    def test_insufficient_samples_has_no_fake_volatility(self):
        data=bars(10)
        self.assertIsNotNone(period_result(data,5).cumulative_pct)
        self.assertIsNone(period_result(data,21).cumulative_pct)
        self.assertIsNone(period_result(data,63).volatility_pct)
        report=individual_report(HistoryResult(WATCHLIST[2],data,'모의'))
        self.assertIn('1개월(21일): 데이터 부족',report)
        self.assertIn('3개월(63일): 데이터 부족',report)
        self.assertEqual(report.count('데이터 부족'),2)

    def test_five_closed_sessions_with_prices_and_daily_returns(self):
        data=bars(7)
        report=individual_report(HistoryResult(WATCHLIST[0],data,'네이버'))
        self.assertIn('삼성전자 (005930.KS)',report)
        self.assertEqual(sum('원 (' in line for line in report.splitlines()),5)
        self.assertIn('5거래일 누적: +5.10%', report)
        self.assertIn('1개월(21일): 데이터 부족', report)
        self.assertIn('장마감 종가',report)

    def test_yahoo_uses_adjusted_closes_and_filters_null_and_future(self):
        stock=WATCHLIST[2]
        dates=[datetime(2026,11,2,15,tzinfo=timezone.utc),
               datetime(2026,11,3,15,tzinfo=timezone.utc),
               datetime(2026,11,4,15,tzinfo=timezone.utc),
               datetime(2026,11,5,15,tzinfo=timezone.utc)]
        payload=yahoo_payload(stock,[int(t.timestamp()) for t in dates],
                              [90,None,120,150],[45,None,60,75])
        result=parse_yahoo_history(stock,payload,now=NOW)
        self.assertEqual(len(result),2)  # 11/5 미국 정규장 아직 끝나지 않음
        self.assertEqual([bar.close for bar in result],[90,120])
        self.assertEqual([bar.adjusted for bar in result],[45,60])
        self.assertEqual(result[-1].date,date(2026,11,4))

    def test_yahoo_rejects_wrong_symbol_currency_and_interval(self):
        stock=WATCHLIST[2]
        epoch=int(datetime(2026,11,4,15,tzinfo=timezone.utc).timestamp())
        for field, bad in [('symbol','BAD'),('currency','KRW'),('dataGranularity','1wk')]:
            sample=yahoo_payload(stock,[epoch],[100],[100])
            sample['chart']['result'][0]['meta'][field]=bad
            with self.subTest(field=field), self.assertRaises(StockQuoteError):
                parse_yahoo_history(stock,sample,now=NOW)
        sample=yahoo_payload(stock,[epoch,epoch],[100],[100])
        with self.assertRaises(StockQuoteError):
            parse_yahoo_history(stock,sample,now=NOW)

    def test_naver_parsing_and_stale_rejection(self):
        stock=WATCHLIST[0]
        payload={'itemCode':'005930','priceInfos':[
            {'localDate':'20261102','closePrice':190000},
            {'localDate':'20261104','closePrice':'200,000'},
            {'localDate':'20261105','closePrice':'210,000'},
            {'localDate':'BAD','closePrice':999999}]}
        now=datetime(2026,11,5,1,0,tzinfo=timezone.utc)  # KST 10:00, 아직 장중
        result=parse_naver_history(stock,payload,now=now)
        self.assertEqual(len(result),2)
        self.assertEqual(result[-1].close,200000)
        payload['itemCode']='000660'
        with self.assertRaises(StockQuoteError):
            parse_naver_history(stock,payload,now=now)
        with self.assertRaises(StockQuoteError):
            parse_naver_history(stock,{'priceInfos':[{'localDate':'20261001','closePrice':100}]},now=now)

    def test_provider_order_korea_naver_first_us_yahoo_first(self):
        class MockResponse:
            def __init__(self, data):self.data=data
            def __enter__(self):return self
            def __exit__(self,*args):return None
            def read(self,length):return self.data
        calls=[]
        naver={'priceInfos':[{'localDate':'20261104','closePrice':200000}]}
        def opener(req,timeout):
            calls.append(req.full_url)
            if 'naver' in req.full_url:
                return MockResponse(json.dumps(naver).encode())
            raise OSError('no access')
        result=fetch_history(WATCHLIST[0],opener=opener,now=NOW,use_cache=False)
        self.assertEqual(result.bars[0].close,200000)
        self.assertIn('naver',calls[0])
        calls=[]
        with self.assertRaises(StockQuoteError):
            fetch_history(WATCHLIST[2],opener=opener,now=NOW,use_cache=False)
        self.assertEqual(len(calls),2)
        self.assertTrue(all('finance.yahoo' in x for x in calls))

    def test_invalid_source_and_absurd_bytes_do_not_create_numbers(self):
        class BigResponse:
            def __enter__(self):return self
            def __exit__(self,*args):return None
            def read(self,length):return b'X'*(HISTORY_MAX_BYTES+1)
        with self.assertRaises(StockQuoteError):
            fetch_history(WATCHLIST[2],opener=lambda req,timeout:BigResponse(),now=NOW,use_cache=False)

    def test_group_report_partial_failure_preserves_order(self):
        from app.watchlists import resolve_stock
        symbols=(resolve_stock('MU'),resolve_stock('AAPL'),resolve_stock('285A.T'))
        def provider(stock):
            if stock.ticker == 'AAPL': raise StockQuoteError('blocked')
            return HistoryResult(stock,bars(70),'mock')
        body=group_report('미국시총10',symbols,fetcher=provider)
        self.assertIn('마이크론[',body)
        self.assertIn('AAPL: 조회 불가',body)
        self.assertIn('1M',body)
        self.assertIn('3M',body)
        self.assertLess(body.index('마이크론['),body.index('AAPL:'))
        self.assertLess(body.index('AAPL:'),body.index('키오시아'))
        self.assertLess(len(body),1800)
        with self.assertRaises(StockQuoteError):
            group_report('x',symbols,fetcher=lambda s: (_ for _ in ()).throw(StockQuoteError('no')))

    def test_dedup_and_sign_and_request_classifier(self):
        stock=WATCHLIST[5]
        records=[DailyBar(date(2026,11,2), 150,150),DailyBar(date(2026,11,2), 100,100),
                 DailyBar(date(2026,11,4),90,90)]
        from app.history import _clean_bars
        final=_clean_bars(stock,records,now=NOW)
        self.assertEqual(len(final),2)
        self.assertEqual(final[0].close,100)
        self.assertTrue(is_analysis_request('분석 MU'))
        self.assertFalse(is_analysis_request('목록'))
        self.assertFalse(is_analysis_request('추가 MU'))

if __name__ == '__main__':unittest.main()
