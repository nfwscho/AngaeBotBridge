"""
앙개봇 Python Core v0.5.7 네이버 국내 시세 회귀 테스트 — 전체 기능·보존 사항
1. 네이버 실시간 폴링 URL을 국내 삼성전자/하이닉스 1순위로 사용하며 기존 모바일 URL은 안전한 2순위다.
2. 폴링 응답의 itemCode/symbolCode, 현재가/전일비/거래시각/시장상태/지연정보를 독립 검증한다.
3. 0분 지연 표기만으로 실시간 인증하지 않고 폴링·OPEN·최근 180초 체결·최근 180초 서버시각이 동시에 맞아야 한다.
4. 마감·장전·폴링 시각 누락·오래된 체결·지연 15분·서버 응답 과거값은 실시간으로 표시하지 않는다.
5. KRX 본장 체결과 장전·장후 별도 시세를 구분하고, NXT 정보가 직접 없는 경우 거래소를 추정하지 않는다.
6. 변동률·체결시각/가격이 불일치하거나 과거인 시간외 시세는 제외하고 KRX 본장 가격을 보존한다.
7. 네이버 연결 실패 시 기존 Yahoo 폴백을 보존하고 실시간으로 오인하지 않도록 출처를 표시한다.
8. 메모리7 1~8번 번호 선택, 사용자 그룹 번호 및 기존 Android 배터리·기존 DB/로그/인증은 그대로 유지한다.
9. 외부 인터넷/AI/실제 운영 SQLite를 읽거나 수정하지 않으며 TestClient/Mock 데이터만 사용한다.
10. 환율/외국 주식/과거 종가·변동성·알림/주문/백그라운드 처리에는 변경이 없음을 확인한다.
11. v0.5.9 메모리7과 사용자 그룹에서 KRX 상세 정보가 종목마다 반복되지 않고 출처가 시장별 하단 한 줄로 이동했음을 검사한다.
"""
from __future__ import annotations

import json
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.market import (WATCHLIST, DomesticQuoteMetadata, StockQuoteError, fetch_naver_quote,
                        fetch_quote, parse_naver_quote, memory7_report, quote_line)
from app.watchlists import group_report

KST = timezone(timedelta(hours=9))


def local(h: int, minute: int, sec: int = 0) -> datetime:
    return datetime(2026, 11, 5, h, minute, sec, tzinfo=KST)


def payload(time: datetime, *, status='OPEN', delay=0, code='005930', price='221,500', percent='0.50') -> dict:
    return {
        'pollingInterval': 70000,
        'time': time.strftime('%Y%m%d%H%M%S'),
        'datas': [{
            'itemCode': code, 'symbolCode': code, 'closePrice': price,
            'compareToPreviousPrice': {'name': 'RISING'},
            'fluctuationsRatio': percent, 'localTradedAt': time.isoformat(),
            'marketStatus': status, 'stockExchangeType': {'delayTime': delay, 'name':'KOSPI'},
        }],
    }


class Response:
    def __init__(self, raw: bytes): self.raw = raw
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, size): return self.raw[:size]


class NaverRealtimeTests(unittest.TestCase):
    def test_valid_realtime_polling_requires_4_checks(self):
        t = local(9, 16, 10)
        data = payload(t)
        urls = []
        def opener(req, timeout):
            urls.append(req.full_url)
            return Response(json.dumps(data).encode())
        quote = fetch_naver_quote(WATCHLIST[0], opener=opener, now=t.astimezone(timezone.utc) + timedelta(seconds=5))
        self.assertEqual(len(urls), 1)
        self.assertIn('polling.finance.naver.com', urls[0])
        self.assertEqual(quote.price, 221500)
        self.assertEqual(quote.domestic.provider, '폴링')
        self.assertIn('KRX 11/05 09:16:10', quote_line(quote))
        self.assertIn('네이버 실시간표시(지연 0분)', quote_line(quote))

    def test_delay_and_old_polling_are_not_realtime(self):
        t = local(9, 20)
        sample = payload(t)
        for overrides, now, expected in [
            ({'stockExchangeType': {'delayTime':15}}, t + timedelta(seconds=30), '지연 15분 표기'),
            ({'marketStatus': 'CLOSE'}, t + timedelta(seconds=30), '장마감 종가'),
            ({'marketStatus': 'PREPARE'}, t + timedelta(seconds=30), '개장 전 최종가'),
            ({}, t + timedelta(minutes=8), '시세 갱신 지연'),
        ]:
            with self.subTest(expected=expected):
                data = {**sample['datas'][0], **overrides}
                quote = parse_naver_quote(WATCHLIST[0], data, now=now, provider='폴링', snapshot_time=t)
                label = quote_line(quote)
                self.assertIn(expected, label)
                self.assertNotIn('실시간표시(지연 0분)',label)
        # 체결시각은 최근이지만 서버 폴링 갱신 기준이 과거여도 실시간 금지.
        quote = parse_naver_quote(WATCHLIST[0], sample['datas'][0], now=t,
                                  provider='폴링', snapshot_time=t-timedelta(hours=3))
        self.assertNotIn('실시간표시(지연 0분)',quote_line(quote))
        quote = parse_naver_quote(WATCHLIST[0], sample['datas'][0], now=t,
                                  provider='모바일', snapshot_time=t)
        self.assertNotIn('실시간표시(지연 0분)',quote_line(quote))

    def test_nxt_aftermarket_is_separate_and_market_unspecified_stays_unspecified(self):
        t = local(20, 0)
        regular = local(15, 30)
        base = payload(regular, status='CLOSE', price='230,000', percent='-0.43')['datas'][0]
        base['compareToPreviousPrice'] = {'name':'FALLING'}
        after = dict(tradingSessionType='AFTER_MARKET', overMarketStatus='CLOSE', overPrice='231,500',
                     fluctuationsRatio='0.22',compareToPreviousPrice={'name':'RISING'},
                     localTradedAt=local(20,0).isoformat())
        # 네이버 polling 응답에 거래소 확인 필드가 없다면 NXT를 추정하지 않는다.
        a = parse_naver_quote(WATCHLIST[0], base | {'overMarketPriceInfo':after}, now=t)
        self.assertEqual(a.price, 230000)
        self.assertEqual(a.domestic.after_market.price,231500)
        body=quote_line(a)
        self.assertIn('KRX 11/05 15:30:00 · 장마감 종가',body)
        self.assertIn('시간외(거래소 미확인) 장후 231,500원',body)
        self.assertIn('마감',body)
        # nxtOverMarketPriceInfo는 NXT임이 명시된 구조에 한해 표시한다.
        b=parse_naver_quote(WATCHLIST[0],base | {'nxtOverMarketPriceInfo':after},now=t)
        self.assertIn('NXT 장후 231,500원',quote_line(b))
        self.assertNotIn('NXT',quote_line(a))
        # 명시적으로 과거 시간외 시세는 현재가처럼 붙이지 않는다.
        stale_after = after | {'localTradedAt':local(10,0).isoformat()}
        old = parse_naver_quote(WATCHLIST[0],base | {'overMarketPriceInfo': stale_after},now=t)
        self.assertIsNone(old.domestic.after_market)
        invalid = after | {'fluctuationsRatio':'99.9'}
        self.assertIsNone(parse_naver_quote(WATCHLIST[0],base | {'overMarketPriceInfo': invalid},now=t).domestic.after_market)

    def test_polling_live_stale_then_mobile_fresher(self):
        now = local(9, 41)
        polling = payload(local(9, 20), status='OPEN')
        mobile = dict(itemCode='005930', closePrice='223,000', fluctuationsRatio='0.75',
                      localTradedAt=local(9,40).isoformat(), marketStatus='OPEN')
        calls=[]
        def opener(req, timeout):
            calls.append(req.full_url)
            data = polling if 'polling.finance' in req.full_url else mobile
            return Response(json.dumps(data).encode())
        quote=fetch_naver_quote(WATCHLIST[0],opener=opener,now=now)
        self.assertEqual(quote.price,223000)
        self.assertEqual(quote.domestic.provider,'모바일')
        self.assertEqual(len(calls),2)
        self.assertNotIn('실시간표시',quote_line(quote))
        # 두 번째 공급자가 더 오래된 시세를 주면 첫 번째 폴링 가격을 보존한다.
        mobile['localTradedAt'] = local(9,18).isoformat()
        quote=fetch_naver_quote(WATCHLIST[0],opener=opener,now=now)
        self.assertEqual(quote.price,221500)
        self.assertIn('시세 갱신 지연',quote_line(quote))

    def test_bad_identity_and_yahoo_fallback_no_realtime_claim(self):
        t = local(9, 32)
        data = payload(t)
        data['datas'][0]['itemCode'] = '000660'
        data['datas'][0]['symbolCode'] = '000660'
        urls=[]
        def opener(req, timeout):
            urls.append(req.full_url)
            if 'polling.finance.naver.com' in req.full_url:
                return Response(json.dumps(data).encode())
            if 'm.stock.naver.com' in req.full_url:
                basic = dict(itemCode='005930', closePrice='221,500', fluctuationsRatio='0.50',
                             localTradedAt=t.isoformat(), marketStatus='OPEN')
                return Response(json.dumps(basic).encode())
            raise OSError('unavailable')
        quote=fetch_naver_quote(WATCHLIST[0],opener=opener,now=t)
        self.assertEqual(quote.domestic.provider,'모바일')
        self.assertEqual(len(urls),2)
        self.assertIn('실시간 여부 미확인',quote_line(quote))
        # 기존 미국/일본 코드와 동일한 Yahoo fallback; 출처/지연미확인을 정확히 표기.
        from app.market import Quote
        yahoo=Quote(WATCHLIST[0],220000,219000,0.4566,t,t)
        with patch('app.market.fetch_naver_quote', side_effect=StockQuoteError('failed')):
            with patch('app.market.fetch_yahoo_quote', return_value=yahoo):
                backup=fetch_quote(WATCHLIST[0],now=t)
        self.assertEqual(backup.price,220000)
        self.assertIn('Yahoo 대체',quote_line(backup))
        self.assertNotIn('실시간표시',quote_line(backup))

    def test_group_and_memory_keep_row_numbers_and_metadata(self):
        t = local(9, 15)
        q = parse_naver_quote(WATCHLIST[0], payload(t)['datas'][0],
                              now=t, provider='폴링',snapshot_time=t)
        def quotes(stock):
            return q if stock.ticker == WATCHLIST[0].ticker else None
        report=memory7_report(fetcher=quotes,use_cache=False)
        self.assertIn('1. 삼성전자',report)
        self.assertIn('2. 하이닉스 : 조회 불가',report)
        self.assertIn('  국내: 네이버 폴링 · KRX',report)
        self.assertNotIn('   └ KRX',report)
        self.assertIn('번호 1~8',report)
        def group_quotes(stock): return q if stock.ticker == q.stock.ticker else None
        report=group_report('내종목', (WATCHLIST[0],WATCHLIST[2]),fetcher=group_quotes)
        self.assertIn('1. 삼성전자',report)
        self.assertIn('2. 마이크론 : 조회 불가',report)
        self.assertIn('  국내: 네이버 폴링 · KRX',report)
        self.assertNotIn('   └ KRX',report)
        self.assertIn('번호 1~2',report)


if __name__=='__main__': unittest.main()
