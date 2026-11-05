"""
앙개봇 v0.6.1 응답 모듈 정보 — 전체 기능과 안정성 보증
1. 모든 Python Core의 정상/오류 응답에 현재 실행 기능을 담당하는 소스 모듈 ID를 부여한다.
2. 메뉴 이동은 selection_menu.py, 운영 조회는 ops.py, 주식 시세는 market.py로 구별한다.
3. 종목 분석은 history.py, 주식 그룹 관리/조회는 watchlists.py로 구별한다.
4. AI 질문/요약/상태는 ai_engine.py, 계산/시간/서버상태는 commands.py로 구별한다.
5. 요청된 사용자 인수와 조회 결과를 일치시켜 앙패스의 마지막 단계 실제 모듈을 반환한다.
6. 임의 파일 경로·민감한 로그/메시지를 넘기지 않고 허용된 짧은 ID만 반환한다.
7. 기존 응답 내용, SQLite 스키마/로그, 가격 조회, AI, 배터리, 메뉴 기능은 변경하지 않는다.
8. 중복된 요청의 표시 역시 순수 함수로 처리하며 추가 API/DB 요청이나 부작용은 없다.
"""
from __future__ import annotations


def module_for(command: str, argument: str = '', reply: str = '') -> str:
    """Return the single existing module responsible for the resulting answer."""
    arg = argument.strip()
    if command in {'상세상태', '통계', '최근오류', '가동시간'}:
        return 'core.ops'
    if command in {'질문', '요약', 'AI상태', '대화초기화'}:
        return 'core.ai'
    if command in {'계산', '시간', '서버상태'}:
        return 'core.commands'
    if command == '메모리7':
        return 'core.market'
    if command in {'메뉴', '주식'}:
        if arg.startswith('설정보기 '):
            return 'core.ops'
        if arg.startswith('분석 '):
            return 'core.history'
        if arg == '메모리7':
            return 'core.market'
        if arg == '목록' or arg.startswith((
            '추가 ', '삭제 ', '그룹생성 ', '그룹삭제 ', '그룹조회 ', '프리셋 '
        )):
            return 'core.watchlists'
        if arg in {'반도체', '미국시총10'}:
            return 'core.market' if command == '주식' else 'core.watchlists'
        if not arg or arg == '메뉴':
            return 'core.menu'
        if '메뉴' in reply or '개발 예정' in reply:
            return 'core.menu'
        if reply.startswith('💾') or reply.startswith('📊'):
            return 'core.market'
        if '분석' in reply:
            return 'core.history'
        return 'core.watchlists' if command == '주식' else 'core.menu'
    return 'core.main'
