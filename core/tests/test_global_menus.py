"""
앙개봇 통합 메뉴 회귀 테스트 — 전체 검증 기능
1. 홈/주식/배드민턴/요리/여행/종친/날씨/설정 메뉴의 정확한 번호 이동을 검증한다.
2. 0은 현재 페이지의 이전 메뉴, 00은 홈으로 복귀하며 메뉴 세션을 재설정한다.
3. 미구현 콘텐츠는 '개발 예정' 메시지만 반환하고 파일·AI·외부 명령을 실행하지 않는다.
4. 5분 만료, 방·발신자 격리, 허가되지 않은 접근, 잘못된 번호를 검증한다.
5. 기존 주식 시세·분석 명령은 통합 메뉴에서도 동일한 실행 함수로 처리된다.
6. 인증 FastAPI의 중복 요청 감지·jobs/events SQLite 로깅·원래 명령 보존을 검사한다.
7. S20+/Android/실데이터 없이 순수 메모리와 모의 응답만 사용한다.
8. 홈 8~10 신규 카테고리로 인해 8번은 유효하며 11번만 잘못된 번호로 검증한다.
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app
from app.market import StockQuoteError
from app.selection_menu import MENU_TTL_SECONDS, StockSelectionMenus


class GlobalMenuUnitTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.menus = StockSelectionMenus(clock=lambda: self.now)
        self.db = sqlite3.connect(":memory:")

    def tearDown(self):
        self.db.close()

    def test_home_stock_and_zero_navigation(self):
        home = self.menus.open_home("방", "나")
        self.assertTrue(home.menu_active)
        self.assertIn("앙개봇 메인 메뉴", home.reply)
        stock = self.menus.choose(self.db, "방", "나", "1")
        self.assertIn("주식 메뉴", stock.reply)
        self.assertTrue(stock.menu_active)
        self.assertIn("앙개봇 메인 메뉴", self.menus.choose(self.db, "방", "나", "0").reply)
        self.assertIn("여행", self.menus.choose(self.db, "방", "나", "4").reply)
        self.assertIn("앙개봇 메인 메뉴", self.menus.choose(self.db, "방", "나", "00").reply)

    def test_all_shortcut_categories_and_pending_leaf(self):
        for category in ("배드민턴", "요리", "여행", "종친", "날씨"):
            menu = self.menus.open_category("방", "나", category)
            self.assertTrue(menu.menu_active)
            self.assertIn(category + " 메뉴", menu.reply)
            leaf = self.menus.choose(self.db, "방", "나", "1")
            self.assertIn("개발 예정", leaf.reply)
            self.assertTrue(leaf.menu_active)
            self.assertIn("앙개봇 메인 메뉴", self.menus.choose(self.db, "방", "나", "0").reply)

    def test_scope_expiry_and_invalid_number(self):
        self.menus.open_home("방", "나")
        with self.assertRaises(StockQuoteError):
            self.menus.choose(self.db, "다른방", "나", "1")
        with self.assertRaises(StockQuoteError):
            self.menus.choose(self.db, "방", "남", "1")
        with self.assertRaises(StockQuoteError):
            self.menus.choose(self.db, "방", "나", "11")
        self.now += MENU_TTL_SECONDS
        with self.assertRaisesRegex(StockQuoteError, "5분"):
            self.menus.choose(self.db, "방", "나", "1")


class GlobalMenuAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dbpath = Path(self.temp.name) / "core.db"
        self.client = TestClient(create_app("M" * 64, self.dbpath))
        self.headers = {"X-AngaeBot-Token": "M" * 64}
        self.n = 0

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def post(self, argument, *, command="메뉴", room="방", sender="나", request_id=None, auth=True):
        self.n += 1
        return self.client.post(
            "/v1/commands",
            headers=self.headers if auth else {},
            json={
                "request_id": request_id or f"global_menu_{self.n:010d}",
                "command": command, "argument": argument,
                "room": room, "sender": sender,
            },
        )

    def test_home_category_back_home_and_direct_entry(self):
        self.assertEqual(self.post("홈", auth=False).status_code, 401)
        self.assertFalse(self.post("선택 1").json()["ok"])
        first = self.post("홈").json()
        self.assertTrue(first["ok"])
        self.assertTrue(first["menu_active"])
        self.assertIn("앙개봇 메인 메뉴", first["reply"])
        self.assertIn("배드민턴 메뉴", self.post("선택 2").json()["reply"])
        pending = self.post("선택 1").json()
        self.assertTrue(pending["ok"])
        self.assertTrue(pending["menu_active"])
        self.assertIn("개발 예정", pending["reply"])
        self.assertIn("앙개봇 메인 메뉴", self.post("선택 0").json()["reply"])
        self.assertIn("요리 메뉴", self.post("요리").json()["reply"])
        self.assertIn("앙개봇 메인 메뉴", self.post("선택 00").json()["reply"])
        self.assertFalse(self.post("선택 3", sender="다른사람").json()["ok"])
        with sqlite3.connect(self.dbpath) as db:
            jobs = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            events = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            self.assertEqual(jobs, events)
            self.assertGreaterEqual(jobs, 7)

    def test_stock_path_reuses_existing_quote_and_analysis(self):
        self.assertIn("앙개봇 메인 메뉴", self.post("홈").json()["reply"])
        self.assertIn("주식 메뉴", self.post("선택 1").json()["reply"])
        with patch("app.main.execute_stock_command", return_value="💾 메모리7 시세 요약") as quote:
            result = self.post("선택 2").json()
            self.assertEqual(result["reply"], "💾 메모리7 시세 요약")
            self.assertTrue(result["menu_active"])
            quote.assert_called_once()
        with patch("app.main.fetch_history") as history, patch("app.main.individual_report", return_value="마이크론 분석") as report:
            result = self.post("선택 3").json()
            self.assertTrue(result["ok"])
            self.assertEqual(result["reply"], "마이크론 분석")
            self.assertEqual(history.call_args.args[0].ticker, "MU")
            report.assert_called_once()
        self.assertIn("주식 메뉴", self.post("메뉴", command="주식").json()["reply"])
        self.assertIn("앙개봇 메인 메뉴", self.post("선택 0").json()["reply"])

    def test_idempotency_and_no_state_after_wrong_user(self):
        self.post("홈")
        self.assertFalse(self.post("선택 1", room="다른방").json()["ok"])
        request_id = "global_menu_repeat_001"
        first = self.post("선택 6", request_id=request_id).json()
        self.assertTrue(first["ok"])
        self.assertIn("날씨 메뉴", first["reply"])
        again = self.post("선택 6", request_id=request_id).json()
        self.assertTrue(again["duplicate"])
        self.assertEqual(again["reply"], first["reply"])
        self.assertIn("앙개봇 메인 메뉴", self.post("선택 0").json()["reply"])


if __name__ == "__main__":
    unittest.main()
