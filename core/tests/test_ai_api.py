"""앙개봇 v0.3.0 AI API 회귀 테스트 — 기존 API 유지/문맥/중복요청/초기화/실패 격리/토큰 인증.
1. v0.5.4 SQLite 테스트 조회는 contextlib.closing을 사용해 트랜잭션뿐 아니라 연결도 명시적으로 닫으며 ResourceWarning을 방지한다.
"""
from contextlib import closing
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('ANGAE_TOKEN', 'T' * 64)
from fastapi.testclient import TestClient
from app.main import create_app
from app.ai_engine import AIError, AISettings


def config(enabled=True, memory=True):
    return AISettings(enabled=enabled, provider='openai', base_url='https://api.openai.com/v1',
                      model='gpt-6-luna', api_key='test',timeout=12,
                      memory_enabled=memory,context_turns=6)

class AIApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'test.db'
        self.client=TestClient(create_app('Q'*64, self.path))
        self.headers={'X-AngaeBot-Token':'Q'*64}
        self.index=0

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def cmd(self,name,arg='',room='A',sender='B',request_id=None):
        self.index+=1
        return self.client.post('/v1/commands', headers=self.headers,
               json={'request_id':request_id or f'request_{self.index:08d}',
                     'command':name, 'argument':arg,'room':room,'sender':sender})

    def test_auth_all_commands(self):
        self.assertEqual(self.client.post('/v1/commands',json={'request_id':'abcdefgh','command':'AI상태'}).status_code,401)

    def test_ai_off_and_existing_math_stays_working(self):
        with patch('app.main.AISettings.from_env',return_value=config(enabled=False)):
            r=self.cmd('질문','안녕하세요').json()
            self.assertFalse(r['ok'])
            self.assertIn('OFF',r['reply'])
            self.assertIn('56,088',self.cmd('계산','123*456').json()['reply'])
            self.assertTrue(self.cmd('시간').json()['ok'])

    def test_status_no_external_request(self):
        with patch('app.main.AISettings.from_env',return_value=config(enabled=False)):
            self.assertIn('OFF',self.cmd('AI상태').json()['reply'])

    def test_memory_scoped_reset_and_duplicate(self):
        inputs=[]
        def fake_ai(settings, question, *, history, summarize):
            inputs.append((question, list(history)))
            return '답변'+str(len(inputs))
        with patch('app.main.AISettings.from_env',return_value=config()), patch('app.main.get_ai_reply',side_effect=fake_ai):
            one=self.cmd('질문','첫 질문',request_id='request_unique_0001').json()
            self.assertTrue(one['ok']); self.assertEqual(one['reply'],'답변1')
            same=self.cmd('질문','첫 질문',request_id='request_unique_0001').json()
            self.assertTrue(same['duplicate'])
            self.assertEqual(len(inputs),1)
            self.cmd('질문','다음 질문')
            self.assertEqual(inputs[-1][1],[('첫 질문','답변1')])
            self.cmd('질문','다른 사람',sender='C')
            self.assertEqual(inputs[-1][1],[])
            self.assertTrue(self.cmd('대화초기화').json()['ok'])
            self.cmd('질문','초기화 다음')
            self.assertEqual(inputs[-1][1],[])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('select count(*) from ai_turns').fetchone()[0],4)
            self.assertGreaterEqual(db.execute('select count(*) from jobs').fetchone()[0],5)
            self.assertGreaterEqual(db.execute('select count(*) from events').fetchone()[0],5)

    def test_legacy_command_survives_ai_failure(self):
        with patch('app.main.AISettings.from_env',return_value=config()), patch('app.main.get_ai_reply',side_effect=AIError('AI 연결 실패')):
            self.assertFalse(self.cmd('질문','테스트').json()['ok'])
            self.assertIn('56,088',self.cmd('계산','123*456').json()['reply'])

    def test_disabled_memory_does_not_store_turns(self):
        with patch('app.main.AISettings.from_env',return_value=config(memory=False)),patch('app.main.get_ai_reply',return_value='응답'):
            self.cmd('질문','안녕')
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('select count(*) from ai_turns').fetchone()[0],0)

    def test_old_tables_remain(self):
        with closing(sqlite3.connect(self.path)) as db:
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({'jobs','events','ai_turns','ai_sessions'} <= tables)

if __name__ == '__main__': unittest.main()
