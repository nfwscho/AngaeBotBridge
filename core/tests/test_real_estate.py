"""
앙개봇 부동산 실거래가 회귀 테스트 — 전체 보존 및 신규 검증 기능
1. 서울 25개 법정동구 코드·전국 5자리 조회 코드 입력, 유효하지 않은 지명 거부를 검증한다.
2. SQLite 방/발신자별 조회 지역 저장·재조회·미설정 오류·기존 DB 스키마 보존을 검증한다.
3. 국토부 XML 매매 및 전월세 필드 파싱·취소 계약 제거·전세/월세 구분을 검사한다.
4. 최근 3개월·최근 5건 계약일 정렬, 만원 환산, 단지명 필터 및 출처·지연 고지를 검사한다.
5. API 키 미설정/인증/HTTP/XML/페이지 누락·과다 오류에서 가격을 만들지 않음을 검증한다.
6. 기존 부동산 메모 메뉴 1/2를 유지하며 홈2→3/4/5, 부 지역·직접 조회, 0/00 이동을 검증한다.
7. 장문 '앙개야 부동산 시세' 및 부동산 기존 메모 CRUD를 동일 FastAPI 경로로 독립 검증한다.
8. 기존 jobs/events 로그·요청 중복·401 인증·core.real_estate 모듈 표시를 검사한다.
9. 네트워크와 S20+ 서비스·운영 DB·실제 공공데이터 키는 사용하지 않고 오프라인에서 실행한다.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("ANGAE_TOKEN", "R" * 64)

from fastapi.testclient import TestClient
from app.main import create_app
from app.real_estate import (
    Deal, District, RealEstateError, _deal_from_item, _fetch_xml, _money, _month_codes,
    fetch_month, get_saved_district, init_real_estate_schema, parse_transaction_query,
    region_help, resolve_district, save_district, transaction_report,
)


def sale_xml() -> ET.Element:
    return ET.fromstring("""<response><header><resultCode>00</resultCode></header>
    <body><items><item>
    <dealYear>2026</dealYear><dealMonth>11</dealMonth><dealDay>2</dealDay>
    <aptNm>래미안 원베일리</aptNm><excluUseAr>84.9</excluUseAr><floor>15</floor>
    <dealAmount>255,000</dealAmount><cdealType></cdealType>
    </item><item>
    <dealYear>2026</dealYear><dealMonth>11</dealMonth><dealDay>1</dealDay>
    <aptNm>취소된 집</aptNm><excluUseAr>59</excluUseAr><floor>3</floor>
    <dealAmount>10,000</dealAmount><cdealType>O</cdealType>
    </item></items><numOfRows>1000</numOfRows><totalCount>2</totalCount></body>
    </response>""")


def rent_xml() -> ET.Element:
    return ET.fromstring("""<response><header><resultCode>00</resultCode></header>
    <body><items>
    <item><dealYear>2026</dealYear><dealMonth>11</dealMonth><dealDay>1</dealDay>
    <aptNm>전세아파트</aptNm><excluUseAr>59.99</excluUseAr><floor>9</floor>
    <deposit>82,000</deposit><monthlyRent>0</monthlyRent></item>
    <item><dealYear>2026</dealYear><dealMonth>11</dealMonth><dealDay>3</dealDay>
    <aptNm>월세아파트</aptNm><excluUseAr>84.2</excluUseAr><floor>11</floor>
    <deposit>5,000</deposit><monthlyRent>150</monthlyRent></item>
    </items><totalCount>2</totalCount></body></response>""")


class RealEstateUnitTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        init_real_estate_schema(self.db)

    def tearDown(self):
        self.db.close()

    def test_regions_and_scope(self):
        self.assertEqual(resolve_district("강남구"), District("서울 강남구", "11680"))
        self.assertEqual(resolve_district("서울 동작구").code, "11590")
        self.assertEqual(resolve_district("서울특별시 용산구").code, "11170")
        self.assertEqual(resolve_district("41117").code, "41117")
        self.assertIsNone(get_saved_district(self.db, "방", "나"))
        save_district(self.db, "방", "나", resolve_district("강남구"))
        self.assertEqual(get_saved_district(self.db, "방", "나").code, "11680")
        self.assertIsNone(get_saved_district(self.db, "방", "다른사람"))
        self.assertIsNone(get_saved_district(self.db, "다른방", "나"))
        self.assertIn("11680", region_help(self.db, "방", "나"))
        for value in ("", "https://bad.example", "없는구", "123456", "중구; DELETE"):
            with self.assertRaises(RealEstateError):
                resolve_district(value)
        with self.assertRaises(RealEstateError):
            get_saved_district(self.db, "", "나")

    def test_query_parser_and_filter(self):
        with self.assertRaisesRegex(RealEstateError, "미설정"):
            parse_transaction_query(self.db, "방", "나", "시세")
        save_district(self.db, "방", "나", resolve_district("마포구"))
        kind, district, apartment = parse_transaction_query(self.db, "방", "나", "시세")
        self.assertEqual((kind, district.code, apartment), ("매매", "11440", ""))
        kind, district, apartment = parse_transaction_query(
            self.db, "방", "나", "매매 서울 강남구 래미안 원베일리")
        self.assertEqual((kind, district.code, apartment), ("매매", "11680", "래미안 원베일리"))
        kind, district, apartment = parse_transaction_query(self.db, "방", "나", "전세 단지 마포래미안")
        self.assertEqual((kind, district.code, apartment), ("전세", "11440", "마포래미안"))
        self.assertEqual(parse_transaction_query(self.db, "방", "나", "실거래조회 월세")[0], "월세")
        for invalid in ("매매 없는지명", "월세 단지", "매매 강남구 단지;해킹", "매매 !!!"):
            with self.assertRaises(RealEstateError):
                parse_transaction_query(self.db, "방", "나", invalid)

    def test_xml_mapping_and_cancel(self):
        sale = sale_xml().findall(".//items/item")
        self.assertEqual(_deal_from_item(sale[0], "매매").amount, 255000)
        self.assertEqual(_deal_from_item(sale[0], "매매").date, "2026-11-02")
        self.assertIsNone(_deal_from_item(sale[1], "매매"))
        rent = rent_xml().findall(".//items/item")
        self.assertEqual(_deal_from_item(rent[0], "전세").amount, 82000)
        self.assertEqual(_deal_from_item(rent[1], "월세").monthly, 150)
        self.assertIsNone(_deal_from_item(rent[0], "월세"))
        self.assertIsNone(_deal_from_item(rent[1], "전세"))
        self.assertEqual(_money(255000), "25억 5,000만원")
        self.assertEqual(_money(10000), "1억원")
        self.assertEqual(_money(150), "150만원")

    def test_fetch_api_pagination_and_errors(self):
        with patch("app.real_estate._fetch_xml", return_value=sale_xml()) as provider:
            rows = fetch_month("매매", resolve_district("강남구"), "202611", "testkey")
        self.assertEqual(len(rows), 1)
        endpoint, params = provider.call_args.args
        self.assertIn("AptTrade", endpoint)
        self.assertEqual(params["LAWD_CD"], "11680")
        self.assertEqual(params["DEAL_YMD"], "202611")
        root = sale_xml()
        root.find(".//totalCount").text = "4000"
        with patch("app.real_estate._fetch_xml", return_value=root):
            with self.assertRaisesRegex(RealEstateError, "조회 제한"):
                fetch_month("매매", resolve_district("강남구"), "202611", "key")
        root.find(".//totalCount").text = "wrong"
        with patch("app.real_estate._fetch_xml", return_value=root):
            with self.assertRaisesRegex(RealEstateError, "총건수"):
                fetch_month("매매", resolve_district("강남구"), "202611", "key")

    def test_provider_xml_failure_without_key_leaks(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"<response><header><resultCode>30</resultCode></header><body/></response>"
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_response
        with patch("app.real_estate.urlopen", return_value=mock_context):
            with self.assertRaisesRegex(RealEstateError, "API 키"):
                _fetch_xml("https://apis.data.go.kr/1613000/test", {"serviceKey": "privatekey"})
        mock_response.read.return_value = b"<not-valid"
        with patch("app.real_estate.urlopen", return_value=mock_context):
            with self.assertRaises(RealEstateError) as failure:
                _fetch_xml("https://apis.data.go.kr/1613000/test", {"serviceKey": "privatekey"})
        self.assertNotIn("privatekey", str(failure.exception))
        with self.assertRaises(RealEstateError):
            _fetch_xml("https://attacker.example/bad", {"serviceKey": "privatekey"})

    def test_report_filter_time_window_and_no_fabricated_values(self):
        self.assertEqual(len(_month_codes()), 3)
        district = resolve_district("강남구")
        with patch.dict(os.environ, {"MOLIT_API_KEY": ""}):
            with self.assertRaisesRegex(RealEstateError, "API 키"):
                transaction_report("매매", district)
        sample = [
            Deal("2026-11-01", "다른집", 84.3, "4", 100000),
            Deal("2026-11-03", "래미안 원베일리", 84.9, "15", 255000),
        ]
        with patch.dict(os.environ, {"MOLIT_API_KEY": "key"}):
            with patch("app.real_estate.fetch_month", return_value=sample) as provider:
                result = transaction_report("매매", district, "래미안")
        self.assertEqual(provider.call_count, 3)
        self.assertIn("25억 5,000만원", result)
        self.assertIn("계약 기간", result)
        self.assertIn("국토교통부", result)
        self.assertIn("현재 매물 호가", result)
        self.assertNotIn("다른집", result)
        self.assertNotIn("실시간 시세", result)
        with patch.dict(os.environ, {"MOLIT_API_KEY": "key"}):
            with patch("app.real_estate.fetch_month", return_value=[]):
                empty = transaction_report("전세", district)
        self.assertIn("신고 실거래 내역이 없습니다", empty)


class RealEstateAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "core.db"
        self.client = TestClient(create_app("E" * 64, self.path))
        self.headers = {"X-AngaeBot-Token": "E" * 64}
        self.counter = 0

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def post(self, command: str, argument: str, *, sender: str = "나", room: str = "방",
             request_id: str | None = None, auth: bool = True):
        self.counter += 1
        return self.client.post("/v1/commands", headers=self.headers if auth else {},
                                json={"request_id": request_id or f"estate_{self.counter:010d}",
                                      "command": command, "argument": argument,
                                      "room": room, "sender": sender})

    def test_menu_and_region_preserves_memo(self):
        self.assertTrue(self.post("부동산", "추가 전세 계약 | 실거주").json()["ok"])
        menu = self.post("메뉴", "부동산").json()
        self.assertTrue(menu["ok"], menu)
        self.assertIn("1. 최근 메모 목록", menu["reply"])
        self.assertIn("2. 메모 등록·검색 안내", menu["reply"])
        self.assertIn("3. 아파트 매매 실거래가", menu["reply"])
        self.assertIn("4. 아파트 전세 실거래가", menu["reply"])
        self.assertIn("5. 아파트 월세 실거래가", menu["reply"])
        self.assertEqual(menu["module_source"], "core.menu")
        guide = self.post("메뉴", "선택 6").json()
        self.assertTrue(guide["ok"], guide)
        self.assertIn("미설정", guide["reply"])
        self.assertEqual(guide["module_source"], "core.real_estate")
        updated = self.post("실거래", "지역 강남구").json()
        self.assertTrue(updated["ok"], updated)
        self.assertEqual(updated["module_source"], "core.real_estate")
        self.assertEqual(self.post("메뉴", "경로 부동산 1").json()["menu_active"], True)
        listing = self.post("메뉴", "선택 1").json()
        self.assertIn("실거주", listing["reply"])
        self.assertEqual(self.post("메뉴", "선택 0").json()["menu_active"], True)
        self.assertIn("메인 메뉴", self.post("메뉴", "선택 0").json()["reply"])
        self.assertEqual(self.post("메뉴", "선택 00").json()["menu_active"], True)

    def test_menu_direct_duplicate_and_logs(self):
        self.assertEqual(self.post("실거래", "매매 강남구", auth=False).status_code, 401)
        self.assertTrue(self.post("실거래", "지역 강남구").json()["ok"])
        self.assertFalse(self.post("실거래", "매매", sender="다른이").json()["ok"])
        sale = Deal("2026-11-02", "래미안 원베일리", 84.9, "15", 255000)
        request_id = "estate_repeat_0001"
        with patch.dict(os.environ, {"MOLIT_API_KEY": "test"}):
            with patch("app.real_estate.fetch_month", return_value=[sale]) as provider:
                first = self.post("메뉴", "경로 부동산 3", request_id=request_id).json()
                duplicate = self.post("메뉴", "경로 부동산 3", request_id=request_id).json()
        self.assertTrue(first["ok"], first)
        self.assertTrue(first["menu_active"], first)
        self.assertEqual(first["module_source"], "core.real_estate")
        self.assertIn("25억 5,000만원", first["reply"])
        self.assertEqual(duplicate["reply"], first["reply"])
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(provider.call_count, 3)
        with patch.dict(os.environ, {"MOLIT_API_KEY": "test"}):
            with patch("app.real_estate.fetch_month", return_value=[sale]):
                direct = self.post("부동산", "시세 강남구").json()
        self.assertTrue(direct["ok"], direct)
        self.assertEqual(direct["module_source"], "core.real_estate")
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM real_estate_regions").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
                             db.execute("SELECT COUNT(*) FROM events").fetchone()[0])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM personal_records").fetchone()[0], 0)

    def test_missing_key_rejection_and_legacy_record(self):
        self.assertTrue(self.post("실거래", "지역 동작구").json()["ok"])
        with patch.dict(os.environ, {"MOLIT_API_KEY": ""}):
            failed = self.post("실거래", "전세").json()
        self.assertFalse(failed["ok"], failed)
        self.assertEqual(failed["module_source"], "core.real_estate")
        self.assertIn("API 키", failed["reply"])
        self.assertTrue(self.post("부동산", "추가 계약 | 신규 메모").json()["ok"])
        records = self.post("부동산", "목록").json()
        self.assertTrue(records["ok"])
        self.assertIn("계약 (#1)", records["reply"])
        details = self.post("메뉴", "선택 1").json()
        self.assertIn("신규 메모", details["reply"])
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs WHERE ok=0").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
