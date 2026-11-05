"""
앙개봇 전체 명령 간결형 출력 회귀 테스트 — 모든 기능 설명
1. 계산 결과는 기존 AST 안전 계산을 유지하며 카카오톡 표시만 짧게 한다.
2. 시간과 서버상태는 기존 명령 이름 및 동작을 유지하고 간결하게 출력한다.
3. 운영 상세상태는 runit/SSH 상태와 가동시간을 빠짐없이 보존한다.
4. AI OFF 상태는 실제 설정/보안 기능을 변경하지 않고 안내만 줄인다.
5. 주식 시세 출처는 한국/미국/일본별 날짜·출처·시각을 보존한다.
6. 기존 상세 시세 포맷과 5분 번호 선택/로그/SQLite 데이터는 수정하지 않는다.
7. 간결 시세의 상승 🔺 +, 하락 🔵▼ -, 보합 ➖ 표시를 회귀 검증한다.
"""
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from app.commands import execute_command
from app.ops import details, uptime_report
from app.ai_engine import AISettings
from app.market import Stock, Quote, compact_source_summary, compact_quote_line


class CompactAllReplyTests(unittest.TestCase):
    def test_calculation(self):
        self.assertEqual(execute_command("계산", "2+3*4", 0), "🧮 14")

    def test_time(self):
        self.assertTrue(execute_command("시간", "", 0).startswith("🕐 "))
        self.assertIn("KST", execute_command("시간", "", 0))

    def test_server_status(self):
        result = execute_command("서버상태", "", 125)
        self.assertIn("정상", result)
        self.assertIn("125초", result)

    def test_ops_preserve_all_status(self):
        result = details(3600, services=lambda name: "실행 중", ssh=lambda: "연결 가능")
        self.assertIn("Core 실행 중", result)
        self.assertIn("감시 실행 중", result)
        self.assertIn("SSH 실행 중", result)
        self.assertIn("8022 연결 가능", result)
        self.assertIn("1시간", result)
        self.assertIn("Core 기준", uptime_report(60))

    def test_ai_off(self):
        settings = AISettings(False, "openai", "https://api.openai.com/v1", "", "", 15, True, 6)
        result = settings.status_text()
        self.assertIn("AI OFF", result)
        self.assertIn("configure-ai.py", result)

    def test_compact_quote_direction_colors(self):
        stock = Stock("애플", "AAPL", "USD", "미국", "America/New_York")
        stamp = datetime(2026, 11, 5, 12, 12, tzinfo=ZoneInfo("America/New_York"))
        for pct, expected in ((5.31, "🔺 +5.31%"), (-3.17, "🔵▼ -3.17%"), (0.0, "➖ 0.00%")):
            quote = Quote(stock, 100, 100, pct, stamp, stamp)
            self.assertIn(expected, compact_quote_line(quote))

    def test_source_summary_keeps_provenance(self):
        stock = Stock("마이크론", "MU", "USD", "미국", "America/New_York")
        stamp = datetime(2026, 11, 5, 12, 12, tzinfo=ZoneInfo("America/New_York"))
        quote = Quote(stock, 100, 110, -9.09, stamp, stamp, source="나스닥 확정 종가")
        footer = compact_source_summary([quote])
        self.assertEqual(len(footer), 1)
        self.assertIn("미국 11/05", footer[0])
        self.assertIn("12:12", footer[0])
        self.assertIn("ET", footer[0])
        self.assertIn("확정 종가", footer[0])


if __name__ == "__main__":
    unittest.main()
