"""
앙개봇 v0.7.4 부동산 10개 메뉴 회귀 테스트 — 전체 기능/보존 명세
1. 부동산 1~10 순서와 문자열을 사용자가 지정한 내용 그대로 검증한다.
2. 청구e편한세상·신당동 1/2번은 기존 부동산 메모의 제목/본문만 조회한다.
3. 메모는 카카오톡 채팅방·발신자 범위가 유지되며 다른 사용자의 기록은 노출되지 않는다.
4. 관련 메모가 없으면 사용자에게 등록법을 안내하고 부동산 메뉴 선택 상태를 유지한다.
5. 서울 전체 매매 추이·뉴스 3/4번은 미구현 상태를 명시하며 추정 숫자·가짜 뉴스는 표시하지 않는다.
6. 기존 매매/전세/월세 실거래가 조회는 5/6/7번을 통해 동일 공식 API 경로로 실행된다.
7. 기존 부동산 메모 목록/등록·검색 안내는 8/9번에서 그대로 유지한다.
8. 기존 조회지역 설정 안내는 10번, 지역 저장은 '부 지역 강남구' 명령으로 유지한다.
9. 메뉴 전체 트리와 연속 번호 경로는 10개 메뉴 정의와 정확히 같은 순서를 반환한다.
10. 기존 0 이전/00 홈, TTL, FastAPI 인증, jobs/events 로그, 기존 SQLite 테이블을 유지한다.
11. API는 모킹하고 테스트용 임시 DB 및 비밀이 아닌 가짜 값만 사용한다.
12. Android Bridge UI/배터리/기존 도움말·주식·AI 기능은 테스트에서도 수정하지 않는다.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("ANGAE_TOKEN", "T" * 64)

from fastapi.testclient import TestClient

from app.main import create_app
from app.real_estate import Deal
from app.selection_menu import StockSelectionMenus


LABELS = (
    "청구e편한세상 관련",
    "신당동 아파트 관련",
    "서울시 아파트 매매 추이",
    "부동산 관련 뉴스",
    "아파트 매매 실거래가",
    "아파트 전세 실거래가",
    "아파트 월세 실거래가",
    "최근 메모 목록",
    "메모 등록·검색 안내",
    "조회 지역 설정 안내",
)


class RealEstateTenItemMenuTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database = Path(self.tmp.name) / "ten-menu.db"
        self.client = TestClient(create_app("T" * 64, self.database))
        self.headers = {"X-AngaeBot-Token": "T" * 64}
        self.counter = 0

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def post(self, command: str, argument: str, *, room: str = "부동산방",
             sender: str = "소유자", auth: bool = True):
        self.counter += 1
        return self.client.post(
            "/v1/commands", headers=self.headers if auth else {},
            json={"request_id": f"estate_ten_{self.counter:07d}", "command": command,
                  "argument": argument, "room": room, "sender": sender},
        )

    def test_exact_ten_choices_help_tree_and_home(self):
        self.assertEqual([c.label for c in StockSelectionMenus._record_sector_choices("부동산")],
                         list(LABELS))
        menu = self.post("메뉴", "부동산").json()
        self.assertTrue(menu["ok"], menu)
        self.assertEqual(menu["module_source"], "core.menu")
        for index, label in enumerate(LABELS, 1):
            self.assertIn(f"{index}. {label}", menu["reply"])
        self.assertIn("부 5~7 실거래", StockSelectionMenus.help_report())
        tree = self.post("메뉴", "경로 설정 7").json()
        self.assertTrue(tree["ok"], tree)
        for index, label in enumerate(LABELS, 1):
            self.assertIn(f"2-{index}. {label}", tree["reply"])
        self.assertIn("2-3. 서울시 아파트 매매 추이 [개발 예정]", tree["reply"])
        self.assertIn("2-4. 부동산 관련 뉴스 [개발 예정]", tree["reply"])
        self.assertIn("2-10. 조회 지역 설정 안내", tree["reply"])
        self.assertEqual(self.post("메뉴", "선택 00").json()["menu_active"], True)

    def test_topic_memos_are_read_only_and_isolated(self):
        self.assertTrue(self.post("부동산", "추가 청구e편한세상 계약 | 보증금 정보").json()["ok"])
        self.assertTrue(self.post("부동산", "추가 신당동 아파트 | 방문 계획").json()["ok"])
        self.assertTrue(self.post("부동산", "추가 다른 단지 | 타인과 공유 금지").json()["ok"])
        first = self.post("메뉴", "경로 부동산 1").json()
        self.assertTrue(first["ok"], first)
        self.assertTrue(first["menu_active"])
        self.assertEqual(first["module_source"], "core.records")
        self.assertIn("청구e편한세상", first["reply"])
        self.assertNotIn("신당동 아파트", first["reply"])
        self.assertNotIn("타인과 공유 금지", first["reply"])
        detail = self.post("메뉴", "선택 1").json()
        self.assertIn("보증금 정보", detail["reply"])
        self.assertIn("부동산 메뉴", detail["reply"])
        self.assertIn("메인 메뉴", self.post("메뉴", "선택 0").json()["reply"])

        second = self.post("메뉴", "경로 부동산 2").json()
        self.assertTrue(second["menu_active"], second)
        self.assertIn("신당동 아파트", second["reply"])
        self.assertNotIn("청구e편한세상", second["reply"])

        another = self.post("메뉴", "경로 부동산 1", sender="다른사람").json()
        self.assertTrue(another["ok"], another)
        self.assertIn("관련 메모가 없습니다", another["reply"])
        self.assertNotIn("보증금 정보", another["reply"])
        self.assertTrue(another["menu_active"])
        self.assertIn("메인 메뉴", self.post("메뉴", "선택 0", sender="다른사람").json()["reply"])

    def test_reserved_trends_and_news_are_explicitly_pending(self):
        for num, expected in ((3, "서울시 전체"), (4, "뉴스 출처 검증")):
            with self.subTest(num=num):
                reply = self.post("메뉴", f"경로 부동산 {num}").json()
                self.assertTrue(reply["ok"], reply)
                self.assertTrue(reply["menu_active"])
                self.assertIn("개발 예정", reply["reply"])
                self.assertIn(expected, reply["reply"])
                self.assertIn("부동산 메뉴", reply["reply"])
                self.assertEqual(reply["module_source"], "core.menu")
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM personal_records").fetchone()[0], 0)

    def test_all_existing_menu_paths_and_region(self):
        self.assertTrue(self.post("실거래", "지역 강남구").json()["ok"])
        sale = Deal("2026-11-02", "테스트 아파트", 84.9, "4", 123456, 0)
        rent = Deal("2026-11-02", "테스트 아파트", 59.9, "2", 95000, 0)
        monthly = Deal("2026-11-02", "테스트 아파트", 59.9, "2", 10000, 250)
        with patch.dict(os.environ, {"MOLIT_API_KEY": "FAKE_TEST_KEY"}):
            for number, expected, deal in (
                (5, "매매", sale), (6, "전세", rent), (7, "월세", monthly)
            ):
                with self.subTest(number=number), patch(
                    "app.real_estate.fetch_month", return_value=[deal]
                ) as provider:
                    result = self.post("메뉴", f"경로 부동산 {number}").json()
                    self.assertTrue(result["ok"], result)
                    self.assertTrue(result["menu_active"])
                    self.assertEqual(result["module_source"], "core.real_estate")
                    self.assertIn("아파트 " + expected + " 실거래가", result["reply"])
                    self.assertIn("부 5~7 재조회", result["reply"])
                    self.assertEqual(provider.call_count, 3)

        self.assertTrue(self.post("부동산", "추가 관리 메모 | 검색되는 본문").json()["ok"])
        listing = self.post("메뉴", "경로 부동산 8").json()
        self.assertTrue(listing["menu_active"])
        self.assertIn("관리 메모", listing["reply"])
        self.assertIn("검색되는 본문", self.post("메뉴", "선택 1").json()["reply"])
        help_page = self.post("메뉴", "경로 부동산 9").json()
        self.assertTrue(help_page["ok"], help_page)
        self.assertIn("부동산 추가 제목 | 내용", help_page["reply"])
        region = self.post("메뉴", "경로 부동산 10").json()
        self.assertTrue(region["ok"], region)
        self.assertEqual(region["module_source"], "core.real_estate")
        self.assertIn("강남구", region["reply"])
        self.assertTrue(region["menu_active"])
        self.assertEqual(self.post("메뉴", "경로 부동산 10", auth=False).status_code, 401)
        with sqlite3.connect(self.database) as db:
            jobs = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            events = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            self.assertEqual(jobs, events)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM personal_records").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
