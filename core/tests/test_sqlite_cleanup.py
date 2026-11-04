"""
앙개봇 v0.5.4 SQLite 연결 수명 검증 — 전체 테스트 기능 및 기존 동작 보존
1. FastAPI 인증·계산·중복 request_id·관심 그룹 생성·종목 등록/삭제/목록·한글 종목 분석을 재현한다.
2. 운영 DB 대신 임시 SQLite를 사용하며 .env/기존 로그/사용자 기록을 읽거나 변경하지 않는다.
3. 테스트용 sqlite3.Connection 하위 클래스가 모든 연결 생성과 close() 호출을 추적한다.
4. 정상 응답, 실패, 중복 요청 경로에서 앱이 close()를 모두 명시적으로 호출하는지 검사한다.
5. 외부 시세 조회는 mock 처리해 무료 API 제한/네트워크/OpenAI/자동매매/알림 기능에 영향을 주지 않는다.
6. 기존 128개 회귀 테스트를 삭제하지 않고 연결 검증 1개를 추가한다.
7. S20+ Android UI·Kakao 자동답장·메모리7·미국시총10·주식 분석 및 모든 운영 로그를 보존한다.
8. 실패 시 기존 Termux 안전 배포기에 따라 서버 재시작 전 중단하고 소스 백업으로 복원한다.
"""
from __future__ import annotations
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('ANGAE_TOKEN','T'*64)
from fastapi.testclient import TestClient
from app.main import create_app

class SQLiteLifetimeTests(unittest.TestCase):
    def test_all_server_connection_paths_close_explicitly(self):
        original_connect=sqlite3.connect
        opened=[]
        class TrackedConnection(sqlite3.Connection):
            def close(self):
                self.explicitly_closed=True
                return super().close()
        def tracked_connect(*args,**kwargs):
            connection=original_connect(*args,factory=TrackedConnection,**kwargs)
            connection.explicitly_closed=False
            opened.append(connection)
            return connection
        with tempfile.TemporaryDirectory() as folder:
            with patch('app.main.sqlite3.connect',new=tracked_connect):
                client=TestClient(create_app('Q'*64,Path(folder)/'test.db'))
                try:
                    def send(name,arg,key):
                        return client.post('/v1/commands',
                          headers={'X-AngaeBot-Token':'Q'*64},
                          json={'request_id':key,'command':name,'argument':arg,
                                'room':'본인방','sender':'본인'})
                    self.assertEqual(client.get('/v1/health').status_code,401)
                    self.assertTrue(send('계산','2+3','sqlite_cleanup_0001').json()['ok'])
                    self.assertTrue(send('계산','2+3','sqlite_cleanup_0001').json()['duplicate'])
                    self.assertTrue(send('주식','그룹생성 실험','sqlite_cleanup_0002').json()['ok'])
                    self.assertTrue(send('주식','추가 실험 MU 마이크론','sqlite_cleanup_0003').json()['ok'])
                    self.assertTrue(send('주식','목록','sqlite_cleanup_0004').json()['ok'])
                    with patch('app.main.fetch_history',return_value=object()):
                        with patch('app.main.individual_report',return_value='📈 모의 분석 결과'):
                            self.assertTrue(send('주식','분석 마이크론','sqlite_cleanup_0005').json()['ok'])
                    self.assertFalse(send('주식','삭제 실험 WDC','sqlite_cleanup_0006').json()['ok'])
                    self.assertTrue(send('주식','삭제 실험 MU','sqlite_cleanup_0007').json()['ok'])
                finally:
                    client.close()
        self.assertGreaterEqual(len(opened),8)
        self.assertTrue(all(conn.explicitly_closed for conn in opened),
                        'SQLite 연결 close()가 누락되었습니다.')

if __name__=='__main__':
    unittest.main()
