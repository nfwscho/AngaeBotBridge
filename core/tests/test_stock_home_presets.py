"""
앙개봇 2026-11-07 주식 홈 8개 메뉴·혼합 반도체주 19·미국시총10 검증
1. 주식 홈은 1 반도체주, 2 미국 시총10, 3 AI, 4 반도체기자재, 5 데센, 6 최근, 7 관심목록, 8 분석 순서를 절대 변경하지 않는다.
2. 사용자 지정 반도체주 19종목은 정확한 순서와 원래 KRW/JPY/USD 거래소별 통화/현지시각을 유지한다.
3. EWY는 iShares MSCI South Korea ETF, DRAM은 Roundhill Memory ETF 미국 종목코드로 조회하며 원본 환율이나 주가를 고정하지 않는다.
4. 미국 시총10 홈은 개인 DB에 기존 프리셋 그룹이 없어도 원래 US_MARKET_CAP_PRESET 10종목을 같은 순서로 조회한다.
5. AI 13종목·반도체기자재 19종목·데센 5종목은 기존 구성/번호/분석/99/0/00/선택 TTL을 변경하지 않는다.
6. 개인 반도체 그룹·메모리7 직접 명령·기존 주식그룹 CRUD·DB/로그/인증·Android UI 데이터는 삭제하지 않는다.
7. 개인 그룹 간략 시세에서 공통 ※ 무료 지연/5분 분석 두 줄을 빼되 정확한 거래시각과 99 상세보기를 보존한다.
8. 상세 시세에는 원래 시세 출처/지연 경고/종목별 정규장·프리/애프터 데이터를 보존한다.
9. 조회 실패시 개별 실패/총실패 건수를 남겨 2줄 푸터를 유지하고 임의 가격을 발명하지 않는다.
10. SQLite 메모리 DB와 시세 fetcher 모의 객체로만 테스트하며 운영 서버·계정·GitHub 외부 데이터는 건드리지 않는다.
"""
from __future__ import annotations

import sqlite3
import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.market import Stock, Quote, WATCHLIST
from app.sector_watchlists import SECTORS, get_page, sector_report, sector_argument
from app.selection_menu import StockSelectionMenus
from app.watchlists import US_MARKET_CAP_PRESET, group_report
from app.module_info import module_for


ORDER = (
    "005930.KS", "000660.KS", "MU", "SNDK", "285A.T", "WDC", "STX", "SKHY",
    "EWY", "DRAM", "NVDA", "TSM", "AMD", "INTC", "AVGO", "MRVL", "ARM", "QCOM", "ASML",
)


def quote(stock):
    moment = datetime(2026, 11, 6, 16, 0, tzinfo=ZoneInfo(stock.timezone_name))
    return Quote(stock, 100.0, 99.0, 1.010101, moment, moment, source="테스트 검증 시세")


class StockHomePresetTests(unittest.TestCase):
    def test_home_has_exactly_eight_choices_in_requested_order(self):
        menu = StockSelectionMenus()
        db = sqlite3.connect(":memory:")
        try:
            opened = menu.open("단체방", "사용자")
            expected = (
                "반도체주 시세", "미국 시총10 시세", "AI 주도주",
                "반도체 및 기자재", "데센 및 네트워크",
                "최근 사용한 주식 조회", "관심종목 목록", "종목별 분석",
            )
            for index, label in enumerate(expected, 1):
                self.assertIn(f"{index}. {label}", opened.reply)
            self.assertIn("5. 데센 및 네트워크\n\n6. 최근 사용한 주식 조회", opened.reply)
            self.assertNotIn("9. ", opened.reply)
            arg = menu.choose(db, "단체방", "사용자", "1").execute_argument
            self.assertEqual(arg, sector_argument("chip", 1, False))
        finally:
            db.close()

    def test_chip_tickers_and_currency_are_exactly_requested(self):
        chip = get_page("chip", 1)
        self.assertEqual(len(chip), 19)
        self.assertEqual(tuple(s.ticker for s in chip), ORDER)
        self.assertEqual(tuple(s.name for s in chip[:8]), (
            "삼성전자", "하이닉스", "마이크론", "샌디스크", "키오시아",
            "WDC", "씨게이트", "SKHY",
        ))
        self.assertEqual(tuple(s.name for s in chip[8:]), ORDER[8:])
        self.assertEqual(tuple(s.currency for s in chip), (
            "KRW", "KRW", "USD", "USD", "JPY", *("USD",) * 14,
        ))
        self.assertEqual(chip[0].timezone_name, "Asia/Seoul")
        self.assertEqual(chip[4].timezone_name, "Asia/Tokyo")
        self.assertEqual(chip[9].ticker, "DRAM")
        self.assertEqual(chip[8].ticker, "EWY")
        self.assertEqual(tuple(s.ticker for s in WATCHLIST), (
            "005930.KS", "000660.KS", "MU", "SKHY", "SNDK", "285A.T", "STX", "WDC",
        ))

    def test_us10_is_built_in_and_does_not_require_a_saved_group(self):
        us10 = get_page("us10", 1)
        self.assertEqual(tuple(s.ticker for s in us10), tuple(item[0] for item in US_MARKET_CAP_PRESET))
        self.assertEqual(tuple(s.name for s in us10), tuple(item[1] for item in US_MARKET_CAP_PRESET))
        self.assertEqual(len(us10), 10)
        report = sector_report("us10", fetcher=quote)
        self.assertIn("1. 엔비디아", report)
        self.assertIn("10. 일라이릴리", report)
        self.assertEqual(report.splitlines()[-1], "99. 🔎 상세보기")
        self.assertIn("📡 ", report)
        self.assertNotIn("※ 무료", report)

    def test_chip_all_19_rows_and_three_markets_remain_visible(self):
        fetched = []
        def capture(stock):
            fetched.append(stock.ticker)
            return quote(stock)
        report = sector_report("chip", fetcher=capture)
        self.assertCountEqual(fetched, ORDER)
        self.assertEqual(len(report.splitlines()), 22)
        for index, stock in enumerate(get_page("chip", 1), 1):
            self.assertTrue(any(row.startswith(f"{index}. {stock.name} ") for row in report.splitlines()))
        clock = report.splitlines()[-2]
        self.assertTrue(clock.startswith("📡 "))
        for market in ("KR", "US", "JP"):
            self.assertIn(market, clock)
        self.assertEqual(report.splitlines()[-1], "99. 🔎 상세보기")
        self.assertNotIn("※ 무료", report)
        self.assertNotIn("※ 5분", report)
        detail = sector_report("chip", fetcher=quote, detailed=True)
        self.assertIn("99. ↩ 간략보기", detail)
        self.assertIn("시세 출처 · 기준시각:", detail)

    def test_saved_group_compact_has_clock_plus_ninety_nine_only(self):
        group = (get_page("chip", 1)[0], get_page("chip", 1)[4], get_page("chip", 1)[2])
        report = group_report("반도체", group, fetcher=quote)
        self.assertEqual(report.splitlines()[-2].startswith("📡 "), True)
        self.assertEqual(report.splitlines()[-1], "99. 🔎 상세보기")
        self.assertNotIn("※ 무료·지연", report)
        self.assertNotIn("※ 5분 내", report)
        detail = group_report("반도체", group, fetcher=quote, detailed=True)
        self.assertIn("※ 무료·지연 가능·실시간 아님", detail)
        self.assertIn("※ 5분 내 1~3: 종목 분석", detail)
        self.assertIn("99. ↩ 간략보기", detail)

    def test_duplicate_menu_source_is_correct_for_both_new_quote_types(self):
        for title in ("📊 반도체주 시세 (19종목)", "🔎 반도체주 시세 상세 (19종목)",
                      "📊 미국 시총10 시세 (10종목)"):
            self.assertEqual(module_for("메뉴", "경로 주식 1 99", title), "core.sector_watchlists")


if __name__ == "__main__":
    unittest.main()
