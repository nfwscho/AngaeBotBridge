"""
앙개봇 v0.5.5 주식 분석 API 회귀 테스트 — 기존 기능 및 안전 규칙 총정리
1. 인증 없는 과거 종가 요청을 HTTP 401로 차단하고 허용 티커·명령만 처리한다.
2. 단일 종목/메모리7/소유자 그룹 분석을 기존 /v1/commands 흐름으로 제공한다.
3. 다른 채팅방/발신자의 그룹은 조회·유출할 수 없음을 검증한다.
4. 중복 request_id는 저장된 답장을 반환하고 외부 시세 조회를 다시 실행하지 않는다.
5. 실패 응답도 jobs/events에 기록하며 기존 계산·AI상태·통계·시세 조회는 유지한다.
6. 가격 분석은 읽기 전용으로 처리하고 DB 그룹·로그 구조를 변형하지 않는다.
7. 테스트 시 외부 HTTP와 AI 호출을 모의 실행하여 무료 API 제한/키/실제 사용자 DB를 보호한다.
8. 이전 메모리7·미국시총10/반도체 그룹·Kakao Android 설정·로그에 영향을 주지 않는다.
9. 목표가 알림·주기적 감시·자동발신·주식 주문 기능을 의도적으로 추가하지 않는다.
10. v0.5.5 마이크론·삼성전자·하이닉스·미국시총10 한글 종목과 저장 별칭 분석을 검사한다.
11. v0.5.5 sqlite3.Connection 문맥 관리자는 연결 종료를 보장하지 않으므로 closing(...)으로 명시적으로 닫아 ResourceWarning을 방지한다.
"""
from __future__ import annotations
from contextlib import closing
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('ANGAE_TOKEN','T'*64)
from fastapi.testclient import TestClient
from app.main import create_app
from app.history import DailyBar, HistoryResult
from datetime import date
from app.market import StockQuoteError

class HistoryAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/'core.db'
        self.client=TestClient(create_app('Q'*64,self.db))
        self.header={'X-AngaeBot-Token':'Q'*64}
        self.count=0

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def send(self, arg='', command='주식', room='방', sender='주인', ident=None, auth=True):
        self.count+=1
        return self.client.post('/v1/commands',headers=self.header if auth else {},json={
            'request_id':ident or f'hist_test_{self.count:08d}',
            'command':command,'argument':arg,'room':room,'sender':sender})

    def test_single_auth_duplicate_and_event_log(self):
        self.assertEqual(self.send('분석 MU',auth=False).status_code,401)
        ident='history_same_00000001'
        with patch('app.main.fetch_history') as hist, patch('app.main.individual_report',return_value='5일 +3% / 1개월 σ20%'):
            a=self.send('분석 MU',ident=ident).json()
            b=self.send('분석 MU',ident=ident).json()
            self.assertTrue(a['ok'])
            self.assertEqual(a['reply'],b['reply'])
            self.assertTrue(b['duplicate'])
            hist.assert_called_once()
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM stock_items').fetchone()[0],0)

    def test_korean_company_names_and_scoped_aliases(self):
        with patch('app.main.fetch_history') as fetch, \
             patch('app.main.individual_report',return_value='5일 수익률 +2%'):
            for name, ticker in [('마이크론','MU'),('삼성전자','005930.KS'),
                                 ('하이닉스','000660.KS'),('엔비디아','NVDA'),
                                 ('애플','AAPL'),('웨스턴 디지털','WDC')]:
                result=self.send('분석 '+name).json()
                self.assertTrue(result['ok'], name)
                self.assertEqual(fetch.call_args.args[0].ticker, ticker)
        self.assertTrue(self.send('그룹생성 투자').json()['ok'])
        self.assertTrue(self.send('추가 투자 NVDA 나만의GPU').json()['ok'])
        with patch('app.main.fetch_history') as fetch, \
             patch('app.main.individual_report',return_value='5일 수익률 +2%'):
            self.assertTrue(self.send('분석 나만의GPU').json()['ok'])
            self.assertEqual(fetch.call_args.args[0].ticker,'NVDA')
            denied=self.send('분석 나만의GPU',room='외부방',sender='외부인').json()
            self.assertFalse(denied['ok'])
            self.assertEqual(fetch.call_count,1)
        self.assertTrue(self.send('그룹생성 별도').json()['ok'])
        self.assertTrue(self.send('추가 별도 AAPL 나만의GPU').json()['ok'])
        with patch('app.main.fetch_history') as fetch:
            ambiguous=self.send('분석 나만의GPU').json()
            self.assertFalse(ambiguous['ok'])
            self.assertIn('여러 종목',ambiguous['reply'])
            fetch.assert_not_called()

    def test_group_ownership_and_memory7(self):
        self.assertTrue(self.send('그룹생성 반도체').json()['ok'])
        self.assertTrue(self.send('추가 반도체 MU').json()['ok'])
        with patch('app.main.history_group_report',return_value='반도체 그룹 5일 · σ') as hist:
            res=self.send('분석 반도체').json()
            self.assertTrue(res['ok'])
            self.assertEqual(len(hist.call_args.args[1]),1)
            denied=self.send('분석 반도체',room='외부방',sender='외부인').json()
            self.assertFalse(denied['ok'])
            self.assertEqual(hist.call_count,1)
            mem=self.send('분석 메모리7').json()
            self.assertTrue(mem['ok'])
            self.assertEqual(len(hist.call_args.args[1]),8)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM stock_items').fetchone()[0],1)

    def test_errors_logged_and_prior_commands_unchanged(self):
        with patch('app.main.fetch_history',side_effect=StockQuoteError('일봉이 없습니다')):
            fail=self.send('분석 MU').json()
        self.assertFalse(fail['ok'])
        self.assertIn('일봉',fail['reply'])
        self.assertIn('56,088',self.send('123*456',command='계산').json()['reply'])
        self.assertIn('OFF',self.send(command='AI상태').json()['reply'])
        self.assertIn('v0.5.8',self.send(command='서버상태').json()['reply'])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs WHERE ok=0').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM events').fetchone()[0],4)

    def test_invalid_ticker_and_arguments_never_fetch(self):
        with patch('app.main.fetch_history') as fetch:
            for arg in ('분석','분석 MU MORE','분석 https://evil.test','분석 00;drop'):
                self.assertFalse(self.send(arg).json()['ok'])
            fetch.assert_not_called()
        with patch('app.main.fetch_history',side_effect=StockQuoteError('mock failure')):
            bad=self.send('분석 MU',ident='history_name_9876543')
        mismatch=self.send('분석 WDC',ident='history_name_9876543')
        self.assertEqual(mismatch.status_code,409)

if __name__=='__main__':unittest.main()
