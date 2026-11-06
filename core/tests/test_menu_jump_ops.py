"""
앙개봇 v0.6.0 메뉴 점프·설정 운영 조회 회귀 테스트 — 전체 동작과 보호 조건
1. 기존 홈/주식/메모리7 메뉴의 다단계 번호 이동을 최종 명령까지 실행한다.
2. 중간 시세 HTTP 호출 없이 한 번에 종목 분석으로 이동한다.
3. 기존 단일 번호 0/00, 5분 TTL, 방·발신자 격리, API 토큰 및 request_id 중복 보호를 유지한다.
4. 날씨/설정 하위 메뉴의 번호 이동, 읽기 전용 진단 정보 및 메뉴 재표시를 검사한다.
5. 배포 기록은 실제 SHA가 없으면 미기록, 유효한 기록이 있으면 SHA를 표시한다.
6. 최근 실행 로그는 같은 채팅방과 발신자의 명령·시간·결과 상태만 표시하며 인수·타인 정보는 절대 출력하지 않는다.
7. 기존 주식·AI/로그·SQLite·설정·Android UI/배터리 기능은 그대로 보존한다.
8. 네트워크 연결·장치·서버 재시작·외부 파일 변경 없이 임시 SQLite DB와 mock만 사용한다.
9. 설정 메뉴의 8번 도움말을 기존 1~7 항목과 함께 읽기 전용 회귀 검증한다.
10. v0.7.1 홈 설정 경로는 10, 날씨는 8로 변경하고 직접 설 경로·기존 통계 조회를 보존한다.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app
from app.ops import deployment_report, recent_command_log
from app.selection_menu import StockSelectionMenus, MENU_TTL_SECONDS
from app.market import StockQuoteError


class MenuJumpCoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dbpath = Path(self.temp.name) / "ops-test.db"
        self.client = TestClient(create_app("Z" * 64, self.dbpath))
        self.headers = {"X-AngaeBot-Token": "Z" * 64}
        self.seq = 0

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def post(self, argument: str, *, room="친구방", sender="친구",
             command="메뉴", request_id=None, authorized=True):
        self.seq += 1
        return self.client.post("/v1/commands", headers=self.headers if authorized else {},
                                json={"request_id": request_id or f"jump_{self.seq:012d}",
                                      "command": command, "argument": argument,
                                      "room": room, "sender": sender})

    def test_direct_jump_single_then_numeric_selection_still_works(self):
        with patch("app.main.execute_stock_command", return_value="메모리7 시세 표") as quote:
            result = self.post("경로 주식 2").json()
            self.assertEqual(result["reply"], "메모리7 시세 표")
            self.assertTrue(result["menu_active"])
            quote.assert_called_once()
        with patch("app.main.fetch_history") as history, patch(
                "app.main.individual_report", return_value="2번 종목 분석"):
            selected = self.post("선택 2").json()
            self.assertTrue(selected["ok"])
            self.assertEqual(selected["reply"], "2번 종목 분석")
            self.assertEqual(history.call_args.args[0].ticker, "000660.KS")

    def test_direct_jump_two_and_three_levels_skip_quote_fetch(self):
        for route in ("경로 주식 2 2", "경로 홈 1 2 2", "경로 주식 5 1 2"):
            with self.subTest(route=route), patch(
                "app.main.execute_stock_command", side_effect=AssertionError("intermediate quote called")
            ), patch("app.main.fetch_history") as history, patch(
                "app.main.individual_report", return_value="SK하이닉스 분석"):
                answer = self.post(route).json()
                self.assertTrue(answer["ok"], answer)
                self.assertEqual(answer["reply"], "SK하이닉스 분석")
                self.assertTrue(answer["menu_active"])  # 0은 바로 이전 시세/그룹 목록으로 복귀
                self.assertEqual(history.call_args.args[0].ticker, "000660.KS")

    def test_jump_to_nested_menu_and_back(self):
        a = self.post("경로 홈 10").json()
        self.assertIn("설정·운영 메뉴", a["reply"])
        b = self.post("선택 0").json()
        self.assertIn("메인 메뉴", b["reply"])
        c = self.post("경로 홈 8").json()
        self.assertIn("날씨 메뉴", c["reply"])
        d = self.post("선택 00").json()
        self.assertIn("메인 메뉴", d["reply"])

    def test_settings_report_from_shortcut_path_and_scope(self):
        self.assertEqual(self.post("설정", authorized=False).status_code, 401)
        self.post("홈", room="타인방", sender="타인")
        self.post("경로 설정 3", room="타인방", sender="타인")
        self.post("경로 주식 6", room="친구방", sender="친구")
        report = self.post("경로 설정 3").json()
        self.assertTrue(report["ok"])
        self.assertTrue(report["menu_active"])
        self.assertIn("최근 명령 로그", report["reply"])
        self.assertIn("설정·운영 메뉴", report["reply"])
        self.assertNotIn("타인방", report["reply"])
        self.assertNotIn("타인", report["reply"])
        self.assertNotIn("경로 주식 6", report["reply"])
        self.assertIn("설정·운영 메뉴", self.post("선택 0").json()["reply"])
        self.assertIn("메인 메뉴", self.post("선택 0").json()["reply"])

    def test_settings_subsections_readonly(self):
        for number, expected in (("2", "배포 정보"), ("4", "설정 현황"),
                                 ("5", "명령 통계"), ("6", "최근 오류"), ("8", "도움말")):
            with self.subTest(number=number):
                answer = self.post("경로 설정 " + number).json()
                self.assertTrue(answer["ok"], answer)
                self.assertTrue(answer["menu_active"])
                self.assertIn(expected, answer["reply"])
        with sqlite3.connect(self.dbpath) as db:
            # Request+event logs continue to be one-to-one; no new tables or write side-effects.
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
                             db.execute("SELECT COUNT(*) FROM events").fetchone()[0])

    def test_jump_rejects_invalid_path_and_other_scope(self):
        self.assertFalse(self.post("경로 주식 11").json()["ok"])
        self.assertFalse(self.post("경로 주식 2 12").json()["ok"])
        self.assertFalse(self.post("경로 주식 2 2 2").json()["ok"])
        self.assertFalse(self.post("경로 주식 1 1 1 1 1 1").json()["ok"])
        self.post("홈")
        self.assertFalse(self.post("선택 1", sender="다른사람").json()["ok"])

    def test_duplicate_route_does_not_reexecute(self):
        request_id = "menujump_duplicate_request_001"
        with patch("app.main.fetch_history") as history, patch(
                "app.main.individual_report", return_value="분석"):
            first = self.post("경로 주식 2 2", request_id=request_id).json()
            second = self.post("경로 주식 2 2", request_id=request_id).json()
        self.assertTrue(first["ok"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(history.call_count, 1)


class MenuJumpUnitTests(unittest.TestCase):
    def test_timeout_and_scope(self):
        now = [10.0]
        menu = StockSelectionMenus(clock=lambda: now[0])
        db = sqlite3.connect(":memory:")
        try:
            menu.open_home("방", "나")
            with self.assertRaises(StockQuoteError):
                menu.choose(db, "방", "다른사람", "1")
            now[0] += MENU_TTL_SECONDS
            with self.assertRaises(StockQuoteError):
                menu.choose(db, "방", "나", "1")
        finally:
            db.close()

    def test_deployment_record_validation(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "meta.json"
            self.assertIn("미기록", deployment_report("0.6.0", info_path=path))
            path.write_text(json.dumps({"sha": "a" * 40,
                                        "branch": "feature/global-shortcut-menus-20261106",
                                        "android_updated": True,
                                        "deployed_at": "2026-11-06T05:00:00+09:00"}))
            result = deployment_report("0.6.0", info_path=path)
            self.assertIn("aaaaaaaaaaaa", result)
            self.assertIn("APK", result)
            path.write_text(json.dumps({"sha": "bad", "branch": "main"}))
            self.assertIn("미기록", deployment_report("0.6.0", info_path=path))

    def test_log_summary_no_args_or_other_room(self):
        db = sqlite3.connect(":memory:")
        try:
            db.execute("CREATE TABLE jobs(request_id TEXT, room TEXT, sender TEXT, command TEXT, "
                       "argument TEXT, result TEXT, ok INTEGER, created_at INTEGER)")
            db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)",
                       ("1", "방", "나", "메뉴", "비밀토큰ABC", "비밀토큰ABC", 1, 1600000000))
            db.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)",
                       ("2", "타인", "타인", "메뉴", "타인비밀123", "타인비밀123", 0, 1600000000))
            text = recent_command_log(db, "방", "나")
            self.assertIn("최근 명령 로그", text)
            for secret in ("비밀토큰ABC", "타인비밀123", "타인"):
                self.assertNotIn(secret, text)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
