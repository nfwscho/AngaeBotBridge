"""
앙개봇 Python Core v0.5.5 선택형 주식 메뉴 — 전체 기능과 안전 제약
1. '주식 메뉴'(Android 단축 '주')로 1~6번 간단한 메뉴를 생성한다.
2. 메뉴가 열린 뒤 문자 '1' 또는 '1번'을 보내면 현재 메뉴의 해당 번호를 선택한다.
3. 1번은 사용자가 실제 실행했던 성공한 주식 읽기 명령을 최신순/중복 제거하여 최대 8개 보여준다.
4. 과거 로그 검색은 같은 카카오톡 방/발신자 범위에서만 수행하고 다른 사람의 데이터는 노출하지 않는다.
5. 주식 추가/삭제, 그룹삭제, 프리셋 등록, AI/원격 실행 등 부작용 명령은 재실행 목록에서 제외한다.
6. 6번은 삼성전자/하이닉스/마이크론/엔비디아/애플/샌디스크/메모리7 분석 메뉴를 연다.
7. 번호 선택 후 원래 주식 명령으로 안전하게 변환되며 기존 FastAPI 인증·jobs/events 기록을 재사용한다.
8. 새로운 SQLite 테이블/데이터 변경 없이 기존 jobs/stock_groups 읽기 전용 조회만 수행한다.
9. 현재 메뉴는 5분 후 만료되며, 별도의 시스템/발신자/채팅방과 섞이지 않게 사용자별로 분리한다.
10. 서버 재시작 또는 프로세스 종료 시 메뉴는 소멸하며 로그나 영구 사용자 정보를 삭제하지 않는다.
11. 메모리에 보관하는 것은 허용된 짧은 주식 명령 문자열뿐이며 최대 200개 대화 스코프로 제한한다.
12. 기존 주식 메모리7/그룹/미국시총10/5일·1/3개월 변동성·AI OFF/Android 권한/로그를 보존한다.
13. 가격 알림/자동매매/예약발신/미인가 사용자의 숫자 명령 실행을 추가하지 않는다.
14. 단위 테스트 시 단조 시계를 주입하여 목록 만료/범위 격리/잘못된 번호를 외부 인터넷 없이 검사한다.
15. v0.5.6은 정상 시세 조회 후 메모리7 8종목 또는 사용자 그룹 최대 10종목의 번호를 분석 명령으로 연결한다.
16. 목록에 표시된 원래 순서/종목코드를 메모리에만 저장하여 동일 이름·별칭 또는 공급자 실패가 있어도 정확한 종목을 선택한다.
17. '10'을 지원하지만 '10개'·'123'과 메뉴가 없는 숫자는 무시하며 5분 만료·방/발신자 격리와 잠금을 유지한다.
18. 기존 메인 메뉴/최근 사용 명령/분석 하위 메뉴/SQLite 원본 기록·AI OFF·배터리 표시는 그대로 보존한다.
19. 관심그룹 목록의 1번 메모리7 및 사용자 그룹을 실제 DB 정렬 순서대로 숫자 선택에 연결한다.
20. 선택 세션은 기존 5분·방/발신자 격리·한 번 선택 후 종료를 재사용하고 DB를 변경하지 않는다.
21. 숫자 0은 현재 선택 화면에서 이전 메뉴(그룹 목록 또는 주식 메인 메뉴)로 돌아간다.
22. 뒤로가기는 기존 인증·5분 만료·방/발신자 격리를 따르며 DB와 기존 로그를 변경하지 않는다.
23. 그룹 시세 선택의 진입 화면을 기억해 주식 메인 메뉴와 관심그룹 목록으로 정확히 복귀한다.
24. 통합 홈 메뉴와 배드민턴·요리·여행·종친·영어 콘텐츠 메뉴를 추가하되 기존 주식 메뉴/로그는 그대로 보존한다.
25. 홈에서 번호로 콘텐츠로 이동하고 0으로 상위 화면 복귀, 00으로 홈 이동을 지원한다.
26. 아직 구현되지 않은 콘텐츠 항목은 실제 기능이 있는 것처럼 실행하지 않고 '개발 예정'으로 안내한다.
27. 모든 메뉴는 기존 5분 TTL/방·발신자 격리/200세션 제한/인증된 요청/기존 SQLite 불변을 재사용한다.
28. 홈 6번 영어 대신 날씨, 7번 읽기 전용 설정·운영 관리 메뉴를 추가한다.
29. 설정에서 상태/배포 이력/로그 요약/환경 설정 상태/통계를 조회하되 비밀키와 타인 로그를 보이지 않는다.
30. 메뉴 점프는 정확한 숫자 경로를 실제 메뉴 선택으로 순회해 중간 시세 조회 없이 최종 명령만 실행한다.
31. 그룹·종목·최근조회 메뉴의 동적 선택은 소유 채팅방/발신자 범위만 읽으며 CRUD·AI·임의 명령을 허용하지 않는다.
32. 기존 주식 메뉴 및 0/00/5분 세션·단축어·기능·로그·DB 스키마는 모두 유지한다.
49. 주식 메뉴 1~6번 위치·동작은 그대로 보존하고 7번 '메모리7 시세 상세 보기'를 읽기 전용 명령으로 추가한다.
50. 2번 간략 목록은 프리/애프터 대표값만 한 행에 보여주며 7번은 정규/장외 가격·등락기준·출처·시각을 각각 표시한다.
51. 두 시세 화면 모두 1~8 번호 분석/0 이전/00 홈/5분 만료/방·발신자 격리 및 기존 로그를 그대로 재사용한다.
52. 메모리7 간략 결과 화면의 9번은 상세보기, 상세 결과 화면의 9번은 간략보기로 전환한다.
53. 메모리7 원래 1~8 종목 분석 선택은 유지하고 9번 전환은 메모리7 전용 세션에만 삽입하여 그룹 1~10 번호와 충돌하지 않는다.
54. 주식 메인 메뉴 기존 1~7번·0/00·방/발신자·5분 제한과 단축명령·도움말을 그대로 보존한다.
55. 설정 도움말에 메모리7 시세표의 9번 상세/간략 전환과 기존 주식 메인 메뉴 7번 직접 상세 보기를 안내한다.
56. 설정 도움말은 원래 8줄 이내를 유지하며 새 9번 전환 안내를 기존 주식 명령 안내와 같은 한 줄에 통합한다.
33. 설정 7번에 전체 메뉴 트리 조회를 추가하며 기존 설정 1~6번의 번호·동작을 보존한다.
34. 트리는 홈·주식·설정·콘텐츠·종목분석의 실제 선택지 정의를 재사용해 번호 경로를 구성한다.
35. 사용자별 관심그룹/최근 명령/선택 시세의 구체적 내용은 노출하지 않고 동적 목록이라고 표시한다.
36. 전체 트리 조회는 DB/시세/외부 API를 읽거나 수정하지 않으며 기존 세션·인증·로그 경로를 따른다.
37. 설정 1번 통합 상태와 8번 간결 도움말을 추가하고 기존 1~7 번호/기능을 보존한다.
38. 도움말은 설정의 인증·번호 점프·5분 세션을 재사용하며 기존 주식/AI/로그·DB는 유지한다.
39. 홈 8 부동산, 9 금융·투자, 10 개인 메모·일정으로 확장하며 기존 홈 1~7 번호를 유지한다.
40. 분야별 최신 메모·다가오는 일정을 목록에서 번호로 상세 조회하고 0/00·5분 스코프·로그를 보존한다.
41. 개인 기록의 제목/본문은 SQLite 개인 기록 모듈에서만 다루며 메뉴 세션에는 번호/제목만 임시 저장한다.
42. v0.7.1 홈 1~10 순서는 주식/부동산/금융·투자/여행/배드민턴/요리/종친/날씨/개인/설정으로 구성한다.
43. 전체 메뉴 트리·설정 8 도움말·연속 번호 경로는 같은 홈 정의를 사용하므로 순서가 항상 일치한다.
44. 기존 부/투/메 단축어를 유지하면서 금(투자)·개(개인)를 추가하고 로그/인증·5분 선택 세션을 유지한다.
45. 날씨 메뉴 1~3은 실제 Open-Meteo 예보 조회로 연결하고 4번은 방/발신자별 지역 설정 안내로 연결한다.
46. 미개발 다른 콘텐츠와 홈/주식/설정/메모 메뉴 및 0/00/5분 보호·로그 경로를 변경하지 않는다.
47. 부동산 메모 1~2번을 유지하고 3 매매·4 전세·5 월세 실거래가 조회, 6 지역 안내를 추가한다.
48. 실거래 API 호출은 메뉴 처리기가 직접 수행하지 않으며 main.py에서 DB 쓰기 잠금 외부로 분리한다.
49. 기존 홈 번호/인증/메뉴 점프/방·발신자 격리/로그/SQLite 메모 동작과 배터리 정보를 보존한다.
"""
from __future__ import annotations

import re
import sqlite3
import threading
import time
from dataclasses import dataclass

from .market import Stock, StockQuoteError, WATCHLIST
from .personal_records import (CATEGORIES as PERSONAL_SECTORS, RecordError,
                               get_record, list_records, record_preview, record_detail, help_text)

MENU_TTL_SECONDS = 300
MAX_MENU_SESSIONS = 200


@dataclass(frozen=True)
class MenuChoice:
    label: str
    command_argument: str = ''
    page: str = ''


@dataclass(frozen=True)
class MenuAnswer:
    reply: str = ''
    execute_argument: str = ''
    menu_active: bool = False
    back: str = 'menu'


@dataclass(frozen=True)
class MenuState:
    expire_at: float
    choices: tuple[MenuChoice, ...]
    back: str = 'menu'
    origin: str = 'menu'


# 카카오톡 대메뉴와 하위 콘텐츠는 텍스트 라벨이 아니라 고정된 내부 카테고리 키로 분리한다.
# 외부 연동/개인정보/실행 권한이 필요한 새 콘텐츠는 기능 구현 후 명시적으로 연결한다.
CONTENT_ITEMS = {
    '배드민턴': ('강좌·기술', '영상 라이브러리', '자세 분석', '훈련 기록'),
    '요리': ('요리 추천', '레시피 찾기', '보유 재료 활용', '장보기'),
    '여행': ('여행지 추천', '여행 일정', '이동 경로', '맛집·숙소'),
    '종친': ('종친회 안내', '행사 일정', '계보·자료', '회비 안내'),
    '날씨': ('오늘 날씨', '내일 날씨', '주간 예보', '지역 설정'),
}


class StockSelectionMenus:
    def __init__(self, *, clock=time.monotonic):
        self._clock = clock
        self._lock = threading.RLock()
        self._states: dict[tuple[str, str], MenuState] = {}

    def _key(self, room: str, sender: str) -> tuple[str, str]:
        if not room.strip() or not sender.strip():
            raise StockQuoteError('메뉴는 채팅방과 발신자가 확인된 경우에만 사용할 수 있습니다.')
        return room, sender

    @staticmethod
    def _render(title: str, choices: tuple[MenuChoice, ...]) -> str:
        return '\n'.join([title, *(f'{i}. {choice.label}' for i, choice in enumerate(choices, 1)),
                          '※ 번호 입력 · 0: 이전 · 00: 홈 · 5분 유효'])

    def _save(self, key: tuple[str, str], choices: tuple[MenuChoice, ...], *, back: str = 'menu', origin: str = 'menu') -> None:
        now = self._clock()
        with self._lock:
            self._states = {k: v for k, v in self._states.items() if v.expire_at > now}
            if len(self._states) >= MAX_MENU_SESSIONS and key not in self._states:
                oldest = min(self._states, key=lambda k: self._states[k].expire_at)
                self._states.pop(oldest, None)
            self._states[key] = MenuState(now + MENU_TTL_SECONDS, choices, back, origin)


    @staticmethod
    def _home_choices() -> tuple[MenuChoice, ...]:
        """홈 항목의 단일 정의: 실제 응답과 전체 메뉴 트리에서 함께 사용한다."""
        return (
            MenuChoice('📈 주식', page='stock-root'),
            MenuChoice('🏠 부동산', page='records:root:부동산'),
            MenuChoice('💰 금융·투자', page='records:root:금융·투자'),
            MenuChoice('🧭 여행', page='category:여행'),
            MenuChoice('🏸 배드민턴', page='category:배드민턴'),
            MenuChoice('🍳 요리', page='category:요리'),
            MenuChoice('🌳 종친', page='category:종친'),
            MenuChoice('🌤 날씨', page='category:날씨'),
            MenuChoice('🗂 개인 메모·일정', page='records:root:개인'),
            MenuChoice('⚙️ 설정·운영', page='settings-root'),
        )

    @staticmethod
    def _stock_choices() -> tuple[MenuChoice, ...]:
        """주식 메뉴의 단일 정의."""
        return (
            MenuChoice('최근 사용한 주식 조회', page='recent'),
            MenuChoice('메모리7 현재 시세', command_argument='메모리7'),
            MenuChoice('반도체 그룹 시세', command_argument='반도체'),
            MenuChoice('미국시총10 시세', command_argument='미국시총10'),
            MenuChoice('관심종목 목록', command_argument='목록'),
            MenuChoice('종목별 분석', page='analysis'),
            MenuChoice('메모리7 시세 상세 보기', command_argument='메모리7 상세'),
        )

    @staticmethod
    def _settings_choices() -> tuple[MenuChoice, ...]:
        """운영 설정의 읽기 전용 항목. 1~6 기존 번호를 절대 변경하지 않는다."""
        return (
            MenuChoice('서버·서비스 상태 (통합)', page='ops:status'),
            MenuChoice('배포 버전·커밋', page='ops:deployment'),
            MenuChoice('최근 실행 로그', page='ops:logs'),
            MenuChoice('설정 현황 (읽기 전용)', page='ops:configuration'),
            MenuChoice('명령 통계', page='ops:stats'),
            MenuChoice('최근 오류', page='ops:errors'),
            MenuChoice('전체 메뉴 트리', page='ops:tree'),
            MenuChoice('도움말', page='ops:help'),
        )

    @staticmethod
    def _record_sector_choices(sector: str) -> tuple[MenuChoice, ...]:
        """개인 기록의 실제 메뉴 정의와 전체 트리·번호 이동에 같은 선택지를 사용한다."""
        if sector not in PERSONAL_SECTORS:
            raise StockQuoteError('지원하지 않는 기록 분야입니다.')
        choices = (
            MenuChoice('최근 메모 목록', page='records:list:' + sector),
            MenuChoice('메모 등록·검색 안내', page='records:help:' + sector),
        )
        if sector == '부동산':
            return (
                choices[0], choices[1],
                MenuChoice('아파트 매매 실거래가', command_argument='실거래조회 매매'),
                MenuChoice('아파트 전세 실거래가', command_argument='실거래조회 전세'),
                MenuChoice('아파트 월세 실거래가', command_argument='실거래조회 월세'),
                MenuChoice('조회 지역 설정 안내', command_argument='실거래설정 안내'),
            )
        if sector == '개인':
            return (
                choices[0],
                MenuChoice('다가오는 일정', page='records:upcoming:개인'),
                MenuChoice('메모 등록·검색 안내', page='records:help:개인'),
                MenuChoice('일정 등록·관리 안내', page='records:help:일정'),
            )
        return choices

    @staticmethod
    def _category_choices(category: str) -> tuple[MenuChoice, ...]:
        """현재 콘텐츠 정의를 재사용해 트리와 실사용 메뉴의 번호 일치를 보장한다."""
        if category == '날씨':
            return (
                MenuChoice('오늘 날씨', command_argument='날씨조회 오늘'),
                MenuChoice('내일 날씨', command_argument='날씨조회 내일'),
                MenuChoice('주간 예보', command_argument='날씨조회 주간'),
                MenuChoice('지역 설정', command_argument='날씨설정 안내'),
            )
        return tuple(MenuChoice(name, page='pending:' + category + ':' + name)
                     for name in CONTENT_ITEMS[category])

    @staticmethod
    def _analysis_choices() -> tuple[MenuChoice, ...]:
        """기존 종목 분석 하위 선택지를 단일 정의로 유지한다."""
        return tuple(MenuChoice(label, '분석 ' + label) for label in
                     ('삼성전자', '하이닉스', '마이크론', '엔비디아', '애플', '샌디스크', '메모리7'))

    @staticmethod
    def help_report() -> str:
        """설정 8번 간결 안내. 폐지한 카카오톡 사용자 명령은 표시하지 않는다."""
        return '\n'.join((
            '📖 앙개봇 도움말',
            '앙(홈) · 주(주식) · 설(설정)',
            '부(부동산) · 금(금융·투자) · 개(개인 메모·일정)',
            '여(여행) · 민(배드민턴) · 요(요리) · 종(종친) · 날(날씨)',
            '설 1 통합 상태 · 설 7 전체 메뉴 · 설 8 도움말',
            '주 2 간략 · 주 7 상세 · 시세표 9 상세/간략 · 주 분 삼성전자 분석',
            '앙 2/3/9 메모·일정 · 부 3~5 실거래 · 날 지역 서울',
            '1~10 선택 · 0 이전 · 00 홈 · 5분 유효 · ※ 시세 지연 가능',
        ))

    @classmethod
    def menu_tree(cls) -> str:
        """실제 메뉴 선택지에서 번호 경로를 재귀 구성하는 부작용 없는 전체 트리 조회.

        사용자별 최근 명령·관심그룹·시세 종목은 값과 수가 변하므로 표시 유형만
        안내한다. DB·API·네트워크를 조회하지 않으며 비밀키/사용자 정보는 포함하지 않는다.
        """
        lines = ['🗺 앙개봇 전체 메뉴 트리', '※ 번호는 홈에서 시작한 경로입니다.']

        def walk(choices: tuple[MenuChoice, ...], prefix: tuple[int, ...] = ()) -> None:
            for index, choice in enumerate(choices, 1):
                path = prefix + (index,)
                number = '-'.join(map(str, path))
                detail = ''
                if choice.page.startswith('pending:'):
                    detail = ' [개발 예정]'
                elif choice.page == 'recent':
                    detail = ' [본인 최근 조회 목록]'
                elif choice.command_argument == '목록':
                    detail = ' [본인 관심그룹 목록]'
                elif choice.command_argument in {'메모리7', '메모리7 상세', '반도체', '미국시총10'}:
                    detail = ' [조회 후 종목 선택]'
                lines.append('  ' * len(prefix) + f'{number}. {choice.label}{detail}')
                if choice.page == 'stock-root':
                    walk(cls._stock_choices(), path)
                elif choice.page == 'settings-root':
                    walk(cls._settings_choices(), path)
                elif choice.page.startswith('category:'):
                    walk(cls._category_choices(choice.page.split(':', 1)[1]), path)
                elif choice.page == 'analysis':
                    walk(cls._analysis_choices(), path)
                elif choice.page.startswith('records:root:'):
                    walk(cls._record_sector_choices(choice.page.split(':', 2)[2]), path)

        walk(cls._home_choices())
        lines.extend([
            '',
            '※ 빠른 이동: 앙 2 1 / 앙 2 3 / 앙 3 1 / 앙 9 2 / 앙 10 7 / 설 7',
            '※ 단축: 앙 홈 · 주 주식 · 부 부동산 · 금 금융·투자 · 개 개인 · 여 여행 · 민 배드민턴 · 요 요리 · 종 종친 · 날 날씨 · 설 설정',
            '※ 최근 조회·관심그룹·종목 번호는 실행 시 표시되는 실제 목록을 따릅니다.',
            '※ 읽기 전용 · 0 이전 · 00 홈 · 메뉴 선택 5분 유효',
        ])
        return '\n'.join(lines)

    def open_home(self, room: str, sender: str) -> MenuAnswer:
        key = self._key(room, sender)
        choices = self._home_choices()
        self._save(key, choices, back='home', origin='home')
        return MenuAnswer(self._render('🤖 앙개봇 메인 메뉴', choices), menu_active=True)

    def open_category(self, room: str, sender: str, category: str) -> MenuAnswer:
        key = self._key(room, sender)
        items = CONTENT_ITEMS.get(category)
        if items is None:
            raise StockQuoteError('등록되지 않은 콘텐츠 메뉴입니다.')
        choices = self._category_choices(category)
        self._save(key, choices, back='home', origin='category:' + category)
        footer = '\n※ 지역 변경: 날 지역 서울' if category == '날씨' else '\n※ 하위 기능은 순차적으로 개발됩니다.'
        return MenuAnswer(self._render('📂 ' + category + ' 메뉴', choices)
                          + footer, menu_active=True)

    def open_record_sector(self, room: str, sender: str, sector: str) -> MenuAnswer:
        """홈 개인 기록 분야. 제목 목록은 선택 때만 DB에서 읽고 내용은 저장하지 않는다."""
        key = self._key(room, sender)
        choices = self._record_sector_choices(sector)
        self._save(key, choices, back='home', origin='records-sector:' + sector)
        alias = '메모' if sector == '개인' else '부동산' if sector == '부동산' else '투자'
        return MenuAnswer(self._render('📂 ' + sector + ' 메뉴', choices)
                          + f'\n※ 등록: {alias} 추가 제목 | 내용'
                          + ('\n※ 조회 지역: 부 지역 강남구' if sector == '부동산' else ''),
                          menu_active=True)

    def open_record_results(self, room: str, sender: str,
                            rows, *, sector: str = '개인', heading: str = '최근 기록') -> MenuAnswer:
        """기록을 삭제/수정하지 않는 번호 선택용 목록. 세션에는 본문을 넣지 않는다."""
        key = self._key(room, sender)
        if sector not in PERSONAL_SECTORS and sector != '전체':
            raise StockQuoteError('지원하지 않는 개인 기록 메뉴입니다.')
        if not rows:
            if sector in PERSONAL_SECTORS:
                parent = self.open_record_sector(room, sender, sector)
                return MenuAnswer('📭 저장된 기록이 없습니다.\n\n' + parent.reply, menu_active=True)
            return MenuAnswer('📭 검색된 기록이 없습니다.\n※ 앙 또는 메로 다시 검색하세요.')
        choices = tuple(MenuChoice(record_preview(item), page=f'records:view:{item.id}:{sector}')
                        for item in rows[:10])
        self._save(key, choices, back='records-sector:' + sector if sector in PERSONAL_SECTORS else 'home',
                   origin='records-results')
        return MenuAnswer(self._render('🗂 ' + heading, choices), menu_active=True)

    def open_settings(self, room: str, sender: str) -> MenuAnswer:
        """읽기 전용 운영 조회 메뉴. 편집/재시작/권한 변경을 메뉴 선택에 연결하지 않는다."""
        key = self._key(room, sender)
        choices = self._settings_choices()
        self._save(key, choices, back='home', origin='settings')
        return MenuAnswer(self._render('⚙️ 설정·운영 메뉴', choices)
                          + '\n※ 조회 전용 · 설정 변경은 관리자 화면에서만', menu_active=True)

    def navigate_path(self, db: sqlite3.Connection, room: str, sender: str,
                      root: str, numbers: tuple[str, ...]) -> MenuAnswer:
        """메뉴 점프: 실제 메뉴 정의를 단계별로 따라가며 최종 선택만 실행한다.

        경로 전체는 1~10, 0, 00 중 최대 다섯 단계만 허용한다.
        중간 메모리7/그룹 선택은 실제 시세 HTTP를 중복 호출하지 않고
        기존 정확한 종목 메뉴를 준비한다. 마지막 종목 분석은 main.py가
        기존 인증·dedup·DB 잠금 외부의 조회 루틴으로만 실행한다.
        """
        if not numbers or len(numbers) > 5 or any(
            re.fullmatch(r'(?:00|10|[0-9])', number) is None for number in numbers
        ):
            raise StockQuoteError('메뉴 점프는 번호 1~10을 공백으로 최대 5개 입력하세요.')
        if root == '홈':
            answer = self.open_home(room, sender)
        elif root == '주식':
            answer = self.open(room, sender, back='home')
        elif root == '설정':
            answer = self.open_settings(room, sender)
        elif root in CONTENT_ITEMS:
            answer = self.open_category(room, sender, root)
        elif root in PERSONAL_SECTORS:
            answer = self.open_record_sector(room, sender, root)
        else:
            raise StockQuoteError('등록되지 않은 메뉴 점프 시작 메뉴입니다.')

        for i, number in enumerate(numbers):
            answer = self.choose(db, room, sender, number)
            last = i == len(numbers) - 1
            if last:
                return answer
            if answer.execute_argument:
                arg = answer.execute_argument.strip()
                from .watchlists import is_group_quote_request, load_group
                if arg in ('메모리7', '메모리7 상세'):
                    from .market import WATCHLIST
                    self.open_quotes(room, sender, WATCHLIST, back=answer.back,
                                     memory7_view='detail' if arg == '메모리7 상세' else 'compact')
                elif arg == '목록':
                    self.open_groups(db, room, sender)
                elif is_group_quote_request(arg):
                    group = load_group(db, room, sender, arg)
                    if not group:
                        raise StockQuoteError('빈 관심그룹에는 추가 숫자 선택이 없습니다.')
                    self.open_quotes(room, sender, group, back=answer.back)
                else:
                    raise StockQuoteError('이 메뉴는 마지막 선택 단계입니다. 이후 번호를 제거하세요.')
            elif not answer.menu_active:
                raise StockQuoteError('이 메뉴는 다음 하위 메뉴가 없습니다.')
            elif answer.reply.startswith('🛠'):
                raise StockQuoteError('개발 예정 기능에서는 추가 번호를 선택할 수 없습니다.')
        raise StockQuoteError('메뉴 점프 경로를 확인하세요.')

    def open(self, room: str, sender: str, *, back: str = 'menu') -> MenuAnswer:
        key = self._key(room, sender)
        choices = self._stock_choices()
        self._save(key, choices, back=back)
        return MenuAnswer(self._render('📊 주식 메뉴', choices), menu_active=True)

    def open_quotes(self, room: str, sender: str, stocks: tuple[Stock, ...], *,
                    back: str = 'menu', memory7_view: str = '') -> None:
        """시세표 번호/종목 분석 5분 보관. 메모리7 전용 9번만 간략↔상세 전환."""
        key = self._key(room, sender)
        if not stocks or len(stocks) > 10:
            raise StockQuoteError('선택 가능한 시세 종목 수는 1~10개여야 합니다.')
        if memory7_view not in ('', 'compact', 'detail'):
            raise StockQuoteError('지원되지 않는 시세 보기 모드입니다.')
        if memory7_view and (len(stocks) != len(WATCHLIST) or
                             tuple(s.ticker for s in stocks) != tuple(s.ticker for s in WATCHLIST)):
            raise StockQuoteError('9번 상세 전환은 메모리7 시세에서만 사용할 수 있습니다.')
        # 별칭이나 표시 이름이 중복돼도 고정된 허용 티커로만 분석한다.
        # 메시지 본문과 공급자 가격은 저장하지 않고 원래 조회 결과의 종목만 5분간 보관한다.
        choices = tuple(MenuChoice(stock.name, command_argument='분석 ' + stock.ticker)
                        for stock in stocks)
        if memory7_view == 'compact':
            choices += (MenuChoice('🔎 상세보기', command_argument='메모리7 상세'),)
        elif memory7_view == 'detail':
            choices += (MenuChoice('↩ 간략보기', command_argument='메모리7'),)
        self._save(key, choices, back=back)

    def open_groups(self, db: sqlite3.Connection, room: str, sender: str) -> None:
        """관심그룹 목록에 표시된 번호를 동일 순서의 시세 조회 명령으로 연결한다."""
        key = self._key(room, sender)
        rows = db.execute("""SELECT name FROM stock_groups
            WHERE room=? AND sender=? ORDER BY created_at,rowid""", (room, sender)).fetchall()
        choices = (MenuChoice('메모리7', command_argument='메모리7'),) + tuple(
            MenuChoice(name, command_argument=name) for (name,) in rows)
        self._save(key, choices, back='menu', origin='groups')

    @staticmethod
    def _recent(db: sqlite3.Connection, room: str, sender: str) -> tuple[MenuChoice, ...]:
        # 실행 가능한 성공한 읽기 명령만 표시. 그룹을 삭제했으면 과거 조회도 재실행하지 않는다.
        groups = {row[0] for row in db.execute(
            'SELECT name FROM stock_groups WHERE room=? AND sender=?', (room, sender)).fetchall()}
        rows = db.execute('''SELECT argument FROM jobs
            WHERE command='주식' AND room=? AND sender=? AND ok=1
            ORDER BY rowid DESC LIMIT 120''', (room, sender)).fetchall()
        result = []
        seen = set()
        for (raw,) in rows:
            argument = str(raw).strip()
            if argument in seen:
                continue
            if not (argument.startswith('분석 ') and argument[3:].strip() or
                    argument in ('메모리7', '메모리7 상세', '목록') or argument in groups):
                continue
            if len(argument) > 100:
                continue
            seen.add(argument)
            result.append(MenuChoice(argument, command_argument=argument))
            if len(result) == 8:
                break
        return tuple(result)

    def choose(self, db: sqlite3.Connection, room: str, sender: str, number: str) -> MenuAnswer:
        key = self._key(room, sender)
        if re.fullmatch(r'(?:00|10|[0-9])', number) is None:
            raise StockQuoteError('메뉴 번호는 1~10 중에서 선택하세요. 이전 메뉴는 0을 입력하세요.')
        with self._lock:
            state = self._states.get(key)
            if state is None or state.expire_at <= self._clock():
                self._states.pop(key, None)
                raise StockQuoteError('메뉴가 열려 있지 않거나 5분이 지났습니다. 앙 또는 주를 입력하세요.')
            if number == '00':
                self._states.pop(key, None)
                return self.open_home(room, sender)
            if number == '0':
                self._states.pop(key, None)
                back = state.back
                if back == 'home':
                    return self.open_home(room, sender)
                if back == 'settings':
                    return self.open_settings(room, sender)
                if back.startswith('records-sector:'):
                    return self.open_record_sector(room, sender, back.split(':', 1)[1])
                if back == 'groups':
                    self.open_groups(db, room, sender)
                    from .watchlists import execute_group_command
                    return MenuAnswer(execute_group_command(db, room, sender, '목록'), menu_active=True)
                return self.open(room, sender, back='home')
            index = int(number) - 1
            if index >= len(state.choices):
                raise StockQuoteError(f'메뉴에 없는 번호입니다. 1~{len(state.choices)}번 중 선택하세요.')
            choice = state.choices[index]
            # 하나를 선택하면 재선택/이중 실행 방지를 위해 현재 페이지를 즉시 닫는다.
            self._states.pop(key, None)
        if choice.page == 'stock-root':
            return self.open(room, sender, back='home')
        if choice.page == 'settings-root':
            return self.open_settings(room, sender)
        if choice.page.startswith('records:root:'):
            return self.open_record_sector(room, sender, choice.page.split(':', 2)[2])
        if choice.page.startswith('records:list:'):
            sector = choice.page.split(':', 2)[2]
            return self.open_record_results(room, sender,
                    list_records(db, room, sender, category=sector, kind='note'),
                    sector=sector, heading=sector + ' 최근 메모')
        if choice.page.startswith('records:upcoming:'):
            sector = choice.page.split(':', 2)[2]
            return self.open_record_results(room, sender,
                    list_records(db, room, sender, category=sector, kind='schedule', upcoming=True),
                    sector=sector, heading='다가오는 개인 일정')
        if choice.page.startswith('records:help:'):
            target = choice.page.split(':', 2)[2]
            sector = '개인' if target == '일정' else target
            command = '일정' if target == '일정' else '메모' if target == '개인' else '부동산' if target == '부동산' else '투자'
            parent = self.open_record_sector(room, sender, sector)
            return MenuAnswer(help_text(command) + '\n\n' + parent.reply, menu_active=True)
        if choice.page.startswith('records:view:'):
            _, _, id_text, sector = choice.page.split(':', 3)
            record = get_record(db, room, sender, int(id_text),
                                category=sector if sector in PERSONAL_SECTORS else None)
            parent = self.open_record_sector(room, sender, record.category)
            return MenuAnswer(record_detail(record) + '\n\n' + parent.reply, menu_active=True)
        if choice.page.startswith('ops:'):
            return MenuAnswer(execute_argument='설정보기 ' + choice.page.split(':', 1)[1],
                              back='settings')
        if choice.page.startswith('category:'):
            return self.open_category(room, sender, choice.page.split(':', 1)[1])
        if choice.page.startswith('pending:'):
            _, category, name = choice.page.split(':', 2)
            # 단독 '준비 중' 응답으로 메뉴가 닫히지 않도록 동일 카테고리 메뉴를 다시 보여준다.
            menu = self.open_category(room, sender, category)
            return MenuAnswer(f'🛠 {category} / {name}: 개발 예정입니다.\n\n{menu.reply}',
                              menu_active=True)
        if choice.page == 'recent':
            choices = self._recent(db, room, sender)
            if not choices:
                return MenuAnswer('📋 최근 성공한 주식 조회 명령이 없습니다. 주 분 삼성전자처럼 먼저 조회해 보세요.')
            self._save(key, choices, back='menu')
            return MenuAnswer(self._render('📋 내 최근 주식 조회 명령', choices), menu_active=True)
        if choice.page == 'analysis':
            choices = self._analysis_choices()
            self._save(key, choices, back='menu')
            return MenuAnswer(self._render('📈 분석할 종목 선택', choices), menu_active=True)
        return MenuAnswer(execute_argument=choice.command_argument,
                          back='groups' if state.origin == 'groups' else 'menu')
