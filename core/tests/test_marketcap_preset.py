"""
앙개봇 v0.5.1 미국시총10 프리셋/그룹 10종목 검증 — 기존 및 신규 전체 기능 상세
1. 기본 메모리7 8종목과 기존 시세·인증·로그·응답 구조가 동일함을 확인한다.
2. 신규 프리셋 10개 미국 기업의 티커·별칭·원화/달러/엔 라우팅·순서를 검사한다.
3. Alphabet 두 주식 클래스 중 GOOGL 한 번만 포함하고 해외 ADR을 제외한다.
4. 카카오톡 주식 명령 하나로 그룹 10개 종목이 정확히 생성되는지 확인한다.
5. 기존 반도체 등 사용자 그룹/종목을 덮어쓰지 않고 중복 생성 시 오류를 반환한다.
6. 10개 초과 등록을 거절하고 기존 메모리7은 수정/삭제할 수 없음을 검증한다.
7. 사용자·채팅방 간 관심종목은 SQLite에서 구분되어 다른 사용자가 열람할 수 없다.
8. 모든 시세 값은 모의 제공자로 만들며 실시간 API, AI, 거래 주문, 네트워크를 호출하지 않는다.
9. FastAPI 요청 인증과 동일 request_id 중복 방지를 유지하고 jobs/events 기존 로그를 보존한다.
10. 실제 Termux DB/.env/기존 로그를 변경하지 않고 임시 데이터베이스만 사용한다.
11. v0.5.4 SQLite 테스트 조회는 contextlib.closing을 사용해 트랜잭션뿐 아니라 연결도 명시적으로 닫으며 ResourceWarning을 방지한다.
"""
from __future__ import annotations
from contextlib import closing

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timezone

os.environ.setdefault('ANGAE_TOKEN', 'TEST_ONLY_'+'T'*64)
from fastapi.testclient import TestClient
from app.main import create_app
from app.market import WATCHLIST, Quote, StockQuoteError
from app.watchlists import (MAX_ITEMS, US_MARKET_CAP_PRESET, US_MARKET_CAP_PRESET_DATE,
                            init_schema, load_group, execute_group_command, group_report)


class MarketCapPresetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dbfile = Path(self.temp.name)/'data.db'
        self.db = sqlite3.connect(self.dbfile)
        init_schema(self.db)
        self.room = '개인방'
        self.sender = '사용자'

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def run_command(self, command, room=None, sender=None):
        return execute_group_command(self.db, room or self.room, sender or self.sender, command)

    def test_exact_snapshot_and_fixed_memory7_untouched(self):
        self.assertEqual(MAX_ITEMS, 10)
        self.assertEqual(US_MARKET_CAP_PRESET_DATE, '2026-11-04')
        self.assertEqual([x[0] for x in US_MARKET_CAP_PRESET],
                         ['NVDA','AAPL','MSFT','GOOGL','AMZN','SPCX','AVGO','META','TSLA','LLY'])
        self.assertEqual(len({x[0] for x in US_MARKET_CAP_PRESET}), 10)
        self.assertEqual(len(WATCHLIST),8)
        self.assertEqual(WATCHLIST[0].ticker, '005930.KS')
        self.assertEqual(WATCHLIST[5].ticker, '285A.T')
        self.assertNotIn('GOOG',[x[0] for x in US_MARKET_CAP_PRESET])

    def test_one_command_creates_ten_and_does_not_fetch_network(self):
        with patch('app.watchlists.fetch_quote') as http:
            response = self.run_command('프리셋 미국시총10')
            self.assertIn('10종목',response)
            self.assertIn('2026-11-04',response)
            stocks = load_group(self.db,self.room,self.sender,'미국시총10')
            self.assertEqual([s.ticker for s in stocks],[a for a,_ in US_MARKET_CAP_PRESET])
            self.assertEqual([s.name for s in stocks],[a for _,a in US_MARKET_CAP_PRESET])
            self.assertTrue(all(s.currency=='USD' for s in stocks))
            http.assert_not_called()
        self.assertIn('미국시총10 10종목',self.run_command('목록'))

    def test_existing_group_is_not_overwritten(self):
        self.run_command('그룹생성 반도체')
        self.run_command('추가 반도체 MU 마이크론')
        self.run_command('프리셋 미국시총10')
        with self.assertRaisesRegex(StockQuoteError,'이미 존재'):
            self.run_command('프리셋 미국시총10')
        self.assertEqual(len(load_group(self.db,self.room,self.sender,'미국시총10')),10)
        self.assertEqual(load_group(self.db,self.room,self.sender,'반도체')[0].ticker,'MU')
        with self.assertRaisesRegex(StockQuoteError, '최대 10개'):
            self.run_command('추가 미국시총10 WMT 월마트')
        with self.assertRaises(StockQuoteError):
            self.run_command('프리셋 무엇')
        with self.assertRaises(StockQuoteError):
            self.run_command('삭제 메모리7 MU')

    def test_scoped_and_group_report_ten(self):
        self.run_command('프리셋 미국시총10')
        with self.assertRaises(StockQuoteError):
            load_group(self.db,'다른방',self.sender,'미국시총10')
        with self.assertRaises(StockQuoteError):
            load_group(self.db,self.room,'다른사람','미국시총10')
        timestamp = datetime(2026,11,4,21,0,tzinfo=timezone.utc)
        with patch('app.watchlists.fetch_quote') as network:
            def fake(stock):
                return Quote(stock,100,99,(100/99-1)*100,timestamp,timestamp)
            report = group_report('미국시총10',load_group(self.db,self.room,self.sender,'미국시총10'),fetcher=fake)
            self.assertIn('엔비디아 $100.00',report)
            self.assertIn('일라이릴리 $100.00',report)
            self.assertEqual(report.count(' $100.00'),10)
            self.assertLess(report.index('엔비디아'),report.index('일라이릴리'))
            network.assert_not_called()


class MarketCapAPIIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.dbfile=Path(self.temp.name)/'integration.db'
        self.client=TestClient(create_app('Q'*64,self.dbfile))
        self.headers={'X-AngaeBot-Token':'Q'*64}
        self.index=0

    def tearDown(self):
        self.client.close()
        self.temp.cleanup()

    def cmd(self,arg,request_id=None,headers=True):
        self.index+=1
        return self.client.post('/v1/commands',headers=self.headers if headers else {},json={
            'request_id':request_id or f'marketcap_{self.index:012d}',
            'command':'주식','argument':arg,'room':'개인방','sender':'사용자'})

    def test_authorization_idempotency_and_persistent_history(self):
        self.assertEqual(self.cmd('프리셋 미국시총10',headers=False).status_code,401)
        original='marketcap_once_000001'
        r=self.cmd('프리셋 미국시총10',request_id=original)
        self.assertTrue(r.json()['ok'])
        repeated=self.cmd('프리셋 미국시총10',request_id=original)
        self.assertTrue(repeated.json()['duplicate'])
        self.assertEqual(self.cmd('목록',request_id=original).status_code,409)
        self.assertIn('10종목',self.cmd('목록').json()['reply'])
        with closing(sqlite3.connect(self.dbfile)) as db:
            self.assertEqual(db.execute('select count(*) from stock_items').fetchone()[0],10)
            self.assertEqual(db.execute('select count(*) from jobs').fetchone()[0],2)
            self.assertEqual(db.execute('select count(*) from events').fetchone()[0],2)
        legacy=self.client.post('/v1/commands',headers=self.headers,json={
            'request_id':'legacy_math_100000','command':'계산','argument':'344*454'})
        self.assertEqual(legacy.json()['ok'],True)
        self.assertIn('156,176',legacy.json()['reply'])


if __name__=='__main__':
    unittest.main()
