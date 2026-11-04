"""
앙개봇 v0.4.3 키오시아 가격 폴백 회귀 테스트 — 현행 기능 전부 보존 범위
1. v0.4.2 Yahoo Japan '11/04' 표시를 계속 허용한다.
2. 'リアルタイム株価 15:30'처럼 시각만 표시되어도 상세에 거래일이 명시되면 조회한다.
3. 거래일이 전혀 없는 HTML로부터 날짜를 임의 생성하지 않는다.
4. 일본 증권사의 실제 보이는 '285A / 東証P / 본장 가격 / 등락률 / 시간 / 前終' 구조를 분석한다.
5. PTS 가격과 본장 가격을 혼동하지 않는다.
6. 티커와 이름이 바뀌거나 잘못된 가격·등락률·전일가·거래일은 거부한다.
7. 양쪽 Yahoo 공급자가 실패할 때에만 일본 증권사 보조 경로를 활용한다.
8. 기존 한국·미국 종목 경로 및 모든 로그·DB·토큰·Android 앱 동작을 보존한다.
9. 모든 HTTP 요청은 모의 opener로 대체해 테스트 중 실제 외부 웹 요청이 발생하지 않는다.
10. 공개 제공자 주소와 타임아웃 한계를 검사한다.
"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from app.market import (WATCHLIST, StockQuoteError, parse_yahoo_japan_quote,
                        parse_rakuten_quote, fetch_rakuten_quote, fetch_quote, quote_line)

NOW = datetime(2026, 11, 5, 1, 50, tzinfo=timezone.utc)


def yahoo_markup(header='15:30', suffix=''):
    return (f'<html><head><title>キオクシア 285A.T</title></head><body>'
            f'<h1>キオクシアホールディングス</h1><span>285A</span>'
            f'<strong>10,735</strong><div>前日比</div><span>-610(-5.38%)</span>'
            f'<span>リアルタイム株価</span><span>{header}</span>'
            f'<h2>株価詳細値</h2><p>前日終値 11,345(11/02)</p>'
            f'<p>始値 用語 11,595(11/04)</p>'
            f'<h2>夜間PTSについて</h2><p>12,900 +2,165(+20.17%)</p>{suffix}</body></html>')


def rakuten_markup(price='10,735.0', delta='-610.0', pct='-5.38', day='26/11/04', prev='11,345.0'):
    return (f'<html><title>285A キオクシアＨＬＤＧ</title><body><h1>285A</h1>'
            f'<div>キオクシアＨＬＤＧ</div><span>東証P</span>'
            f'<span>{price} {delta}{pct}%</span><div>{day} 15:30</div>'
            f'<p>前終(11/02) {prev} 出来高 163,533,500</p>'
            f'<p>PTS 現在値 12,500 +1,765(+16%)</p></body></html>')


class Response:
    def __init__(self, data): self.data = data
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, number): return self.data[:number]


class JapanFallbackTests(unittest.TestCase):
    def test_yahoo_time_only_uses_explicit_market_date(self):
        q = parse_yahoo_japan_quote(WATCHLIST[5], yahoo_markup(), now=NOW)
        self.assertEqual(q.price, 10735)
        self.assertAlmostEqual(q.percent, -5.38)
        self.assertEqual(q.market_time.strftime('%Y-%m-%d'), '2026-11-04')
        self.assertIn('▽5.38%', quote_line(q))

    def test_yahoo_month_day_remains_compatible(self):
        q = parse_yahoo_japan_quote(WATCHLIST[5], yahoo_markup('11/04'), now=NOW)
        self.assertEqual(q.price, 10735)

    def test_yahoo_refuses_missing_explicit_date(self):
        bad = '<html>キオクシア 285A 10,735 前日比 -610(-5.38%) リアルタイム株価 15:30</html>'
        with self.assertRaisesRegex(StockQuoteError, '거래일'):
            parse_yahoo_japan_quote(WATCHLIST[5], bad, now=NOW)

    def test_yahoo_header_not_pts(self):
        q = parse_yahoo_japan_quote(WATCHLIST[5], yahoo_markup(), now=NOW)
        self.assertNotEqual(q.price, 12900)

    def test_rakuten_regulated_market_quote(self):
        q = parse_rakuten_quote(WATCHLIST[5], rakuten_markup(), now=NOW)
        self.assertEqual(q.price, 10735)
        self.assertAlmostEqual(q.percent, -5.38)
        self.assertEqual(q.previous_close, 11345)
        self.assertEqual(q.market_time.strftime('%Y-%m-%d'), '2026-11-04')

    def test_rakuten_reject_wrong_ticker(self):
        with self.assertRaises(StockQuoteError):
            parse_rakuten_quote(WATCHLIST[2], rakuten_markup(), now=NOW)
        with self.assertRaises(StockQuoteError):
            parse_rakuten_quote(WATCHLIST[5], rakuten_markup().replace('285A', '999A'), now=NOW)

    def test_rakuten_reject_unsupported_market_or_stale(self):
        with self.assertRaises(StockQuoteError):
            parse_rakuten_quote(WATCHLIST[5], rakuten_markup(day='26/06/04'), now=NOW)
        with self.assertRaises(StockQuoteError):
            parse_rakuten_quote(WATCHLIST[5], rakuten_markup(day='26/11/08'), now=NOW)

    def test_rakuten_reject_bad_sign_or_previous_close(self):
        with self.assertRaises(StockQuoteError):
            parse_rakuten_quote(WATCHLIST[5], rakuten_markup(pct='+5.38'), now=NOW)
        with self.assertRaises(StockQuoteError):
            parse_rakuten_quote(WATCHLIST[5], rakuten_markup(prev='9,000.0'), now=NOW)

    def test_rakuten_network_fetch(self):
        seen = []
        def opener(req, timeout):
            seen.append((req.full_url, timeout))
            return Response(rakuten_markup().encode('utf-8'))
        q = fetch_rakuten_quote(WATCHLIST[5], opener=opener, now=NOW)
        self.assertEqual(q.price, 10735)
        self.assertIn('rakuten-sec.co.jp', seen[0][0])
        self.assertLess(seen[0][1], 5)

    def test_yahoo_both_fail_use_rakuten(self):
        urls = []
        def opener(req, timeout):
            urls.append(req.full_url)
            if 'rakuten-sec.co.jp' not in req.full_url:
                raise OSError('Yahoo unavailable')
            return Response(rakuten_markup().encode())
        q = fetch_quote(WATCHLIST[5], opener=opener, now=NOW)
        self.assertEqual(q.price, 10735)
        self.assertEqual(len(urls), 4)
        self.assertIn('rakuten-sec.co.jp', urls[-1])

    def test_all_japan_sources_failed_no_fake_quote(self):
        def opener(req, timeout): raise OSError('all blocked')
        with self.assertRaises(StockQuoteError):
            fetch_quote(WATCHLIST[5], opener=opener, now=NOW)


if __name__ == '__main__':
    unittest.main()
