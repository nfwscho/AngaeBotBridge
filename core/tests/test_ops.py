"""
앙개봇 v0.5.6 운영 명령 회귀 테스트 — 전체 검사 기능 상세 안내
1. 인증 없는 운영 명령을 거부하고 응답 스키마·중복 요청 ID를 유지하는지 검사한다.
2. 통계에 저장된 Python 명령만 포함하며 조회 직전 건수로 집계하는지 검사한다.
3. 방/발신자별 SQLite 필터로 다른 대화의 명령·오류가 노출되지 않는지 검사한다.
4. 실패 응답은 기존 jobs 기록에서 가져오고 사용자 계산식 원문은 유출하지 않는지 검사한다.
5. 서비스 상태 조회는 읽기 전용 Mock을 사용해 SSH 및 runit 재시작을 수행하지 않는다.
6. 포맷된 가동시간과 Python Core 버전, AI OFF에서 기존 계산·시간·상태를 유지하는지 확인한다.
7. 운영 명령 실행 후 기존 jobs/events/AI 테이블은 모두 보존하는지 확인한다.
8. tests는 임시 SQLite DB를 이용하며 실제 Termux 토큰·로그·카카오톡을 변경하지 않는다.
9. v0.5.6 서버 버전 응답만 갱신하고 기존 운영 명령 테스트 조건을 유지한다.
10. 5거래일·21/63거래일 변동성 분석을 추가해도 기존 운영 상태/로그 검사는 변경하지 않는다.
11. v0.5.6 상태 문자열을 확인하면서 기존 계산/로그/AI OFF 회귀 검사 조건을 유지한다.
12. v0.5.6 sqlite3.Connection 문맥 관리자는 연결 종료를 보장하지 않으므로 closing(...)으로 명시적으로 닫아 ResourceWarning을 방지한다.
"""
from __future__ import annotations
from contextlib import closing

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("ANGAE_TOKEN", "T" * 64)
from fastapi.testclient import TestClient
from app.main import create_app
from app.ops import details, format_uptime


class OpsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dbpath = Path(self.tmp.name) / "core.db"
        self.client = TestClient(create_app("Q" * 64, self.dbpath))
        self.headers = {"X-AngaeBot-Token": "Q" * 64}
        self.next_id = 0

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def call(self, name, argument="", room="나의방", sender="테스터", request_id=None):
        self.next_id += 1
        return self.client.post("/v1/commands", headers=self.headers,
                                json={"request_id": request_id or f"ops_{self.next_id:010d}",
                                      "command": name, "argument": argument,
                                      "room": room, "sender": sender})

    def test_health_and_legacy_math(self):
        response = self.client.get("/v1/health", headers=self.headers)
        self.assertEqual(response.json()["version"], "0.6.2")
        self.assertIn("156,176", self.call("계산", "344*454").json()["reply"])
        self.assertIn("v0.6.2", self.call("서버상태").json()["reply"])
        self.assertIn("KST", self.call("시간").json()["reply"])

    def test_authentication_and_unknown_command(self):
        for command in ("상세상태", "통계", "최근오류", "가동시간"):
            response = self.client.post("/v1/commands", json={"request_id": "abcdefghij", "command": command})
            self.assertEqual(response.status_code, 401)
        self.assertEqual(self.call("rm -rf", "/").status_code, 400)

    def test_statistics_scoped_and_include_failed_commands(self):
        self.call("계산", "2*3")
        self.call("계산", "1/0")
        self.call("계산", "7*8", sender="다른사람")
        report = self.call("통계").json()["reply"]
        self.assertIn("전체 2", report)
        self.assertIn("성공 1", report)
        self.assertIn("실패 1", report)
        self.assertIn("계산: 2건", report)
        second = self.call("통계", sender="다른사람").json()["reply"]
        self.assertIn("전체 1", second)
        self.assertIn("성공 1", second)

    def test_errors_scoped_and_no_argument_leak(self):
        self.call("계산", "1/0")
        self.call("계산", "10/0", sender="다른사람")
        result = self.call("최근오류").json()["reply"]
        self.assertIn("0으로 나눌 수 없습니다", result)
        self.assertIn("계산", result)
        self.assertNotIn("10/0", result)
        self.assertNotIn("1/0", result)
        empty = self.call("최근오류", room="다른방").json()["reply"]
        self.assertIn("오류 없음", empty)

    def test_idempotent_stats_and_non_destructive_db(self):
        self.call("계산", "5*5", request_id="ops_unique_0001")
        again = self.call("계산", "5*5", request_id="ops_unique_0001")
        self.assertTrue(again.json()["duplicate"])
        self.call("통계")
        with closing(sqlite3.connect(self.dbpath)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 2)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone()[0], 2)
            tables = {x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({"jobs", "events", "ai_sessions", "ai_turns"} <= tables)

    def test_detail_status_mock_and_no_service_side_effect(self):
        called = []
        def status(name):
            called.append(name)
            return "실행 중"
        result = details(123, services=status, ssh=lambda: "연결 가능")
        self.assertEqual(called, ["angaebot-core", "angaebot-watchdog", "sshd"])
        self.assertIn("감시 실행 중", result)
        self.assertIn("8022 연결 가능", result)
        self.assertIn("0일 0시간 2분 3초", result)

    def test_api_detail_and_uptime(self):
        result = self.call("상세상태")
        self.assertTrue(result.json()["ok"])
        self.assertIn("서버 상세상태", result.json()["reply"])
        self.assertIn("SSH", result.json()["reply"])
        result = self.call("가동시간")
        self.assertTrue(result.json()["ok"])
        self.assertIn("Python 가동", result.json()["reply"])
        self.assertIn("KST", result.json()["reply"])

    def test_human_uptime_and_empty_stats(self):
        self.assertEqual(format_uptime(90061), "1일 1시간 1분 1초")
        result = self.call("통계")
        self.assertIn("전체 0", result.json()["reply"])


if __name__ == "__main__":
    unittest.main()
