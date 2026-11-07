"""
앙개봇 개인 해야 할 일 등록/수정/완료/복원/삭제/번호 메뉴 전체 회귀 테스트
1. 인증 없는 접근을 차단하고 기존 jobs 요청 ID 중복 감지/기록 보존을 검증한다.
2. 첫 해야 할 일인 S20+ Extend Unlock 확인을 등록하고 1~10 번호로 상세 조회한다.
3. 개인 메뉴 기존 1~4번 및 새 5번, 0 이전/00 홈과 5분 조회 세션을 확인한다.
4. 완료와 복원은 삭제 없이 상태만 변경하고 날짜 정렬 및 검색이 유지되는지 확인한다.
5. 확인 없는 삭제, 다른 발신자·방의 조회/수정/삭제, 긴 제목/상세 내용과 잘못된 날짜를 거부한다.
6. 개인 기록/일정/주식/AI 및 기존 jobs/events 기록은 변경하지 않고 신규 테이블을 추가한다.
7. 임시 SQLite와 TestClient만 사용하며 실제 카카오톡/Termux/Google 계정에 접근하지 않는다.
8. v0.7.5 등록/수정/완료 시각(KST)과 고유 #번호, 항목 관리·2단계 삭제·취소·0/00를 테스트한다.
9. 숫자 선택 변경도 기존 인증·요청ID 중복 방지·타 사용자 격리·jobs/events 로깅을 유지한다.
10. v0.7.6 97/98 페이지, 1~10 고유 ID 선택, 이전 화면 필터 복원과 범위 분리를 검증한다.
11. 제목만 수정 시 기존 상세/기한/등록시각 보존, 명시적 |로 상세 비우기를 검증한다.
12. S20+·운영 DB·Android Bridge는 테스트하지 않고 임시 DB만 사용하여 기존 기능을 보존한다.
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import create_app
from app.selection_menu import StockSelectionMenus
from app.todos import TodoError, init_todos_schema, execute_todo_command


class TodoAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "todos.db"
        self.client = TestClient(create_app("Z" * 64, self.path))
        self.auth = {"X-AngaeBot-Token": "Z" * 64}
        self.index = 0

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def post(self, arg, *, command="할일", room="조우상", sender="조우상",
             request_id=None, authorized=True):
        self.index += 1
        return self.client.post("/v1/commands",
            headers=self.auth if authorized else {},
            json={"request_id": request_id or f"task_request_{self.index:08d}",
                  "command": command, "argument": arg, "room": room, "sender": sender})

    def test_registration_duplicate_and_numbered_personal_menu(self):
        self.assertEqual(self.post("목록", authorized=False).status_code, 401)
        initial = self.post("목록").json()
        self.assertTrue(initial["ok"], initial)
        self.assertIn("표시할 할 일이 없습니다", initial["reply"])
        self.assertNotIn("☐ S20+", initial["reply"])  # Never seed into unrelated rooms.

        identifier = "todo_same_request_0001"
        added = self.post("추가 S20+ Extend Unlock 확인 | PIN 설정한 상태에서 이미지 전송 시험",
                          request_id=identifier).json()
        self.assertTrue(added["ok"], added)
        self.assertEqual(added["module_source"], "core.todos")
        self.assertIn("#1", added["reply"])
        repeated = self.post("추가 S20+ Extend Unlock 확인 | PIN 설정한 상태에서 이미지 전송 시험",
                             request_id=identifier).json()
        self.assertTrue(repeated["duplicate"])
        self.assertEqual(added["reply"], repeated["reply"])

        home = self.post("홈", command="메뉴").json()
        self.assertIn("9. 🗂 개인 메모·일정", home["reply"])
        personal = self.post("선택 9", command="메뉴").json()
        self.assertTrue(personal["ok"], personal)
        self.assertIn("1. 최근 메모 목록", personal["reply"])
        self.assertIn("2. 다가오는 일정", personal["reply"])
        self.assertIn("3. 메모 등록·검색 안내", personal["reply"])
        self.assertIn("4. 일정 등록·관리 안내", personal["reply"])
        self.assertIn("5. ✅ 해야 할 일", personal["reply"])
        todos = self.post("선택 5", command="메뉴").json()
        self.assertTrue(todos["ok"], todos)
        self.assertTrue(todos["menu_active"])
        self.assertEqual(todos["module_source"], "core.todos")
        self.assertIn("S20+ Extend Unlock 확인", todos["reply"])
        self.assertIn("1. ☐", todos["reply"])
        detail = self.post("선택 1", command="메뉴").json()
        self.assertTrue(detail["ok"], detail)
        self.assertIn("PIN 설정한 상태", detail["reply"])
        self.assertIn("할 일 #1 관리", detail["reply"])
        self.assertIn("등록:", detail["reply"])
        self.assertIn("2026-", detail["reply"])
        self.assertIn("1. ✅ 완료 처리", detail["reply"])
        self.assertIn("2. ✏️ 제목·내용 수정 안내", detail["reply"])
        self.assertIn("3. 🗑️ 삭제", detail["reply"])
        self.assertIn("✅ 해야 할 일", self.post("선택 0", command="메뉴").json()["reply"])
        self.assertIn("개인 메뉴", self.post("선택 0", command="메뉴").json()["reply"])
        self.assertIn("앙개봇 메인 메뉴", self.post("선택 00", command="메뉴").json()["reply"])

    def test_numbered_task_management_safe_delete_and_timestamps(self):
        added = self.post("추가 Extend Unlock 자동전송 확인 | PIN 잠금 실험").json()
        self.assertTrue(added["ok"], added)
        self.assertIn("등록:", added["reply"])
        tasks = self.post("경로 개인 5", command="메뉴").json()
        self.assertTrue(tasks["menu_active"], tasks)
        self.assertIn("1. ☐ [#1] Extend Unlock", tasks["reply"])
        self.assertIn("등록", tasks["reply"])
        self.assertNotIn("✅ 완료", tasks["reply"])
        detail = self.post("선택 1", command="메뉴").json()
        self.assertIn("할 일 #1 관리", detail["reply"])
        self.assertIn("등록:", detail["reply"])
        self.assertIn("기한:", detail["reply"])
        edit = self.post("선택 2", command="메뉴").json()
        self.assertIn("할일 수정 1 새 제목", edit["reply"])
        self.assertIn("할 일 #1 관리", self.post("선택 0", command="메뉴").json()["reply"])
        delete_prompt = self.post("선택 3", command="메뉴").json()
        self.assertIn("삭제 확인", delete_prompt["reply"])
        self.assertIn("1. 🗑️ 이 할 일 영구 삭제 확인", delete_prompt["reply"])
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM personal_todos").fetchone()[0], 1)
        cancel = self.post("선택 2", command="메뉴").json()
        self.assertIn("할 일 #1 관리", cancel["reply"])
        self.assertIn("✅ 해야 할 일", self.post("선택 0", command="메뉴").json()["reply"])
        detail = self.post("선택 1", command="메뉴").json()
        self.assertIn("할 일 #1 관리", detail["reply"])
        done = self.post("선택 1", command="메뉴", request_id="task_complete_menu_0001").json()
        self.assertTrue(done["ok"], done)
        self.assertEqual(done["module_source"], "core.todos")
        self.assertIn("할 일 완료 #1", done["reply"])
        repeated = self.post("선택 1", command="메뉴", request_id="task_complete_menu_0001").json()
        self.assertTrue(repeated["duplicate"])
        self.assertEqual(repeated["reply"], done["reply"])
        completed = self.post("완료목록").json()
        self.assertIn("Extend Unlock", completed["reply"])
        self.assertIn("☑", completed["reply"])
        detail = self.post("선택 1", command="메뉴").json()
        self.assertIn("완료:", detail["reply"])
        self.assertIn("1. ↩️ 다시 할 일로 복원", detail["reply"])
        self.assertIn("할 일 #1 관리", detail["reply"])
        restored = self.post("선택 1", command="메뉴").json()
        self.assertTrue(restored["ok"], restored)
        self.assertIn("다시 해야 할 일", restored["reply"])
        self.assertIn("Extend Unlock", self.post("목록").json()["reply"])
        self.assertTrue(self.post("보기 1").json()["ok"])
        with sqlite3.connect(self.path) as db:
            registered, updated = db.execute(
                "SELECT created_at,updated_at FROM personal_todos WHERE id=1").fetchone()
            self.assertGreater(registered, 0)
            self.assertGreaterEqual(updated, registered)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
                             db.execute("SELECT COUNT(*) FROM events").fetchone()[0])

    def test_numbered_delete_requires_second_confirm_and_valid_scope(self):
        self.assertTrue(self.post("추가 삭제 전에 확인할 작업").json()["ok"])
        self.post("경로 개인 5", command="메뉴")
        self.post("선택 1", command="메뉴")
        confirm = self.post("선택 3", command="메뉴")
        self.assertTrue(confirm.json()["ok"])
        self.assertFalse(self.post("선택 1", command="메뉴", sender="다른사람").json()["ok"])
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM personal_todos").fetchone()[0], 1)
        delete = self.post("선택 1", command="메뉴").json()
        self.assertTrue(delete["ok"], delete)
        self.assertIn("할 일 #1 삭제 완료", delete["reply"])
        self.assertEqual(delete["module_source"], "core.todos")
        self.assertIn("표시할 할 일이 없습니다", delete["reply"])
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM personal_todos").fetchone()[0], 0)

    def test_due_date_complete_restore_search_and_confirm_delete(self):
        self.assertTrue(self.post("추가 2026-11-15 Extend Unlock 테스트 | Bluetooth 연결").json()["ok"])
        self.assertTrue(self.post("추가 업데이트 확인 | 배포 스크립트 시험").json()["ok"])
        listing = self.post("목록").json()
        self.assertIn("2026-11-15", listing["reply"])
        self.assertIn("☐", listing["reply"])
        self.assertIn("Extend Unlock", self.post("검색 Extend").json()["reply"])
        self.assertTrue(self.post("완료 1").json()["ok"])
        self.assertNotIn("Extend Unlock 테스트", self.post("목록").json()["reply"])
        self.assertIn("Extend Unlock 테스트", self.post("완료목록").json()["reply"])
        self.assertTrue(self.post("완료 1").json()["ok"])  # Idempotent action.
        self.assertTrue(self.post("복원 1").json()["ok"])
        self.assertIn("Extend Unlock 테스트", self.post("목록").json()["reply"])
        self.assertTrue(self.post("기한 1 없음").json()["ok"])
        self.assertIn("기한: 기한 없음", self.post("보기 1").json()["reply"])
        self.assertTrue(self.post("기한 1 2026-11-30").json()["ok"])
        self.assertIn("2026-11-30", self.post("보기 1").json()["reply"])
        self.assertTrue(self.post("수정 1 1차 테스트 완료 | 결과 저장").json()["ok"])
        self.assertIn("1차 테스트 완료", self.post("보기 1").json()["reply"])
        self.assertIn("2026-11-30", self.post("보기 1").json()["reply"])
        self.assertFalse(self.post("삭제 1").json()["ok"])
        self.assertTrue(self.post("삭제 1 확인").json()["ok"])
        self.assertFalse(self.post("보기 1").json()["ok"])
        self.assertIn("업데이트 확인", self.post("목록").json()["reply"])

    def test_scope_validation_and_private_records_intact(self):
        self.assertTrue(self.post("추가 비공개 작업").json()["ok"])
        for fields in ({"sender": "타인"}, {"room": "다른방"}):
            self.assertNotIn("비공개 작업", self.post("목록", **fields).json()["reply"])
            for action in ("보기 1", "완료 1", "복원 1", "삭제 1 확인", "수정 1 탈취"):
                self.assertFalse(self.post(action, **fields).json()["ok"], action)
        self.assertFalse(self.post("추가 " + "가" * 61).json()["ok"])
        self.assertFalse(self.post("추가 제목 | " + "가" * 601).json()["ok"])
        self.assertFalse(self.post("추가 2026-02-30 잘못된 날짜").json()["ok"])
        self.assertFalse(self.post("기한 1 2026-02-30").json()["ok"])
        self.assertTrue(self.post("추가 할인율 10%_ 확인").json()["ok"])
        self.assertIn("할인율 10%_", self.post("검색 %_").json()["reply"])
        self.assertNotIn("할인율 10%_", self.post("검색 존재하지않는값").json()["reply"])
        self.assertTrue(self.post("추가 기존 메모 보존", command="메모").json()["ok"])
        with sqlite3.connect(self.path) as db:
            names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({"personal_records", "personal_todos", "jobs", "events", "stock_groups"} <= names)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM personal_todos WHERE room='조우상'").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM personal_records").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
                             db.execute("SELECT COUNT(*) FROM events").fetchone()[0])

    def test_paginated_list_number_maps_to_stable_id_and_back(self):
        for i in range(1, 24):
            self.assertTrue(self.post(f"추가 항목 {i:02d}").json()["ok"])
        first = self.post("경로 개인 5", command="메뉴").json()
        self.assertTrue(first["ok"], first)
        self.assertIn("📄 1/3페이지 · 총 23건", first["reply"])
        self.assertIn("1. ☐ [#23]", first["reply"])
        self.assertIn("98. ▶ 다음 페이지", first["reply"])
        page2 = self.post("선택 98", command="메뉴").json()
        self.assertTrue(page2["ok"], page2)
        self.assertIn("📄 2/3페이지", page2["reply"])
        self.assertIn("1. ☐ [#13]", page2["reply"])
        item = self.post("선택 1", command="메뉴").json()
        self.assertIn("할 일 #13 관리", item["reply"])
        returned = self.post("선택 0", command="메뉴").json()
        self.assertIn("📄 2/3페이지", returned["reply"])
        self.assertIn("[#13]", returned["reply"])
        page3 = self.post("선택 98", command="메뉴").json()
        self.assertIn("📄 3/3페이지", page3["reply"])
        self.assertIn("1. ☐ [#3]", page3["reply"])
        self.assertNotIn("98. ▶", page3["reply"])
        self.assertFalse(self.post("선택 98", command="메뉴").json()["ok"])
        self.assertIn("📄 2/3페이지", self.post("선택 97", command="메뉴").json()["reply"])
        self.assertIn("앙개봇 메인 메뉴", self.post("선택 00", command="메뉴").json()["reply"])
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM personal_todos").fetchone()[0], 23)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
                             db.execute("SELECT COUNT(*) FROM events").fetchone()[0])

    def test_paginated_completed_and_search_remember_scope_and_filter(self):
        for i in range(1, 15):
            self.assertTrue(self.post(f"추가 필터작업 {i:02d} | 검색키").json()["ok"])
        self.assertTrue(self.post("추가 별도 기록").json()["ok"])
        for i in range(1, 13):
            self.assertTrue(self.post(f"완료 {i}").json()["ok"])
        done = self.post("완료목록").json()
        self.assertIn("📄 1/2페이지 · 총 12건", done["reply"])
        self.assertIn("98. ▶ 다음 페이지", done["reply"])
        done_page2 = self.post("선택 98", command="메뉴").json()
        self.assertIn("📄 2/2페이지 · 총 12건", done_page2["reply"])
        self.assertIn("☑", done_page2["reply"])
        self.assertIn("완료한 일", self.post("선택 0", command="메뉴").json()["reply"])
        search = self.post("검색 필터작업").json()
        self.assertIn("📄 1/2페이지 · 총 14건", search["reply"])
        self.assertIn("검색된 할 일", search["reply"])
        search_page2 = self.post("선택 98", command="메뉴").json()
        self.assertIn("📄 2/2페이지 · 총 14건", search_page2["reply"])
        self.assertNotIn("별도 기록", search_page2["reply"])
        detail = self.post("선택 1", command="메뉴").json()
        self.assertIn("할 일 #", detail["reply"])
        back = self.post("선택 0", command="메뉴").json()
        self.assertIn("📄 2/2페이지 · 총 14건", back["reply"])
        self.assertNotIn("별도 기록", back["reply"])
        other = self.post("검색 필터작업", sender="남").json()
        self.assertIn("표시할 할 일이 없습니다", other["reply"])
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM personal_todos").fetchone()[0], 15)

    def test_edit_title_only_retains_detail_due_date_and_created_at(self):
        created = self.post("추가 2030-11-10 원제목 | 지우면 안 되는 상세").json()
        self.assertTrue(created["ok"], created)
        with sqlite3.connect(self.path) as db:
            before = db.execute(
                "SELECT title,detail,due_date,created_at FROM personal_todos WHERE id=1").fetchone()
        self.assertTrue(self.post("수정 #1 변경된 제목").json()["ok"])
        with sqlite3.connect(self.path) as db:
            after = db.execute(
                "SELECT title,detail,due_date,created_at FROM personal_todos WHERE id=1").fetchone()
        self.assertEqual(after, ("변경된 제목", before[1], before[2], before[3]))
        self.assertIn("지우면 안 되는 상세", self.post("보기 1").json()["reply"])
        self.assertTrue(self.post("수정 1 비운 제목 |").json()["ok"])
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT title,detail,due_date,created_at FROM personal_todos").fetchone()
            self.assertEqual(row, ("비운 제목", "", "2030-11-10", before[3]))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
                             db.execute("SELECT COUNT(*) FROM events").fetchone()[0])

    def test_first_registration_and_menu_tree(self):
        tree = StockSelectionMenus.menu_tree()
        self.assertIn("9-5. ✅ 해야 할 일", tree)
        self.assertIn("개 5 해야 할 일", StockSelectionMenus.help_report())
        self.assertIn("해야 할 일", self.post("경로 개인 5", command="메뉴").json()["reply"])
        self.assertTrue(self.post("추가 S20+ Extend Unlock 확인").json()["ok"])
        self.assertIn("S20+ Extend Unlock 확인", self.post("경로 홈 9 5", command="메뉴").json()["reply"])
        self.assertIn("해야 할 일", self.post("선택 0", command="메뉴").json()["reply"])

if __name__ == "__main__":
    unittest.main()
