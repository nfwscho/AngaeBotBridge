"""앙개봇 Python v0.2.0: 인증/아이템포턴시/명령 API의 회귀 테스트."""
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault('ANGAE_TOKEN', 'T' * 64)
from fastapi.testclient import TestClient
from app.main import create_app

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.token = 'Q' * 64
        self.client = TestClient(create_app(self.token, Path(self.tmp.name) / 'jobs.db'))
        self.headers = {'X-AngaeBot-Token': self.token}

    def tearDown(self):
        self.client.close()
        self.tmp.cleanup()

    def test_health_auth(self):
        self.assertEqual(self.client.get('/v1/health').status_code, 401)
        self.assertEqual(self.client.get('/v1/health', headers=self.headers).status_code, 200)

    def test_command_auth(self):
        x = {'request_id': 'abcd000000001', 'command': '계산', 'argument': '123*456'}
        self.assertEqual(self.client.post('/v1/commands', json=x).status_code, 401)
        first = self.client.post('/v1/commands', json=x, headers=self.headers)
        self.assertEqual(first.status_code, 200)
        self.assertIn('56,088', first.json()['reply'])
        self.assertFalse(first.json()['duplicate'])
        again = self.client.post('/v1/commands', json=x, headers=self.headers)
        self.assertTrue(again.json()['duplicate'])

    def test_request_id_collision(self):
        x = {'request_id': 'abcd000000002', 'command': '시간'}
        self.assertEqual(self.client.post('/v1/commands', json=x, headers=self.headers).status_code, 200)
        x['command'] = '계산'
        self.assertEqual(self.client.post('/v1/commands', json=x, headers=self.headers).status_code, 409)

    def test_no_arbitrary_execution(self):
        x = {'request_id': 'abcd000000003', 'command': 'shell', 'argument': 'rm -rf /'}
        self.assertEqual(self.client.post('/v1/commands', json=x, headers=self.headers).status_code, 400)

    def test_invalid_calculation(self):
        x = {'request_id': 'abcd000000004', 'command': '계산', 'argument': '1/0'}
        response = self.client.post('/v1/commands', json=x, headers=self.headers)
        self.assertFalse(response.json()['ok'])
        self.assertIn('0으로', response.json()['reply'])

if __name__ == '__main__': unittest.main()
