"""
앙개봇 시세 간략/상세 보기 전용 회귀 테스트 — 전체 기능과 보존 사항
1. 한국 애프터 대표가격은 전일비 음수인 경우에도 당일 KRX 확정 종가 대비 상승이면 플러스로 표시한다.
2. 한국 애프터/프리 기준가 미확인 시 방향과 등락률을 지어내지 않고 실제 세션 체결가격만 한 줄에 표시한다.
3. 미국 프리·애프터가 동시에 있을 때 현재 현지 거래 세션에 맞는 대표가격 한 개만 표시한다.
4. 미국 프리 가격은 세션의 검증된 거래일 및 원본 시세를 훼손하지 않고 출력한다.
5. 메모리7 1~8 종목, 사용자 그룹의 1~10 번호와 기존 분석 선택·출처·캐시·로그 기능을 보존한다.
6. '메모리7 상세'만 정규/프리/애프터를 여러 줄로, 기본 조회는 종목마다 정확히 한 줄로 표시한다.
7. 상세 보기에서 한국 장후 정규장 대비 및 전일비의 기준을 명시하고 검증된 정규 종가를 제공한다.
8. 모든 검사는 네트워크, 실제 SQLite, Android Bridge, .env, AI 설정, 운영 로그에 영향을 주지 않는 모의 데이터만 사용한다.
9. 구형 Naver 정규장 15:30 값과 overMarketPriceInfo를 별도로 제공한 경우에도 현재 장외 세션의 대표값·정규장대비 부호를 검증한다.
10. 다른 KST 거래일의 장외 데이터를 현재 체결가로 오표시하지 않고 정규장 값으로 복귀한다.
11. 카카오톡 좁은 말풍선에서 P/A 한 글자 표시, 8개 종목·9번 상세 메뉴·짧은 현지시각 요약으로 전체보기 접힘을 최소화한다.
12. 미국 정규장 중 과거 프리 체결은 대표 시세를 덮지 않으며 장외 시간에는 실제 세션의 P/A 가격만 보인다.
13. 메모리7 간략 보기와 상세 보기 사이에 원본 정규·프리·애프터 데이터, 거래일과 출처가 누락되지 않음을 검증한다.
"""
from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

from app.extended_sessions import SessionPrice
from app.market import (
    WATCHLIST, Quote, DomesticQuoteMetadata, AfterMarketQuote,
    compact_quote_line, quote_line, memory7_report, execute_stock_command,
)
from app.watchlists import group_report

KST = timezone(timedelta(hours=9))
ET = ZoneInfo('America/New_York')


def korean_after(stock, regular, after, previous, *, known=True, session='장후'):
    local = (datetime(2026, 11, 6, 19, 1, tzinfo=KST) if session == '장후'
             else datetime(2026, 11, 6, 8, 25, tzinfo=KST))
    close = datetime(2026, 11, 6, 15, 30, tzinfo=KST)
    prior = datetime(2026, 11, 5, 15, 30, tzinfo=KST)
    after_percent = (after / previous - 1) * 100
    base = AfterMarketQuote(after, after_percent, local, session, 'OPEN', '거래소 미확인')
    meta = DomesticQuoteMetadata(
        '폴링', 'OPEN', 0, local, base,
        'aftermarket' if session == '장후' else 'premarket',
        regular_price=regular if known else None,
        regular_percent=(regular / previous - 1) * 100 if known else None,
        regular_time=(close if session == '장후' else prior) if known else None,
        regular_source='네이버 KRX 일봉' if known else '',
    )
    return Quote(stock, after, previous, after_percent, local, local, domestic=meta)


def us_sessions():
    stock = WATCHLIST[2]
    fetched = datetime(2026, 11, 6, 5, 5, tzinfo=ET)
    regular = datetime(2026, 11, 5, 16, 0, tzinfo=ET)
    pre = datetime(2026, 11, 6, 5, 0, tzinfo=ET)
    return Quote(stock, 656.0, 780.0, -17.46, regular, fetched,
                 extended=(SessionPrice('프리', 707.11, 7.73, pre, '네이버 해외'),))


class CompactSessionQuoteTests(unittest.TestCase):
    def test_samsung_after_rises_versus_today_regular_even_if_yesterday_negative(self):
        q = korean_after(WATCHLIST[0], 188600, 193800, 201500)
        text = compact_quote_line(q)
        self.assertEqual(text, '삼성전자 19.4만 🔺 +2.76% A')
        self.assertNotIn('\n', text)
        self.assertNotIn('▽', text)
        self.assertAlmostEqual(q.percent, (193800 / 201500 - 1) * 100)
        detail = quote_line(q)
        self.assertIn('188,600원', detail)
        self.assertIn('193,800원', detail)
        self.assertIn('▲2.76% 정규장 대비', detail)
        self.assertIn('전일 종가 대비 -3.82%', detail)

    def test_hynix_after_rises_relative_to_regular(self):
        q = korean_after(WATCHLIST[1], 1130000, 1180000, 1264000)
        self.assertEqual(compact_quote_line(q), '하이닉스 118만 🔺 +4.42% A')
        self.assertNotIn('\n', compact_quote_line(q))

    def test_legacy_krx_regular_close_plus_nxt_after_is_positive(self):
        now = datetime(2026, 11, 6, 20, 0, tzinfo=KST)
        close = datetime(2026, 11, 6, 15, 30, tzinfo=KST)
        aft = AfterMarketQuote(231500, (231500 / 231000 - 1) * 100,
                               now, '장후', 'CLOSE', 'NXT')
        meta = DomesticQuoteMetadata('폴링', 'CLOSE', None, now, aft)
        quote = Quote(WATCHLIST[0], 230000, 231000, -0.43, close, now, domestic=meta)
        rendered = compact_quote_line(quote)
        self.assertEqual(rendered, '삼성전자 23.1만 🔺 +0.65% A')
        self.assertNotIn('\n', rendered)
        self.assertIn('NXT 장후 231,500원', quote_line(quote))
        self.assertIn('▲0.65% 정규장 대비', quote_line(quote))

    def test_unknown_regular_never_invents_direction(self):
        q = korean_after(WATCHLIST[0], 188600, 193800, 201500, known=False)
        text = compact_quote_line(q)
        self.assertIn('19.4만', text)
        self.assertIn('A 기준가?', text)
        self.assertNotIn('\n', text)
        self.assertNotIn('▽', text)
        self.assertIn('정규장 기준가 미확인', quote_line(q))

    def test_prior_day_korean_after_does_not_override_current_regular_quote(self):
        old = korean_after(WATCHLIST[0], 188600, 193800, 201500)
        stale = replace(old, fetched_at=old.fetched_at + timedelta(days=1))
        self.assertNotIn(' A', compact_quote_line(stale))
        self.assertIn('18.9만', compact_quote_line(stale))
        self.assertNotIn('19.4만', compact_quote_line(stale))
        self.assertNotIn('\n', compact_quote_line(stale))

    def test_premarket_compares_previous_regular(self):
        q = korean_after(WATCHLIST[0], 188600, 192000, 201500, session='장전')
        self.assertEqual(compact_quote_line(q), '삼성전자 19.2만 🔺 +1.80% P')

    def test_us_premarket_one_line_and_exact_price(self):
        q = us_sessions()
        self.assertEqual(compact_quote_line(q), '마이크론 $707.11 🔺 +7.73% P')
        self.assertNotIn('\n', compact_quote_line(q))
        self.assertIn('프리 $707.11', quote_line(q))
        self.assertEqual(q.price, 656.0)

    def test_us_after_priority_at_after_hours(self):
        q = us_sessions()
        after = datetime(2026, 11, 6, 16, 45, tzinfo=ET)
        q = replace(q, fetched_at=after,
                    market_time=datetime(2026, 11, 6, 15, 59, tzinfo=ET),
                    extended=(*q.extended, SessionPrice('애프터', 669.50, 2.06,
                                                        after - timedelta(minutes=5), 'Yahoo 분봉')))
        self.assertEqual(compact_quote_line(q), '마이크론 $669.50 🔺 +2.06% A')

    def test_group_quote_one_line_per_item_and_ids_unchanged(self):
        kr = korean_after(WATCHLIST[0], 188600, 193800, 201500)
        us = us_sessions()
        report = group_report('반도체', (WATCHLIST[0], WATCHLIST[2]),
                              fetcher=lambda stock: kr if stock.ticker == WATCHLIST[0].ticker else us)
        self.assertIn('1. 삼성전자 19.4만 🔺 +2.76% A', report)
        self.assertIn('2. 마이크론 $707.11 🔺 +7.73% P', report)
        self.assertNotIn('   └ ', report)
        self.assertIn('※ 5분 내 1~2', report)

    def test_us_regular_session_does_not_show_stale_premarket(self):
        quote = us_sessions()
        midday = datetime(2026, 11, 6, 12, 45, tzinfo=ET)
        quote = replace(quote, fetched_at=midday,
                        market_time=midday - timedelta(minutes=2))
        rendered = compact_quote_line(quote)
        self.assertEqual(rendered, '마이크론 $656 ▽ -17.46%')
        self.assertNotIn(' P', rendered)
        self.assertNotIn(' A', rendered)

    def test_full_watchlist_mobile_concise_message_stays_under_limit(self):
        k1 = korean_after(WATCHLIST[0], 188600, 193800, 201500)
        k2 = korean_after(WATCHLIST[1], 1130000, 1180000, 1264000)
        mu = us_sessions()
        all_quotes = [k1, k2]
        usa_prices = {'SKHY': 129.30, 'SNDK': 877.09, 'STX': 491.00, 'WDC': 281.50}
        for stock in WATCHLIST[2:]:
            if stock.ticker == '285A.T':
                current = datetime(2026, 11, 6, 15, 30, tzinfo=ZoneInfo('Asia/Tokyo'))
                all_quotes.append(Quote(stock, 8511, 9330, -8.72, current, current))
            elif stock.ticker == 'MU':
                all_quotes.append(mu)
            else:
                base = replace(mu, stock=stock)
                extra = SessionPrice('프리', usa_prices[stock.ticker], 5.18,
                                     mu.extended[0].market_time, '네이버 해외')
                all_quotes.append(replace(base, extended=(extra,)))
        lookups = {q.stock.ticker:q for q in all_quotes}
        report = memory7_report(fetcher=lambda stock:lookups[stock.ticker], use_cache=False)
        lines = report.splitlines()
        # 한 종목은 한 행, 전체 카카오톡 본문은 대략 400자 이내를 목표로 한다.
        self.assertEqual(len([line for line in lines if line[:2] in (
            '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.'))]), 8)
        self.assertLessEqual(len(report), 430)
        self.assertLessEqual(len(lines), 15)
        self.assertTrue(any(line == '9. 🔎 상세보기' for line in lines))
        self.assertEqual(len([line for line in lines if line.startswith('📡 ')]), 1)
        self.assertNotIn('[프리]',report)
        self.assertNotIn('[애프터]',report)

    def test_default_memory7_single_row_and_detail_separate(self):
        quotes = {
            '005930.KS': korean_after(WATCHLIST[0], 188600, 193800, 201500),
            'MU': us_sessions(),
        }
        fetcher = lambda stock: quotes.get(stock.ticker)
        brief = memory7_report(fetcher=fetcher, use_cache=False)
        self.assertIn('1. 삼성전자 19.4만 🔺 +2.76% A', brief)
        self.assertIn('3. 마이크론 $707.11 🔺 +7.73% P', brief)
        self.assertNotIn('   └', brief)
        self.assertIn('9. 🔎 상세보기', brief)
        long = memory7_report(fetcher=fetcher, use_cache=False, detailed=True)
        self.assertIn('🔎 메모리7 시세 상세 보기', long)
        self.assertIn('1. 삼성전자 : 188,600원', long)
        self.assertIn('   └ 시간외(거래소 미확인) 장후 193,800원', long)
        self.assertIn('   └ 프리 $707.11', long)
        self.assertIn('시세 출처 · 기준시각:', long)
        self.assertIn('9. ↩ 간략보기', long)

    def test_command_dispatch_to_readonly_detailed_view(self):
        with patch('app.market.memory7_report', return_value='detail') as rendering:
            self.assertEqual(execute_stock_command('주식', '메모리7 상세'), 'detail')
            rendering.assert_called_once_with(detailed=True)
        with patch('app.market.memory7_report', return_value='brief') as rendering:
            self.assertEqual(execute_stock_command('주식', '메모리7'), 'brief')
            rendering.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
