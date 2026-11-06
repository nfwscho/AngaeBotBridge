"""
앙개봇 v0.5.9 국내/미국/일본 시세 출처 통합 출력 회귀 테스트 — 모든 기능 검증
1. 메모리7은 기존 8종목/번호/순서/가격/등락률/실패 자리와 현지 거래일을 변경하지 않는다.
2. 관심종목 그룹은 기존 최대 10종목/번호 선택/5분 안내와 사용자별 저장/조회 흐름을 변경하지 않는다.
3. 국내 네이버 폴링 시세·KRX 시각/실시간 여부를 행마다 출력하지 않고 목록 하단에 단 한 번 표시한다.
4. 미국 나스닥 공개 웹 및 Yahoo Finance 시세가 혼합되면 공급자들을 한 시장에 병합해 표시한다.
5. 일본 Yahoo Finance/Japan·라쿠텐 출처는 성공한 조회의 기록이 있으면 그 공급자만 출력한다.
6. 시장 내 체결시각이 다른 경우 '최신' 및 '종목별 거래시각 상이'를 표시해 전체 공통시각으로 오인하지 않는다.
7. 조회 불가 종목만 남은 시장은 성공한 시세로 위장하지 않고 출처 목록에서 제외한다.
8. 기존 quote_line 단독 상세 출력은 전부 유지하고 KRX/NXT 시간외 가격은 정규 시세와 별도 표시한다.
9. 30초 캐시·예외 격리·Kakao 배터리 접미사·DB/이벤트/메뉴·기존 API는 변경하지 않는다.
10. 테스트는 고정 UTC/거래소 시각·Mock Quote만 이용하고 외부 서버/실제 사용자 DB에 접근하지 않는다.
"""
from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.market import (WATCHLIST, Quote, DomesticQuoteMetadata, AfterMarketQuote,
                        memory7_report, quote_line, market_source_summary)
from app.watchlists import group_report

KST = ZoneInfo('Asia/Seoul')
ET = ZoneInfo('America/New_York')
JST = ZoneInfo('Asia/Tokyo')


def mock_quote(stock, when, *, source='', provider=None, status='OPEN', delay=None, after=None):
    metadata = (DomesticQuoteMetadata(provider, status, delay, when, after)
                if provider is not None else None)
    return Quote(stock, 100.0, 98.0, 2.040816, when, when, domestic=metadata, source=source)


class MarketSourceSummaryTests(unittest.TestCase):
    def setUp(self):
        self.korean = datetime(2026, 11, 5, 10, 48, 50, tzinfo=KST)
        self.us = datetime(2026, 11, 4, 19, 59, 0, tzinfo=ET)
        self.jp = datetime(2026, 11, 5, 10, 25, 0, tzinfo=JST)
        self.a = mock_quote(WATCHLIST[0], self.korean, provider='폴링')
        self.b = mock_quote(WATCHLIST[1], self.korean, provider='폴링')
        self.c = mock_quote(WATCHLIST[2], self.us, source='나스닥 웹')
        self.d = mock_quote(WATCHLIST[4], self.us, source='나스닥 웹')
        self.j = mock_quote(WATCHLIST[5], self.jp, source='Yahoo Japan')

    def test_group_source_once_below_all_rows(self):
        data = (self.a, self.b, self.j, self.c, self.d)
        lookup = {q.stock.ticker: q for q in data}
        report = group_report('반도체', tuple(q.stock for q in data), fetcher=lambda s: lookup[s.ticker])
        rows = report.splitlines()
        for n, q in enumerate(data, 1):
            self.assertTrue(any(row.startswith(f'{n}. {q.stock.name} ') for row in rows))
        footer_idx = next(i for i, row in enumerate(rows) if row.startswith('📡 '))
        self.assertTrue(all(i < footer_idx for i, row in enumerate(rows) if row.startswith(('1.', '2.', '3.', '4.', '5.'))))
        self.assertEqual(sum(row.startswith('📡 ') for row in rows), 1)
        self.assertIn('KR11/05', report)
        self.assertIn('US11/04', report)
        self.assertIn('JP11/05', report)
        self.assertIn('99. 🔎 상세보기', report)
        self.assertNotIn('네이버·KRX', report)
        self.assertNotIn('5분 내 1~5', report)
        self.assertEqual(report.splitlines()[-1], '99. 🔎 상세보기')
        detailed = group_report('반도체', tuple(q.stock for q in data),
                                fetcher=lambda stock: lookup[stock.ticker], detailed=True)
        self.assertIn('99. ↩ 간략보기', detailed)
        self.assertIn('네이버', detailed)
        self.assertIn('나스닥', detailed)
        self.assertIn('Yahoo Japan', detailed)
        self.assertIn('ET', detailed)
        self.assertIn('시세 출처 · 기준시각:', detailed)

    def test_memory7_market_summary_and_partial_failure(self):
        data = {q.stock.ticker:q for q in (self.a, self.b, self.c, self.j)}
        def get(stock):
            if stock.ticker not in data:
                raise ValueError('network mock blocked')
            return data[stock.ticker]
        report = memory7_report(fetcher=get,use_cache=False)
        self.assertIn('8. 웬디 : 조회 불가', report)
        self.assertIn('3. 마이크론 ', report)
        # 메모리7 기본 화면은 국가별 시각 3줄 대신 한 줄 압축.
        # 거래일 차이(한국·일본 11/05, 미국 11/04)를 숨기지 않는다.
        self.assertIn('📡 KR11/05', report)
        self.assertIn('US11/04', report)
        self.assertIn('JP11/05', report)
        self.assertEqual(report.count('📡 '), 1)
        self.assertEqual(report.count('KR11/05'), 1)
        self.assertEqual(report.count('US11/04'), 1)
        self.assertEqual(report.count('JP11/05'), 1)
        self.assertIn('99. 🔎 상세보기', report)
        self.assertIn('4종목 조회 실패', report)
        self.assertIn('5분 내 1~8', report)

    def test_mixed_us_suppliers_and_different_times(self):
        old = replace(self.c, source='', market_time=self.us-timedelta(hours=4))
        result = '\n'.join(market_source_summary([self.c, old]))
        self.assertIn('나스닥 공개 시세 / Yahoo Finance',result)
        self.assertIn('최신',result)
        self.assertIn('종목별 거래시각 상이',result)
        self.assertEqual(result.count('미국:'),1)
        self.assertEqual(result.count('지연 여부 미확인'),1)

    def test_summary_omits_unavailable_markets(self):
        result = '\n'.join(market_source_summary([None,self.j,None]))
        self.assertNotIn('국내:',result)
        self.assertNotIn('미국:',result)
        self.assertIn('일본: Yahoo Japan',result)

    def test_domestic_mix_mobile_and_market_freshness(self):
        old = replace(self.b, domestic=replace(self.b.domestic, provider='모바일', market_status='CLOSE'),
                      market_time=self.korean-timedelta(minutes=5))
        result = '\n'.join(market_source_summary([self.a,old]))
        self.assertIn('네이버 폴링 / 네이버 모바일',result)
        self.assertIn('장마감 종가',result)
        self.assertIn('종목별 거래시각 상이',result)

    def test_single_quote_details_and_aftermarket_still_present(self):
        after=AfterMarketQuote(105.0, 3.0, self.korean, '장후', 'OPEN', 'NXT')
        regular = replace(self.a, domestic=replace(self.a.domestic, after_market=after))
        original=quote_line(regular)
        short=quote_line(regular,source_details=False)
        self.assertIn('네이버 폴링', original)
        self.assertIn('NXT 장후',original)
        self.assertIn('NXT 장후',short)
        self.assertNotIn('네이버 폴링',short)
        self.assertIn('나스닥 공개 시세',quote_line(self.c))
        self.assertNotIn('나스닥 공개 시세',quote_line(self.c,source_details=False))


if __name__ == '__main__':
    unittest.main()
