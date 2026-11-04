"""앙개봇 v0.3.0 AI 모듈 회귀/보안 테스트 — AI 기본 OFF, 검증, HTTP 매핑, 문맥, 비밀키 보호."""
import io
import json
import os
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request

os.environ.setdefault("ANGAE_TOKEN", "T" * 64)
from app.ai_engine import AIError, AISettings, get_ai_reply


def settings(**overrides):
    data = dict(enabled=True, provider="openai", base_url="https://api.openai.com/v1",
                model="gpt-6-luna", api_key="sk-unit-test-not-a-real-key", timeout=12,
                memory_enabled=True, context_turns=6)
    data.update(overrides)
    return AISettings(**data)


class Response:
    def __init__(self, obj):
        self.value = json.dumps(obj, ensure_ascii=False).encode()
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n): return self.value[:n]


class AITests(unittest.TestCase):
    def test_off_never_calls_network(self):
        called = []
        with self.assertRaisesRegex(AIError, 'OFF'):
            get_ai_reply(settings(enabled=False), '안녕', sender=lambda *a, **k: called.append(1))
        self.assertEqual(called, [])

    def test_cloud_endpoint_https(self):
        self.assertEqual(settings().endpoint(), 'https://api.openai.com/v1/chat/completions')

    def test_local_ollama_http(self):
        self.assertEqual(settings(provider='ollama', base_url='http://10.1.1.100:11434/v1', api_key='').endpoint(),
                         'http://10.1.1.100:11434/v1/chat/completions')

    def test_reject_public_http(self):
        with self.assertRaises(AIError):
            settings(provider='ollama', base_url='http://example.com:11434/v1', api_key='').endpoint()

    def test_openai_requires_key(self):
        with self.assertRaises(AIError):
            settings(api_key='').endpoint()

    def test_provider_rejects_unexpected(self):
        with self.assertRaises(AIError):
            settings(provider='random').endpoint()

    def test_network_request_and_context(self):
        captured = []
        def send(request, timeout):
            self.assertIsInstance(request, Request)
            data = json.loads(request.data)
            captured.append((request.full_url, timeout, request.get_header('Authorization'), data))
            return Response({'choices': [{'message': {'content': '좋습니다.'}}]})
        reply = get_ai_reply(settings(), '계속 알려줘', history=[('앞 질문', '앞 답변')], sender=send)
        self.assertEqual(reply, '좋습니다.')
        url, timeout, authorization, payload = captured[0]
        self.assertEqual(url, 'https://api.openai.com/v1/chat/completions')
        self.assertEqual(timeout, 12)
        self.assertTrue(authorization.startswith('Bearer '))
        self.assertEqual([x['role'] for x in payload['messages']], ['system','user','assistant','user'])
        self.assertEqual(payload['messages'][1]['content'], '앞 질문')
        self.assertEqual(payload['messages'][-1]['content'], '계속 알려줘')
        self.assertEqual(payload['max_completion_tokens'], 650)
        self.assertEqual(payload['reasoning_effort'], 'none')

    def test_ollama_without_bearer_key(self):
        def send(req, timeout):
            self.assertIsNone(req.get_header('Authorization'))
            return Response({'choices': [{'message': {'content': 'Ollama OK'}}]})
        result = get_ai_reply(settings(provider='ollama', base_url='http://127.0.0.1:11434/v1',api_key=''), '안녕', sender=send)
        self.assertEqual(result, 'Ollama OK')

    def test_summary_does_not_replay_history(self):
        def send(req, timeout):
            payload=json.loads(req.data)
            self.assertEqual(len(payload['messages']), 2)
            self.assertIn('요약',payload['messages'][-1]['content'])
            return Response({'choices': [{'message': {'content': '요약 완료'}}]})
        self.assertEqual(get_ai_reply(settings(), '가나다', summarize=True,history=[('비밀','답변')], sender=send), '요약 완료')

    def test_http_429_safe_error(self):
        def send(req, timeout):
            raise HTTPError(req.full_url, 429, 'secret token', None, None)
        with self.assertRaisesRegex(AIError, '요청 한도') as err:
            get_ai_reply(settings(), '안녕', sender=send)
        self.assertNotIn('secret token', str(err.exception))

    def test_bad_result_safe_error(self):
        with self.assertRaisesRegex(AIError, '응답 형식'):
            get_ai_reply(settings(), '안녕', sender=lambda req, timeout: Response({'x': 'bad'}))

    def test_input_limit(self):
        with self.assertRaisesRegex(AIError, '1000'):
            get_ai_reply(settings(), 'x' * 1001, sender=lambda *a, **k: None)

    def test_context_limit(self):
        with self.assertRaisesRegex(AIError, '0~10'):
            settings(context_turns=11).endpoint()

if __name__ == '__main__': unittest.main()
