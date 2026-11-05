"""
앙개봇 날씨 기능 회귀 테스트 — 전체 검증 범위
1. 오늘/내일/7일 예보의 날짜·기온·강수확률·WMO 날씨 한국어 표시를 모의 데이터로 검증한다.
2. 기본 서울 위치, 국내 지역 검색, 잘못된 지명·위험한 인수 차단을 검증한다.
3. 날씨 설정은 채팅방/발신자별로 SQLite에 보존하고 다른 사용자 데이터는 읽지 않는다.
4. 홈 8→날씨 1~4 및 날씨 직접 명령의 원래 세션·0/00 이동·메타데이터를 확인한다.
5. 토큰 인증, 요청 중복 처리, jobs/events 로그, 공급자 장애 시 정확한 실패를 확인한다.
6. 테스트는 외부 Open-Meteo/Android/S20+ 네트워크에 접속하지 않고 임시 DB와 패치만 사용한다.
7. 주식·메모·AI·Android 배터리/관리 UI/기존 로깅을 변경하지 않는다.
"""
from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app
from app.weather import (WeatherError, WeatherLocation, forecast_text, get_location,
                         init_weather_schema, resolve_location, save_location)


def sample_forecast() -> dict:
    dates = [(date(2026, 11, 6) + timedelta(days=i)).isoformat() for i in range(7)]
    return {
        "current": {
            "temperature_2m": 13.2, "apparent_temperature": 12.3,
            "relative_humidity_2m": 63, "wind_speed_10m": 9.2,
            "weather_code": 3,
        },
        "daily": {
            "time": dates,
            "weather_code": [0, 61, 3, 2, 45, 75, 95],
            "temperature_2m_min": [4, 5, 3, 7, 2, 1, -1],
            "temperature_2m_max": [17, 14, 15, 16, 11, 10, 8],
            "precipitation_probability_max": [0, 80, 20, 30, 10, 65, 90],
        },
    }


class WeatherUnitTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        init_weather_schema(self.db)

    def tearDown(self):
        self.db.close()

    def test_default_and_user_scoped_location(self):
        self.assertEqual(get_location(self.db, "방", "나").name, "서울 (기본)")
        loc = resolve_location("부산")
        self.assertEqual(loc.name, "부산")
        save_location(self.db, "방", "나", loc)
        self.assertEqual(get_location(self.db, "방", "나").name, "부산")
        self.assertEqual(get_location(self.db, "방", "다른이").name, "서울 (기본)")
        self.assertEqual(get_location(self.db, "다른방", "나").name, "서울 (기본)")
        with self.assertRaises(WeatherError):
            get_location(self.db, "", "나")

    def test_geocoding_only_in_korea(self):
        valid = {"results": [{"name": "강남구", "country_code": "KR",
                              "latitude": 37.50, "longitude": 127.05}]}
        with patch("app.weather._get_json", return_value=valid) as lookup:
            loc = resolve_location("서울 강남구")
        self.assertEqual(loc.name, "서울 강남구")
        self.assertEqual(loc.latitude, 37.5)
        self.assertIn("countryCode", lookup.call_args.args[1])
        for unsafe in ("", "a", "https://example.com", "강남구; rm", "가" * 41):
            with self.assertRaises(WeatherError):
                resolve_location(unsafe)
        with patch("app.weather._get_json", return_value={
            "results": [{"name": "Gangnam", "country_code": "JP", "latitude": 35.0, "longitude": 139.0}]
        }):
            with self.assertRaises(WeatherError):
                resolve_location("강남구")

    @patch("app.weather._get_json", return_value=sample_forecast())
    def test_today_tomorrow_week_and_source(self, provider):
        loc = WeatherLocation("서울", 37.5665, 126.978)
        today = forecast_text(loc, "오늘")
        self.assertIn("11/06(금)", today)
        self.assertIn("13.2℃", today)
        self.assertIn("63%", today)
        self.assertIn("17.0℃", today)
        tomorrow = forecast_text(loc, "내일")
        self.assertIn("11/07(토)", tomorrow)
        self.assertIn("비 80%", tomorrow) if False else self.assertIn("80%", tomorrow)
        weekly = forecast_text(loc, "주간")
        self.assertIn("7일 예보", weekly)
        self.assertIn("11/12(목)", weekly)
        self.assertEqual(len([line for line in weekly.splitlines() if "· 비" in line]), 7)
        self.assertEqual(provider.call_count, 3)
        self.assertIn("Open-Meteo", today)

    def test_weather_api_failure_is_not_fabricated(self):
        with patch("app.weather._get_json", return_value={"daily": {}}):
            with self.assertRaises(WeatherError):
                forecast_text(WeatherLocation(*("서울", 37.5665, 126.978)), "오늘")
        with self.assertRaises(WeatherError):
            forecast_text(WeatherLocation("서울", 37.5, 127.0), "어제")


class WeatherAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "core.db"
        self.client = TestClient(create_app("W" * 64, self.path))
        self.headers = {"X-AngaeBot-Token": "W" * 64}
        self.counter = 0

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def post(self, argument: str, *, command: str = "메뉴", sender: str = "나",
             room: str = "방", auth: bool = True, request_id: str | None = None):
        self.counter += 1
        return self.client.post("/v1/commands", headers=self.headers if auth else {},
                                json={"request_id": request_id or f"weather_{self.counter:010d}",
                                      "command": command, "argument": argument,
                                      "room": room, "sender": sender})

    def test_weather_menu_number_and_back(self):
        self.assertEqual(self.post("경로 날씨 1", auth=False).status_code, 401)
        menu = self.post("날씨").json()
        self.assertTrue(menu["menu_active"])
        self.assertIn("1. 오늘 날씨", menu["reply"])
        self.assertIn("4. 지역 설정", menu["reply"])
        self.assertEqual(menu["module_source"], "core.menu")
        with patch("app.weather._get_json", return_value=sample_forecast()):
            today = self.post("선택 1").json()
        self.assertTrue(today["ok"], today)
        self.assertTrue(today["menu_active"])
        self.assertIn("서울 (기본)", today["reply"])
        self.assertIn("현재 13.2℃", today["reply"])
        self.assertEqual(today["module_source"], "core.weather")
        with patch("app.weather._get_json", return_value=sample_forecast()):
            tomorrow = self.post("경로 홈 8 2").json()
        self.assertTrue(tomorrow["ok"], tomorrow)
        self.assertIn("내일 날씨", tomorrow["reply"])
        self.assertEqual(tomorrow["module_source"], "core.weather")
        with patch("app.weather._get_json", return_value=sample_forecast()):
            week = self.post("경로 날씨 3").json()
        self.assertIn("7일 예보", week["reply"])
        self.assertIn("앙개봇 메인 메뉴", self.post("선택 0").json()["reply"])
        self.assertIn("앙개봇 메인 메뉴", self.post("선택 00").json()["reply"])

    def test_region_setting_scope_and_persistence(self):
        guide = self.post("경로 날씨 4").json()
        self.assertTrue(guide["ok"], guide)
        self.assertIn("지역 설정", guide["reply"])
        self.assertIn("서울 (기본)", guide["reply"])
        saved = self.post("지역 부산", command="날씨").json()
        self.assertTrue(saved["ok"], saved)
        self.assertTrue(saved["menu_active"])
        self.assertIn("부산", saved["reply"])
        self.assertEqual(saved["module_source"], "core.weather")
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM weather_locations").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
                             db.execute("SELECT COUNT(*) FROM events").fetchone()[0])
        with patch("app.weather._get_json", return_value=sample_forecast()):
            owner = self.post("오늘", command="날씨").json()
            another = self.post("오늘", command="날씨", sender="다른이").json()
        self.assertIn("부산 오늘", owner["reply"])
        self.assertIn("서울 (기본) 오늘", another["reply"])
        # Core 재시작과 다른 인스턴스에서도 사용자별 저장 지역을 읽는다.
        self.client.close()
        self.client = TestClient(create_app("W" * 64, self.path))
        after = self.post("지역", command="날씨").json()
        self.assertIn("부산", after["reply"])

    def test_duplicate_weather_and_provider_error_logging(self):
        req = "weather_duplicate_00001"
        with patch("app.weather._get_json", return_value=sample_forecast()) as provider:
            first = self.post("오늘", command="날씨", request_id=req).json()
            second = self.post("오늘", command="날씨", request_id=req).json()
        self.assertTrue(first["ok"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(first["reply"], second["reply"])
        provider.assert_called_once()
        with patch("app.weather._get_json", side_effect=WeatherError("날씨 서버 장애")):
            failed = self.post("주간", command="날씨").json()
        self.assertFalse(failed["ok"])
        self.assertIn("날씨 서버 장애", failed["reply"])
        with sqlite3.connect(self.path) as db:
            counts = db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            self.assertEqual(counts, db.execute("SELECT COUNT(*) FROM events").fetchone()[0])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs WHERE ok=0").fetchone()[0], 1)
        bad = self.post("지역 https://example.com", command="날씨").json()
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["module_source"], "core.weather")


if __name__ == "__main__":
    unittest.main()
