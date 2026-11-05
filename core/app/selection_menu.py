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
"""
from __future__ import annotations

import re
import sqlite3
import threading
import time
from dataclasses import dataclass

from .market import Stock, StockQuoteError

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


@dataclass(frozen=True)
class MenuState:
    expire_at: float
    choices: tuple[MenuChoice, ...]


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
                          '※ 번호 입력 · 5분 유효'])

    def _save(self, key: tuple[str, str], choices: tuple[MenuChoice, ...]) -> None:
        now = self._clock()
        with self._lock:
            self._states = {k: v for k, v in self._states.items() if v.expire_at > now}
            if len(self._states) >= MAX_MENU_SESSIONS and key not in self._states:
                oldest = min(self._states, key=lambda k: self._states[k].expire_at)
                self._states.pop(oldest, None)
            self._states[key] = MenuState(now + MENU_TTL_SECONDS, choices)

    def open(self, room: str, sender: str) -> MenuAnswer:
        key = self._key(room, sender)
        choices = (
            MenuChoice('최근 사용한 주식 조회', page='recent'),
            MenuChoice('메모리7 현재 시세', command_argument='메모리7'),
            MenuChoice('반도체 그룹 시세', command_argument='반도체'),
            MenuChoice('미국시총10 시세', command_argument='미국시총10'),
            MenuChoice('관심종목 목록', command_argument='목록'),
            MenuChoice('종목별 분석', page='analysis'),
        )
        self._save(key, choices)
        return MenuAnswer(self._render('📊 주식 메뉴', choices), menu_active=True)

    def open_quotes(self, room: str, sender: str, stocks: tuple[Stock, ...]) -> None:
        """현재 시세표 번호와 정확히 같은 순서로 종목분석 선택 목록을 5분간 보관한다."""
        key = self._key(room, sender)
        if not stocks or len(stocks) > 10:
            raise StockQuoteError('선택 가능한 시세 종목 수는 1~10개여야 합니다.')
        # 별칭이나 표시 이름이 중복돼도 고정된 허용 티커로만 분석한다.
        # 메시지 본문과 공급자 가격은 저장하지 않고 원래 조회 결과의 종목만 5분간 보관한다.
        choices = tuple(MenuChoice(stock.name, command_argument='분석 ' + stock.ticker)
                        for stock in stocks)
        self._save(key, choices)

    def open_groups(self, db: sqlite3.Connection, room: str, sender: str) -> None:
        """관심그룹 목록에 표시된 번호를 동일 순서의 시세 조회 명령으로 연결한다."""
        key = self._key(room, sender)
        rows = db.execute("""SELECT name FROM stock_groups
            WHERE room=? AND sender=? ORDER BY created_at,rowid""", (room, sender)).fetchall()
        choices = (MenuChoice('메모리7', command_argument='메모리7'),) + tuple(
            MenuChoice(name, command_argument=name) for (name,) in rows)
        self._save(key, choices)

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
                    argument in ('메모리7', '목록') or argument in groups):
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
        if re.fullmatch(r'(?:10|[1-9])', number) is None:
            raise StockQuoteError('메뉴 번호는 1~10 중에서 선택하세요.')
        with self._lock:
            state = self._states.get(key)
            if state is None or state.expire_at <= self._clock():
                self._states.pop(key, None)
                raise StockQuoteError('메뉴가 열려 있지 않거나 5분이 지났습니다. 주를 입력하세요.')
            index = int(number) - 1
            if index >= len(state.choices):
                raise StockQuoteError(f'메뉴에 없는 번호입니다. 1~{len(state.choices)}번 중 선택하세요.')
            choice = state.choices[index]
            # 하나를 선택하면 재선택/이중 실행 방지를 위해 현재 페이지를 즉시 닫는다.
            self._states.pop(key, None)
        if choice.page == 'recent':
            choices = self._recent(db, room, sender)
            if not choices:
                return MenuAnswer('📋 최근 성공한 주식 조회 명령이 없습니다. 주 분 삼성전자처럼 먼저 조회해 보세요.')
            self._save(key, choices)
            return MenuAnswer(self._render('📋 내 최근 주식 조회 명령', choices), menu_active=True)
        if choice.page == 'analysis':
            choices = tuple(MenuChoice(label, '분석 ' + label) for label in
                            ('삼성전자', '하이닉스', '마이크론', '엔비디아', '애플', '샌디스크', '메모리7'))
            self._save(key, choices)
            return MenuAnswer(self._render('📈 분석할 종목 선택', choices), menu_active=True)
        return MenuAnswer(execute_argument=choice.command_argument)
