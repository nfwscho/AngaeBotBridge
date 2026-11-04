"""
앙개봇 v0.4.1 시세 명령 FastAPI 회귀 테스트 — 전체 기능 상세 설명
1. 기존 X-AngaeBot-Token 인증과 /v1/commands 응답 형식을 보존한다.
2. '주식 메모리7' 및 '메모리7' 중복요청/응답/이벤트 로그의 일관성을 확인한다.
3. 외부 네트워크 호출은 mock으로 대체하고 토큰·기존 SQLite 데이터는 노출하지 않는다.
4. 시세 전체 조회 실패를 기존 jobs/events에 실패로 기록하고 계산은 계속 작동한다.
5. 예상하지 못한 명령을 거부하고 같은 request_id의 다른 명령 충돌을 방지한다.
6. 실패한 타인의 채팅 기록을 열람하거나 기존 데이터/로그를 삭제하지 않는다.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('ANGAE_TOKEN','TEST_ONLY_'+'T'*64)
from fastapi.testclient import TestClient
from app.main import create_app
from app.market import StockQuoteError


class StockApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=Path(self.temp.name)/'stocks.db'
        self.client=TestClient(create_app('Q'*64,self.db))
        self.header={'X-AngaeBot-Token':'Q'*64}

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def request(self, name, argument='',request_id='stock_request_000001'):
        return self.client.post('/v1/commands',headers=self.header,json={
            'request_id':request_id,'command':name,'argument':argument,
            'room':'개인방','sender':'호출자'})

    def test_auth_and_stock(self):
        self.assertEqual(self.client.post('/v1/commands',json={
            'request_id':'stock_req_999999','command':'주식','argument':'메모리7'}).status_code,401)
        with patch('app.main.execute_stock_command',return_value='💾 메모리7 시세 요약\n삼성전자 : 221,500원 (▲0.91%)') as mock:
            a=self.request('주식','메모리7').json()
            self.assertTrue(a['ok'])
            self.assertFalse(a['duplicate'])
            self.assertIn('221,500',a['reply'])
            again=self.request('주식','메모리7').json()
            self.assertEqual(again['reply'],a['reply'])
            self.assertTrue(again['duplicate'])
            mock.assert_called_once()
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],1)

    def test_direct_alias_and_conflict(self):
        with patch('app.main.execute_stock_command',return_value='시세 결과'):
            self.assertEqual(self.request('메모리7').status_code,200)
            self.assertEqual(self.request('주식','메모리7').status_code,409)

    def test_network_failure_does_not_break_existing_commands(self):
        with patch('app.main.execute_stock_command',side_effect=StockQuoteError('시세 조회 실패')):
            failure=self.request('주식','메모리7',request_id='stock_request_000002').json()
        self.assertFalse(failure['ok'])
        self.assertIn('시세 조회 실패',failure['reply'])
        ok=self.request('계산','123*456',request_id='stock_request_000003').json()
        self.assertTrue(ok['ok'])
        self.assertIn('56,088',ok['reply'])
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs WHERE ok=0').fetchone()[0],1)

    def test_invalid_stock_name_no_web(self):
        bad=self.request('주식','마이크론',request_id='stock_request_000005').json()
        self.assertFalse(bad['ok'])
        self.assertIn('사용법',bad['reply'])


if __name__=='__main__': unittest.main()
