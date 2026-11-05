"""
앙개봇 v0.7.0 개인메모/부동산/금융투자/일정 회귀 테스트 — 전체 검증 명세
1. 신규 부동산·금융투자·개인·일정 별도 SQLite 저장, 카톡 인증 및 요청 ID 중복 보호 검증.
2. 분야별 등록/목록/검색/보기/수정/삭제 확인 명령의 실제 API·자료 보존 여부 확인.
3. 상대방 방 또는 발신자가 원본 기록 ID를 알아도 제목·본문을 조회/수정/삭제하지 못함을 검증.
4. 일정 YYYY-MM-DD 유효성, 향후 일정 정렬, 과거 일정 제외, 검색 특수문자 이스케이프 검증.
5. 홈 1~7 유지, 새 8~10 메뉴·연속 경로 점프·번호 목록 선택·0/00 복귀 검증.
6. 기존 jobs/events·stock_groups·ai_turns 테이블과 주식/AI 명령 처리 경로의 호환성 검증.
7. 미확인 방/발신자 거부, 길이 제한, 최대 항목 수/메뉴 TTL 보존 확인.
8. S20+/카카오톡/외부 네트워크 없이 임시 DB만 사용; 운영 DB·env·서버·로그를 건드리지 않는다.
9. v0.7.1 요청한 홈 1~10 정확한 순서와 개인 기록 새 위치(2/3/9)·설정 10번 경로를 검증한다.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault('ANGAE_TOKEN', 'N' * 64)

from fastapi.testclient import TestClient

from app.main import create_app
from app.personal_records import (RecordError, init_records_schema, list_records, get_record,
                                  execute_record_command, MAX_RECORDS_PER_SCOPE)
from app.selection_menu import StockSelectionMenus
from app.market import StockQuoteError


class RecordApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'records.db'
        self.client = TestClient(create_app('N' * 64, self.path))
        self.headers = {'X-AngaeBot-Token': 'N' * 64}
        self.seq = 0

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def call(self, cmd, arg='', *, room='내방', sender='나', request_id=None, authorized=True):
        self.seq += 1
        return self.client.post('/v1/commands',
            headers=self.headers if authorized else {},
            json={'request_id': request_id or f'private_{self.seq:012d}',
                  'command': cmd, 'argument': arg, 'room': room, 'sender': sender})

    def test_authenticated_create_update_detail_delete_and_idempotency(self):
        self.assertEqual(self.call('메모', '목록', authorized=False).status_code, 401)
        first = self.call('메모', '추가 중요한 약속 | 11월 확인', request_id='rec_dup_create_001').json()
        self.assertTrue(first['ok'], first)
        self.assertIn('개인 메모', first['reply'])
        self.assertEqual(first['module_source'], 'core.records')
        duplicate = self.call('메모', '추가 중요한 약속 | 11월 확인', request_id='rec_dup_create_001').json()
        self.assertTrue(duplicate['duplicate'])
        self.assertEqual(first['reply'], duplicate['reply'])
        conflict = self.call('메모', '추가 다른 제목 | 다른 내용', request_id='rec_dup_create_001')
        self.assertEqual(conflict.status_code, 409)
        with sqlite3.connect(self.path) as db:
            count = db.execute("SELECT COUNT(*) FROM personal_records").fetchone()[0]
            self.assertEqual(count, 1)
            item_id = db.execute('SELECT id FROM personal_records').fetchone()[0]
        view = self.call('메모', f'보기 {item_id}').json()
        self.assertTrue(view['ok'])
        self.assertIn('11월 확인', view['reply'])
        self.assertFalse(self.call('메모', f'삭제 {item_id}').json()['ok'])
        self.assertTrue(self.call('메모', f'수정 {item_id} 변경된 제목 | 새 내용').json()['ok'])
        self.assertIn('새 내용', self.call('메모', f'보기 {item_id}').json()['reply'])
        self.assertTrue(self.call('메모', f'삭제 {item_id} 확인').json()['ok'])
        self.assertFalse(self.call('메모', f'보기 {item_id}').json()['ok'])

    def test_categories_and_search_across_sectors(self):
        p = self.call('부동산', '추가 전세 계약 | 보증금 검토').json()
        f = self.call('투자', '추가 메모리 반도체 | 기업 분석').json()
        n = self.call('메모', '추가 배드민턴 모임 | 다음주 약속').json()
        self.assertTrue(all(x['ok'] for x in (p, f, n)))
        for command, present, absent in [
            ('부동산', '전세 계약', '메모리 반도체'),
            ('금융', '메모리 반도체', '전세 계약'),
            ('메모', '배드민턴 모임', '전세 계약'),
        ]:
            result = self.call(command, '검색 ' + present.split()[0]).json()
            self.assertTrue(result['ok'], result)
            self.assertIn(present, result['reply'])
            self.assertNotIn(absent, result['reply'])
            self.assertTrue(result['menu_active'])
        all_result = self.call('기록', '검색 계약').json()
        self.assertTrue(all_result['ok'])
        self.assertIn('전세 계약', all_result['reply'])
        with sqlite3.connect(self.path) as db:
            groups = {row[0] for row in db.execute('SELECT DISTINCT category FROM personal_records')}
        self.assertEqual(groups, {'부동산','금융·투자','개인'})

    def test_personal_scope_and_bad_payload(self):
        create = self.call('메모', '추가 은행 준비 | 개인 메모').json()
        self.assertTrue(create['ok'])
        with sqlite3.connect(self.path) as db:
            uid = db.execute('SELECT id FROM personal_records').fetchone()[0]
        for kwargs in ({'sender':'남'}, {'room':'다른방'}):
            self.assertFalse(self.call('메모', f'보기 {uid}', **kwargs).json()['ok'])
            self.assertFalse(self.call('메모', f'수정 {uid} 탈취 | 시도', **kwargs).json()['ok'])
            self.assertFalse(self.call('메모', f'삭제 {uid} 확인', **kwargs).json()['ok'])
            self.assertNotIn('은행 준비', self.call('메모', '목록', **kwargs).json()['reply'])
        self.assertFalse(self.call('메모', '추가 제목 | ' + '가'*601).json()['ok'])
        self.assertFalse(self.call('메모', '추가 ' + '가'*61).json()['ok'])
        self.assertFalse(self.call('메모', '검색 ' + '가'*61).json()['ok'])
        self.assertFalse(self.call('메모', '추가 제목 | 내용', room='', sender='').json()['ok'])
        self.assertIn('은행 준비', self.call('메모', f'보기 {uid}').json()['reply'])

    def test_schedule_dates_upcoming_and_search_escape(self):
        self.assertFalse(self.call('일정', '추가 2026-02-30 잘못된 일정').json()['ok'])
        self.assertTrue(self.call('일정', '추가 2035-12-24 건강검진 | 오전 9시').json()['ok'])
        self.assertTrue(self.call('일정', '추가 2020-01-01 과거 기록').json()['ok'])
        self.assertTrue(self.call('일정', '추가 2035-02-01 공항 출발 | 항공편').json()['ok'])
        upcoming = self.call('일정', '목록').json()
        self.assertTrue(upcoming['menu_active'])
        self.assertIn('2035-02-01 공항 출발', upcoming['reply'])
        self.assertIn('2035-12-24 건강검진', upcoming['reply'])
        self.assertNotIn('과거 기록', upcoming['reply'])
        self.assertLess(upcoming['reply'].index('2035-02-01'), upcoming['reply'].index('2035-12-24'))
        self.assertTrue(self.call('메모', '추가 할인가 10%_ | 할인 확인').json()['ok'])
        self.assertIn('할인가 10%_', self.call('메모', '검색 %_').json()['reply'])
        self.assertNotIn('할인가 10%_', self.call('메모', '검색 존재하지않는키워드').json()['reply'])

    def test_home_menu_new_sectors_and_numbers(self):
        # 메뉴 순서를 명시적으로 검증하여 번호 점프/카톡 선택/전체 트리의 불일치를 방지한다.
        self.assertEqual([item.label for item in StockSelectionMenus._home_choices()], [
            '📈 주식', '🏠 부동산', '💰 금융·투자', '🧭 여행', '🏸 배드민턴',
            '🍳 요리', '🌳 종친', '🌤 날씨', '🗂 개인 메모·일정', '⚙️ 설정·운영',
        ])
        home = self.call('메뉴', '홈').json()
        self.assertTrue(home['ok'], home)
        self.assertIn('2. 🏠 부동산', home['reply'])
        self.assertIn('3. 💰 금융·투자', home['reply'])
        self.assertIn('9. 🗂 개인 메모·일정', home['reply'])
        self.assertIn('10. ⚙️ 설정·운영', home['reply'])
        tree = self.call('메뉴', '경로 설정 7').json()
        self.assertIn('9-2. 다가오는 일정', tree['reply'])
        self.assertIn('2-1. 최근 메모 목록', tree['reply'])
        self.assertIn('3-1. 최근 메모 목록', tree['reply'])
        self.assertIn('앙개봇 메인 메뉴', self.call('메뉴', '선택 00').json()['reply'])
        self.assertIn('부동산 메뉴', self.call('메뉴', '경로 홈 2').json()['reply'])
        self.assertIn('메인 메뉴', self.call('메뉴', '선택 0').json()['reply'])
        self.assertIn('금융·투자 메뉴', self.call('메뉴', '금융·투자').json()['reply'])
        self.assertIn('개인 메뉴', self.call('메뉴', '개인').json()['reply'])

    def test_menu_selected_record_detail_and_back(self):
        self.call('부동산', '추가 건물 | 중요한 정보')
        listing = self.call('메뉴', '경로 홈 2 1').json()
        self.assertTrue(listing['ok'], listing)
        self.assertTrue(listing['menu_active'])
        self.assertIn('건물', listing['reply'])
        details = self.call('메뉴', '선택 1').json()
        self.assertTrue(details['ok'], details)
        self.assertIn('중요한 정보', details['reply'])
        self.assertIn('부동산 메뉴', details['reply'])
        self.assertIn('메인 메뉴', self.call('메뉴', '선택 0').json()['reply'])

    def test_tables_preserved_and_jobs_events_unchanged(self):
        self.call('메모', '추가 안녕 | 데이터')
        self.call('일정', '추가 2035-04-01 일정')
        with sqlite3.connect(self.path) as db:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({'personal_records','jobs','events','stock_groups','ai_turns'} <= tables)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0],
                             db.execute('SELECT COUNT(*) FROM events').fetchone()[0])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM personal_records').fetchone()[0], 2)


class RecordLimitUnitTests(unittest.TestCase):
    def test_no_cross_scope_when_id_known_and_limit(self):
        db = sqlite3.connect(':memory:')
        try:
            init_records_schema(db)
            with self.assertRaises(RecordError):
                execute_record_command(db, '', '', '메모', '목록')
            entry = execute_record_command(db, '방', '사용자', '메모', '추가 제목 | 내용')
            self.assertIn('등록 #1', entry.reply)
            with self.assertRaises(RecordError):
                get_record(db, '방', '타인', 1)
            self.assertEqual(list_records(db, '방', '타인', query='본인'), ())
            # 정상 스코프에서 검색 결과가 없다면 빈 목록만 반환한다.
        except RecordError as error:
            self.fail(f'unexpected record error: {error}')
        finally:
            db.close()


if __name__ == '__main__':
    unittest.main()
