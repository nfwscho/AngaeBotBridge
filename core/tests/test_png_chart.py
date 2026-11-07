"""
앙개봇 Python Core 차트 PNG와 인증 API 전체 회귀 테스트 — 기능 설명
1. 외부 이미지 라이브러리 없이 실제 일봉이 표현된 PNG 구조/차원/데이터를 검증한다.
2. 기존 인증 토큰 없는 이미지 다운로드는 HTTP 401을 반환해 데이터 유출을 차단한다.
3. 이미지 엔드포인트는 허용 종목코드만 사용하고 다른 도메인/파일·개인별 DB 그룹에 접근하지 않는다.
4. 날짜 역순, 종가 0/NaN, 데이터 부족 및 잘못된 종목은 가짜 그림 없이 안전하게 실패한다.
5. 정상 PNG 응답은 no-store, 정확한 MIME, PNG signature 및 IHDR와 zlib 압축 검증을 통과한다.
6. 기존 SQLite jobs, events, 개인 기록, 원래 시세 응답과 Python 토큰 설정은 유지한다.
7. mock 일봉만 사용하므로 실제 무료 시세 공급자에 접근하거나 API 사용량을 소모하지 않는다.
"""
from __future__ import annotations

from contextlib import closing
from datetime import date
import os
import sqlite3
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('ANGAE_TOKEN', 'X'*64)
from fastapi.testclient import TestClient
from app.history import DailyBar, HistoryResult
from app.main import create_app
from app.market import Stock
from app.png_chart import WIDTH, HEIGHT, ChartPngError, render_history_png


class ChartPngTests(unittest.TestCase):
    def setUp(self):
        self.stock = Stock("마이크론", "MU", "USD", "미국", "America/New_York")
        self.history = HistoryResult(self.stock, (
            DailyBar(date(2026, 10, 28), 140.4, 140.4),
            DailyBar(date(2026, 10, 29), 143.1, 143.1),
            DailyBar(date(2026, 10, 30), 138.0, 138.0),
            DailyBar(date(2026, 11, 2), 149.1, 149.1),
        ), "검증 데이터")

    def test_valid_png_and_pixel_data(self):
        output = render_history_png(self.history)
        self.assertTrue(output.startswith(b'\x89PNG\r\n\x1a\n'))
        length = struct.unpack(">I", output[8:12])[0]
        self.assertEqual(length, 13)
        self.assertEqual(output[12:16], b"IHDR")
        width, height, bit_depth, color_type = struct.unpack(">IIBB", output[16:26])
        self.assertEqual((width, height, bit_depth, color_type), (WIDTH, HEIGHT, 8, 2))
        self.assertLess(len(output), 1_200_000)
        index = 8
        rgba = []
        while index < len(output):
            size = struct.unpack(">I", output[index:index+4])[0]
            kind = output[index+4:index+8]
            data = output[index+8:index+8+size]
            crc = struct.unpack(">I", output[index+8+size:index+12+size])[0]
            self.assertEqual(zlib.crc32(kind+data) & 0xffffffff, crc)
            if kind == b'IDAT':
                rgba.append(data)
            index += 12+size
            if kind == b'IEND':
                break
        pixels = zlib.decompress(b''.join(rgba))
        self.assertEqual(len(pixels), HEIGHT*(1+WIDTH*3))
        self.assertEqual(pixels[0], 0)
        self.assertGreater(len(set(pixels[:20000])), 3)

    def test_invalid_data_fails_closed(self):
        for bars in (
            (),
            (self.history.bars[0],),
            (self.history.bars[1], self.history.bars[0]),
            (DailyBar(date(2026,11,1), 0., 0.), self.history.bars[3]),
            (DailyBar(date(2026,11,1), float('nan'), 0.), self.history.bars[3])
        ):
            with self.assertRaises(ChartPngError):
                render_history_png(HistoryResult(self.stock, bars, "test"))

    def test_authenticated_api_and_preexisting_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path=Path(tmp)/'core.db'
            with TestClient(create_app('T'*64, db_path)) as client:
                path='/v1/media/stock-chart?symbol=MU'
                self.assertEqual(client.get(path).status_code,401)
                with patch("app.main.fetch_history", return_value=self.history) as fetch:
                    res=client.get(path,headers={'X-AngaeBot-Token':'T'*64})
                self.assertEqual(res.status_code,200)
                self.assertEqual(res.headers["content-type"],"image/png")
                self.assertIn("no-store",res.headers["cache-control"])
                self.assertTrue(res.content.startswith(b'\x89PNG\r\n\x1a\n'))
                fetch.assert_called_once()
                self.assertEqual(fetch.call_args.args[0].ticker,"MU")
                with patch("app.main.fetch_history") as bad_fetch:
                    denied=client.get('/v1/media/stock-chart?symbol=https://evil.example',
                        headers={'X-AngaeBot-Token':'T'*64})
                    self.assertEqual(denied.status_code,422)
                    bad_fetch.assert_not_called()
                with closing(sqlite3.connect(db_path)) as db:
                    self.assertTrue({'personal_todos','personal_records','jobs','events'} <= {
                        r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")})
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],0)
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM events WHERE stage='MEDIA_STOCK_CHART_READY'").fetchone()[0],1)
                    self.assertEqual(db.execute("SELECT COUNT(*) FROM events WHERE stage='MEDIA_STOCK_CHART_FAILED'").fetchone()[0],1)

    def test_source_failure_no_fake_chart(self):
        with tempfile.TemporaryDirectory() as tmp:
            with TestClient(create_app('T'*64,Path(tmp)/'core.db')) as client:
                from app.market import StockQuoteError
                with patch("app.main.fetch_history", side_effect=StockQuoteError("공급자 연결 오류")):
                    r=client.get('/v1/media/stock-chart?symbol=MU',
                        headers={'X-AngaeBot-Token':'T'*64})
                self.assertEqual(r.status_code,422)
                self.assertNotEqual(r.headers.get("content-type"),"image/png")


if __name__=='__main__':
    unittest.main()
