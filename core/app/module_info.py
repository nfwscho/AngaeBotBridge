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
9. '설정보기 tree' 응답은 읽기 전용 트리를 실제로 생성하는 core.menu로 표시하고 나머지 설정 조회는 core.ops를 유지한다.
10. 설정 8번 도움말은 실제 생성 모듈 core.menu, 통합 상태는 core.ops로 구별하고 나머지 응답 모듈도 보존한다.
11. v0.7.0 개인 기록 CRUD·일정·검색·상세보기는 core.personal_records로 식별하고 기존 메뉴·주식·AI 표시를 보존한다.
12. 날씨 조회/지역 설정 결과는 core.weather, 메뉴 진입은 core.menu로 구분하며 중복 API 응답에도 같은 모듈을 표시한다.
13. 부동산 매매·전월세 공식 실거래 조회 및 지역 설정은 core.real_estate로 식별하고 개인메모는 core.records를 보존한다.
14. 메모리7의 시세표 99 상세/간략 응답은 호출 인수가 번호선택이어도 원본 시세 모듈(core.market)로 식별한다.
15. 기존 메뉴/분석/관심종목/부동산/날씨 등 모듈 분류와 하단 로그/배터리 표기를 변경하지 않는다.
16. 공통 99번 선택의 사용자 관심그룹 상세 응답은 실제 renderer watchlists.py로 표기하고 기존 메모리7/core.market 표시를 유지한다.
17. 메모리7 7번 메뉴 제거는 소스 식별기를 변경하지 않으며 다른 종목 분석·설정·날씨 모듈 귀속은 보존한다.
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
    if command == '실거래' or (
        command == '부동산' and arg.split(' ', 1)[0] in
        {'시세', '매매', '전세', '월세', '지역', '실거래'}
    ):
        return 'core.real_estate'
    if command in {'메모', '일정', '부동산', '투자', '금융', '기록'}:
        return 'core.records'
    if command == '메모리7':
        return 'core.market'
    if command == '날씨':
        return 'core.menu' if '날씨 메뉴' in reply else 'core.weather'
    if command in {'메뉴', '주식'}:
        if arg.startswith('실거래조회 ') or arg == '실거래설정 안내':
            return 'core.real_estate'
        if arg.startswith(('날씨조회 ', '날씨설정 ')) or reply.startswith(
            ('🌤 서울 ', '🌦 서울 ', '🌤 부산 ', '🌦 부산 ', '🗓 ', '📍 날씨 지역 설정')
        ):
            return 'core.weather'
        # 다른 설정 지역의 조회 결과도 선택 인수에 의존하지 않고 정확히 분류한다.
        if reply.startswith(('🌤 ', '🌦 ')) and '날씨 · ' in reply.split('\n', 1)[0]:
            return 'core.weather'
        # 전체 메뉴 트리의 실제 생성 모듈을 표시한다. 기존 운영 조회는 ops 그대로 유지한다.
        if arg in {'설정보기 tree', '설정보기 help'}:
            return 'core.menu'
        if arg.startswith('설정보기 '):
            return 'core.ops'
        if arg.startswith('분석 '):
            return 'core.history'
        if arg in {'메모리7', '메모리7 상세', '상세'}:
            return 'core.market'
        if arg.startswith('상세시세 ') or (
                reply.startswith('🔎 ') and '관심종목 시세 상세 보기' in reply.split('\n', 1)[0]):
            return 'core.watchlists'
        if arg == '목록' or arg.startswith((
            '추가 ', '삭제 ', '그룹생성 ', '그룹삭제 ', '그룹조회 ', '프리셋 '
        )):
            return 'core.watchlists'
        if arg in {'반도체', '미국시총10'}:
            return 'core.market' if command == '주식' else 'core.watchlists'
        # 메뉴 선택은 명령 인수가 비어 있어도 기록 결과 본문이 오면 실제 모듈로 구분한다.
        if reply.startswith(('🗂 ', '📒 메모 #', '📅 일정 #', '📭 저장된 기록')):
            return 'core.records'
        if not arg or arg == '메뉴':
            return 'core.menu'
        if '메뉴' in reply or '개발 예정' in reply:
            return 'core.menu'
        if reply.startswith(('💾', '📊', '🔎 메모리7 시세 상세 보기')):
            return 'core.market'
        if '분석' in reply:
            return 'core.history'
        return 'core.watchlists' if command == '주식' else 'core.menu'
    return 'core.main'
