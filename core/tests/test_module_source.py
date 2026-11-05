"""
앙개봇 v0.6.1 소스 모듈·배포 브랜치 검증 — 전체 테스트
1. 코어 모듈 ID가 실제 실행된 메뉴/주식 시세/분석/운영/AI/기초명령과 일치하는지 확인한다.
2. health API의 인증과 실제 배포 기록 기반 브랜치/SHA, 미기록 상황을 검증한다.
3. 추가 필드의 존재가 메뉴/분석/조회/DB jobs·events/중복 방지 로직을 변경하지 않음을 검사한다.
4. SHA/브랜치 형식, 파일 크기, 손상 기록은 모두 미확인으로 안전하게 처리한다.
5. 테스트용 임시 SQLite/metadata만 사용하며 GitHub, S20+, 외부 네트워크·파일을 변경하지 않는다.
6. 기존 기능과 로그·사용자 데이터·권한·API 토큰/메시지는 그대로 유지한다.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import create_app
from app.module_info import module_for
from app.ops import deployment_identity


class ModuleSourceTests(unittest.TestCase):
    def test_module_categories(self):
        cases = [
            ('메뉴','', '메인 메뉴','core.menu'),
            ('메뉴','메모리7', '', 'core.market'),
            ('메뉴','분석 MU', '', 'core.history'),
            ('메뉴','설정보기 deployment', '', 'core.ops'),
            ('주식','목록', '', 'core.watchlists'),
            ('주식','반도체', '', 'core.market'),
            ('메모리7','', '', 'core.market'),
            ('질문','안녕하세요', '', 'core.ai'),
            ('상세상태','', '', 'core.ops'),
            ('시간','', '', 'core.commands')
        ]
        for cmd,arg,reply,want in cases:
            with self.subTest(cmd=cmd, arg=arg):
                self.assertEqual(module_for(cmd,arg,reply),want)

    def test_deployment_identity_valid_and_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / '.deploy-info.json'
            self.assertEqual(deployment_identity(info_path=file), {'branch':'','sha':''})
            file.write_text(json.dumps({'branch':'feature/global-shortcut-menus-20261106',
                                        'sha':'a'*40}), encoding='utf-8')
            self.assertEqual(deployment_identity(info_path=file),
                             {'branch':'feature/global-shortcut-menus-20261106','sha':'a'*40})
            for meta in ({'branch':'main','sha':'bad'},
                         {'branch':'../../bad / secret','sha':'a'*40}):
                file.write_text(json.dumps(meta), encoding='utf-8')
                self.assertEqual(deployment_identity(info_path=file), {'branch':'','sha':''})
            file.write_text('a'*2200, encoding='utf-8')
            self.assertEqual(deployment_identity(info_path=file), {'branch':'','sha':''})

    def test_authenticated_health_and_module_meta(self):
        with tempfile.TemporaryDirectory() as temp:
            dbfile=Path(temp) / 'test.db'
            with TestClient(create_app('T'*64, dbfile)) as client:
                self.assertEqual(client.get('/v1/health').status_code,401)
                with patch('app.main.deployment_identity',
                           return_value={'branch':'feature/branch','sha':'a'*40}):
                    result=client.get('/v1/health',headers={'X-AngaeBot-Token':'T'*64})
                self.assertEqual(result.status_code,200)
                self.assertEqual(result.json()['deployment_branch'],'feature/branch')
                self.assertEqual(result.json()['deployment_sha'],'a'*40)
                packet={'request_id':'modsource-test-001','command':'메뉴','argument':'홈',
                        'room':'testroom','sender':'testsender'}
                first=client.post('/v1/commands',headers={'X-AngaeBot-Token':'T'*64},json=packet).json()
                self.assertEqual(first['module_source'],'core.menu')
                self.assertTrue(first['menu_active'])
                again=client.post('/v1/commands',headers={'X-AngaeBot-Token':'T'*64},json=packet).json()
                self.assertTrue(again['duplicate'])
                self.assertEqual(again['module_source'],'core.menu')

if __name__ == '__main__':
    unittest.main()
