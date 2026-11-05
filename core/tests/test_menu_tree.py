"""
앙개봇 설정 전체 메뉴 트리 기능 회귀 테스트 — 구현 기능 전체와 보호 조건
1. 설정 메뉴 기존 1~6번을 유지하면서 7번 전체 메뉴 트리를 확인한다.
2. 홈·주식·분석·콘텐츠·설정의 실제 메뉴 정의와 계층 경로를 비교한다.
3. 미개발 항목과 방/발신자별 최근 조회·그룹·시세의 동적 항목 표기를 검증한다.
4. '설 7'/'앙 7 7'에 해당하는 인증된 API 경로와 설정 메뉴 복귀를 검증한다.
5. 0/00 이동, 5분 제한, 방/발신자 격리, request_id 중복 응답을 그대로 유지한다.
6. DB 스키마·원래 jobs/events 기록·Android 로그/UI/AI/주식시세 경로는 변경하지 않는다.
8. 설정 도움말은 기존 7번 전체 트리 다음의 8번으로 추가되어 함께 표시된다.
7. 카카오톡/Termux/외부 시세 접근 없이 TestClient와 임시 SQLite만 사용한다.
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app
from app.selection_menu import CONTENT_ITEMS, StockSelectionMenus


class MenuTreeUnitTests(unittest.TestCase):
    def test_tree_matches_actual_home_stock_settings_and_categories(self):
        tree = StockSelectionMenus.menu_tree()
        for i, choice in enumerate(StockSelectionMenus._home_choices(), 1):
            self.assertIn(f"{i}. {choice.label}", tree)
        for i, choice in enumerate(StockSelectionMenus._stock_choices(), 1):
            self.assertIn(f"1-{i}. {choice.label}", tree)
        for i, choice in enumerate(StockSelectionMenus._settings_choices(), 1):
            self.assertIn(f"7-{i}. {choice.label}", tree)
        for i, choice in enumerate(StockSelectionMenus._analysis_choices(), 1):
            self.assertIn(f"1-6-{i}. {choice.label}", tree)
        for root, category in enumerate(CONTENT_ITEMS, 2):
            for i, label in enumerate(CONTENT_ITEMS[category], 1):
                self.assertIn(f"{root}-{i}. {label} [개발 예정]", tree)

    def test_tree_describes_dynamic_branches_without_exposing_records(self):
        tree = StockSelectionMenus.menu_tree()
        self.assertIn("7-7. 전체 메뉴 트리", tree)
        self.assertIn("7-8. 도움말", tree)
        self.assertIn("1-1. 최근 사용한 주식 조회 [본인 최근 조회 목록]", tree)
        self.assertIn("1-5. 관심종목 목록 [본인 관심그룹 목록]", tree)
        self.assertIn("1-2. 메모리7 현재 시세 [조회 후 종목 선택]", tree)
        self.assertIn("설 7", tree)
        self.assertNotIn("X-AngaeBot-Token", tree)

    def test_settings_selection_preserves_existing_numbers(self):
        menus = StockSelectionMenus()
        db = sqlite3.connect(":memory:")
        try:
            menus.open_settings("방", "나")
            tree_request = menus.choose(db, "방", "나", "7")
            self.assertEqual(tree_request.execute_argument, "설정보기 tree")
            self.assertEqual(tree_request.back, "settings")
            back = menus.open_settings("방", "나")
            self.assertIn("7. 전체 메뉴 트리", back.reply)
            self.assertIn("6. 최근 오류", back.reply)
            self.assertIn("8. 도움말", back.reply)
            self.assertIn("1. 서버·서비스 상태", back.reply)
        finally:
            db.close()


class MenuTreeAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dbpath = Path(self.temp.name) / "menu-tree.db"
        self.client = TestClient(create_app("T" * 64, self.dbpath))
        self.headers = {"X-AngaeBot-Token": "T" * 64}
        self.n = 0

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def post(self, arg: str, *, room="방", sender="나", authorized=True, request_id=None):
        self.n += 1
        return self.client.post(
            "/v1/commands",
            headers=self.headers if authorized else {},
            json={"request_id": request_id or f"tree_{self.n:012d}",
                  "command": "메뉴", "argument": arg, "room": room, "sender": sender},
        )

    def test_direct_settings_path_and_home_path_with_back(self):
        self.assertEqual(self.post("경로 설정 7", authorized=False).status_code, 401)
        first = self.post("경로 설정 7").json()
        self.assertTrue(first["ok"], first)
        self.assertTrue(first["menu_active"])
        self.assertIn("앙개봇 전체 메뉴 트리", first["reply"])
        self.assertIn("7-7. 전체 메뉴 트리", first["reply"])
        self.assertIn("⚙️ 설정·운영 메뉴", first["reply"])
        self.assertEqual(first["module_source"], "core.menu")
        self.assertIn("앙개봇 메인 메뉴", self.post("선택 0").json()["reply"])

        via_home = self.post("경로 홈 7 7").json()
        self.assertTrue(via_home["ok"], via_home)
        self.assertIn("전체 메뉴 트리", via_home["reply"])
        self.assertIn("앙개봇 메인 메뉴", self.post("선택 00").json()["reply"])

    def test_tree_no_market_calls_and_existing_logs_remain(self):
        with patch("app.main.execute_stock_command", side_effect=AssertionError("market call")), patch(
            "app.main.fetch_history", side_effect=AssertionError("history call")
        ), patch("app.main.get_ai_reply", side_effect=AssertionError("AI call")):
            result = self.post("경로 설정 7").json()
            self.assertTrue(result["ok"], result)
            self.assertIn("최근 오류", result["reply"])
        with sqlite3.connect(self.dbpath) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
                             db.execute("SELECT COUNT(*) FROM events").fetchone()[0])

    def test_scope_and_idempotent_response(self):
        self.post("설정", room="방", sender="나")
        self.assertFalse(self.post("선택 7", sender="다른사람").json()["ok"])
        request_id = "menu_tree_repeat_0001"
        first = self.post("선택 7", request_id=request_id).json()
        second = self.post("선택 7", request_id=request_id).json()
        self.assertTrue(first["ok"], first)
        self.assertEqual(first["reply"], second["reply"])
        self.assertTrue(second["duplicate"])


if __name__ == "__main__":
    unittest.main()
