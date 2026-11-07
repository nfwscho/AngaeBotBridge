"""
앙개봇 개인 해야 할 일 관리 모듈 — 전체 기능 및 기존 데이터 보존
1. 인증된 카카오톡 방·발신자별 할 일 등록/목록/검색/상세/수정/완료/복원/삭제를 지원한다.
2. 기존 personal_records/AI/시세/주식그룹/jobs/events 테이블과 로그를 변경하지 않는다.
3. SQLite personal_todos 신규 테이블과 조회 인덱스만 추가하며 서버 재시작 뒤에도 할 일을 보존한다.
4. 기존 FastAPI 인증 및 요청 ID 중복 방지 트랜잭션 안에서 변경 명령을 실행한다.
5. 제목 60자, 상세 600자, 스코프당 최대 500건, 화면 목록 최대 10건 제한을 둔다.
6. 제목 앞의 YYYY-MM-DD는 선택형 마감일로 인식하며 실제 달력 날짜만 허용한다.
7. 할일 목록은 미완료 우선, 완료목록/전체/검색은 별도 조회하여 삭제 없이 이력을 남긴다.
8. 완료/복원은 반복 수행해도 안전하고, 삭제는 반드시 '할일 삭제 번호 확인'으로 재확인한다.
9. 모든 SQL 읽기·쓰기는 정확히 room/sender 일치 조건을 사용해 다른 사용자의 데이터 접근을 거부한다.
10. 메뉴의 1~10 숫자는 조회 전용 상세보기이며 완료/삭제는 명시적 명령으로만 실행한다.
11. 첫 해야 할 일은 사용자가 명시적으로 등록하며 다른 채팅방에 개인 점검 항목을 자동 노출하지 않는다.
12. 외부 API·Google 계정·원격 알림·일정 자동 발신·개인정보 수집 기능은 추가하지 않는다.
13. 카카오톡 메시지·SQLite 로그에 내용이 남을 수 있으므로 인증번호·비밀번호는 입력하지 않는다.
14. 기존 Android Bridge·선택 메뉴·배터리 정보·사진 자동전송 및 로그 동작을 유지한다.
15. v0.7.5는 기존 created_at/updated_at 컬럼을 읽어 등록·수정·완료 시각을 KST로 안내한다.
16. 목록의 1~10은 고유 #ID와 구별된 선택 번호로 보이고 세부 화면에서 안전한 관리 메뉴로 이동한다.
17. 확인 없는 단독 삭제를 계속 차단하고 기존 날짜/검색/범위/중복/SQL 인덱스를 보존한다.
"""
from __future__ import annotations

import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

MAX_TODOS = 500
LIST_LIMIT = 10
KST = timezone(timedelta(hours=9))


class TodoError(ValueError):
    """인증된 채팅 사용자에게 직접 표시할 수 있는 할 일 오류."""


@dataclass(frozen=True)
class Todo:
    id: int
    title: str
    detail: str
    due_date: str | None
    completed_at: int | None
    created_at: int = 0
    updated_at: int = 0


@dataclass(frozen=True)
class TodoResult:
    reply: str
    rows: tuple[Todo, ...] | None = None


def init_todos_schema(db: sqlite3.Connection) -> None:
    """다른 테이블과 기존 로그·데이터는 전혀 손대지 않는다."""
    db.execute("""CREATE TABLE IF NOT EXISTS personal_todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room TEXT NOT NULL, sender TEXT NOT NULL,
        title TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '',
        due_date TEXT, completed_at INTEGER,
        created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL
    )""")
    db.execute("""CREATE INDEX IF NOT EXISTS idx_personal_todos_scope
        ON personal_todos(room,sender,completed_at,due_date,id)""")


def _scope(room: str, sender: str) -> None:
    if not room.strip() or not sender.strip():
        raise TodoError("할 일은 채팅방과 발신자를 확인한 경우에만 저장합니다.")


def _identifier(value: str) -> int:
    value = value.removeprefix('#')
    if not re.fullmatch(r'[1-9]\d{0,8}', value):
        raise TodoError("할 일 번호를 입력하세요. 예: 할일 완료 12")
    return int(value)


def _date(value: str) -> str:
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise TodoError("마감일 형식: YYYY-MM-DD")
    try:
        datetime.strptime(value, '%Y-%m-%d')
    except ValueError as exc:
        raise TodoError("달력에 존재하는 날짜를 입력하세요.") from exc
    return value


def _payload(text: str) -> tuple[str, str, str | None]:
    content = text.strip()
    due_date = None
    first, sep, rest = content.partition(' ')
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', first):
        due_date = _date(first)
        content = rest.strip() if sep else ''
    title, _, detail = content.partition('|')
    title, detail = title.strip(), detail.strip()
    if not (1 <= len(title) <= 60):
        raise TodoError("제목은 1~60자로 입력하세요. 예: 할일 추가 S20+ Extend Unlock 확인")
    if len(detail) > 600:
        raise TodoError("상세 내용은 최대 600자입니다.")
    if any(ord(c) < 32 and c not in '\n\t' for c in title + detail):
        raise TodoError("제어문자는 사용할 수 없습니다.")
    return title, detail, due_date


def _todo(row: tuple) -> Todo:
    return Todo(int(row[0]), str(row[1]), str(row[2]),
                str(row[3]) if row[3] is not None else None,
                int(row[4]) if row[4] is not None else None,
                int(row[5]), int(row[6]))


def list_todos(db: sqlite3.Connection, room: str, sender: str, *,
               state: str = 'open', query: str | None = None,
               limit: int = LIST_LIMIT) -> tuple[Todo, ...]:
    _scope(room, sender)
    if state not in ('open', 'done', 'all'):
        raise TodoError("목록 상태를 확인하세요.")
    where = ['room=?', 'sender=?']
    args: list[object] = [room, sender]
    if state == 'open':
        where.append('completed_at IS NULL')
    elif state == 'done':
        where.append('completed_at IS NOT NULL')
    if query is not None:
        word = query.strip()
        if not word or len(word) > 60:
            raise TodoError("검색어는 1~60자로 입력하세요.")
        escaped = word.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        where.append("(title LIKE ? ESCAPE '\\' OR detail LIKE ? ESCAPE '\\')")
        args.extend(('%' + escaped + '%', '%' + escaped + '%'))
    args.append(max(1, min(int(limit), LIST_LIMIT)))
    return tuple(_todo(row) for row in db.execute(
        'SELECT id,title,detail,due_date,completed_at,created_at,updated_at FROM personal_todos WHERE ' +
        ' AND '.join(where) +
        " ORDER BY (completed_at IS NOT NULL) ASC, COALESCE(due_date,'9999-12-31') ASC, id DESC LIMIT ?",
        args).fetchall())


def get_todo(db: sqlite3.Connection, room: str, sender: str, identifier: int) -> Todo:
    _scope(room, sender)
    row = db.execute('''SELECT id,title,detail,due_date,completed_at,created_at,updated_at FROM personal_todos
        WHERE id=? AND room=? AND sender=?''', (identifier, room, sender)).fetchone()
    if row is None:
        raise TodoError("해당 할 일을 찾을 수 없습니다. 번호와 채팅방을 확인하세요.")
    return _todo(row)


def _korean_time(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, KST).strftime('%Y-%m-%d %H:%M')


def todo_preview(todo: Todo) -> str:
    symbol = '☑' if todo.completed_at is not None else '☐'
    due = (todo.due_date + ' ') if todo.due_date else ''
    registered = datetime.fromtimestamp(todo.created_at, KST).strftime('%m/%d %H:%M')
    return f'{symbol} [#{todo.id}] {due}{" ".join(todo.title.split())[:32]} · 등록 {registered}'


def todo_detail(todo: Todo) -> str:
    status = '✅ 완료' if todo.completed_at is not None else '⬜ 미완료'
    due = todo.due_date or '기한 없음'
    changed = (f'\n수정: {_korean_time(todo.updated_at)}' if todo.updated_at > todo.created_at
               else '')
    finished = (f'\n완료: {_korean_time(todo.completed_at)}'
                if todo.completed_at is not None else '')
    return (f'📋 할 일 #{todo.id} · {status}\n'
            f'{todo.title}\n등록: {_korean_time(todo.created_at)} (KST){changed}{finished}\n'
            f'기한: {due}\n{todo.detail or "(상세 내용 없음)"}\n'
            f'※ 직접 명령: 할일 수정 {todo.id} 새 제목 | 상세 내용')


def todo_help() -> str:
    return ('✅ 해야 할 일 사용법\n'
            '할일 추가 S20+ Extend Unlock 확인\n'
            '할일 추가 2026-11-10 제목 | 상세 내용\n'
            '할일 목록 · 할일 전체 · 할일 완료목록 · 할일 검색 키워드\n'
            '할일 보기 번호 · 할일 완료 번호 · 할일 복원 번호\n'
            '할일 수정 번호 새 제목 | 상세 내용\n'
            '할일 기한 번호 YYYY-MM-DD · 할일 기한 번호 없음\n'
            '할일 삭제 번호 확인\n'
            '※ 개 5 할일 추가 제목 도 가능하며, 항목 번호를 누르면 관리 메뉴가 열립니다.')


def execute_todo_command(db: sqlite3.Connection, room: str, sender: str,
                         argument: str) -> TodoResult:
    """인증 및 request_id 중복 검사를 거친 기존 jobs 트랜잭션에서 실행된다."""
    _scope(room, sender)
    action, _, remainder = argument.strip().partition(' ')
    remainder = remainder.strip()
    if not action or action in ('목록', '전체', '완료목록', '검색'):
        if action == '검색' and not remainder:
            raise TodoError("검색어를 입력하세요. 예: 할일 검색 Extend")
        if action != '검색' and remainder:
            raise TodoError("목록 명령 뒤에는 다른 입력을 넣지 마세요.")
        state = 'done' if action == '완료목록' else 'all' if action in ('전체', '검색') else 'open'
        heading = '완료한 일' if state == 'done' else '전체 할 일' if state == 'all' else '해야 할 일'
        rows = list_todos(db, room, sender, state=state,
                          query=remainder if action == '검색' else None)
        return TodoResult(heading if action != '검색' else '검색된 할 일', rows=rows)
    if action in ('도움말', '안내'):
        return TodoResult(todo_help())
    if action == '추가':
        title, detail, due_date = _payload(remainder)
        count = db.execute('SELECT COUNT(*) FROM personal_todos WHERE room=? AND sender=?',
                           (room, sender)).fetchone()[0]
        if count >= MAX_TODOS:
            raise TodoError("해야 할 일은 최대 500건입니다. 완료한 항목을 확인해 정리하세요.")
        now = int(time.time())
        cur = db.execute('''INSERT INTO personal_todos
            (room,sender,title,detail,due_date,completed_at,created_at,updated_at)
            VALUES (?,?,?,?,?,NULL,?,?)''',
            (room, sender, title, detail, due_date, now, now))
        return TodoResult(f'✅ 할 일 등록 #{cur.lastrowid}\n{title}\n'
                          f'등록: {_korean_time(now)} (KST)\n'
                          f'※ 개 5 / 할일 목록 · 할일 완료 {cur.lastrowid}')
    if action == '보기':
        return TodoResult(todo_detail(get_todo(db, room, sender, _identifier(remainder))))
    if action in ('완료', '복원', '삭제', '수정', '기한'):
        id_value, _, trailing = remainder.partition(' ')
        identifier = _identifier(id_value)
        record = get_todo(db, room, sender, identifier)
        now = int(time.time())
        if action == '완료':
            if trailing.strip():
                raise TodoError("사용법: 할일 완료 번호")
            if record.completed_at is None:
                db.execute('''UPDATE personal_todos SET completed_at=?,updated_at=?
                    WHERE id=? AND room=? AND sender=?''', (now, now, identifier, room, sender))
            return TodoResult(f'✅ 할 일 완료 #{identifier} · {record.title}')
        if action == '복원':
            if trailing.strip():
                raise TodoError("사용법: 할일 복원 번호")
            if record.completed_at is not None:
                db.execute('''UPDATE personal_todos SET completed_at=NULL,updated_at=?
                    WHERE id=? AND room=? AND sender=?''', (now, identifier, room, sender))
            return TodoResult(f'↩️ 다시 해야 할 일 #{identifier} · {record.title}')
        if action == '삭제':
            if trailing.strip() != '확인':
                raise TodoError(f'정말 삭제하려면 "할일 삭제 {identifier} 확인"을 입력하세요.')
            db.execute('DELETE FROM personal_todos WHERE id=? AND room=? AND sender=?',
                       (identifier, room, sender))
            return TodoResult(f'🗑 할 일 #{identifier} 삭제 완료')
        if action == '수정':
            if not trailing.strip():
                raise TodoError(f'사용법: 할일 수정 {identifier} 새 제목 | 상세 내용')
            title, detail, due = _payload(trailing)
            # 날짜를 지정하지 않은 수정은 원래 마감일을 보존한다.
            db.execute('''UPDATE personal_todos
                SET title=?,detail=?,due_date=?,updated_at=? WHERE id=? AND room=? AND sender=?''',
                (title, detail, due if due is not None else record.due_date, now,
                 identifier, room, sender))
            return TodoResult(f'✅ 할 일 수정 #{identifier} · {title}')
        if not trailing.strip():
            raise TodoError(f'사용법: 할일 기한 {identifier} YYYY-MM-DD / 없음')
        due_date = None if trailing.strip() == '없음' else _date(trailing.strip())
        db.execute('''UPDATE personal_todos SET due_date=?,updated_at=?
            WHERE id=? AND room=? AND sender=?''', (due_date, now, identifier, room, sender))
        return TodoResult(f'📅 할 일 #{identifier} 기한: {due_date or "없음"}')
    raise TodoError(todo_help())
