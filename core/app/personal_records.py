"""
앙개봇 Python Core v0.7.0 개인 기록 모듈 — 전체 기능 및 개인정보 보호 지침
1. 부동산·금융투자·개인 메모 세 분야와 개인 일정의 등록/조회/검색/수정/삭제를 지원한다.
2. FastAPI 인증을 통과한 명령만 호출하며 모든 데이터는 정확한 카톡 방·발신자 조합으로 격리한다.
3. SQLite에 personal_records 테이블과 조회 인덱스만 생성하고 기존 DB/jobs/events/AI/주식 자료는 변경하지 않는다.
4. 메모는 제목/본문을 저장하고 일정은 ISO YYYY-MM-DD 날짜/제목/본문을 저장한다.
5. 등록·수정·삭제는 요청 ID 기반 기존 jobs 트랜잭션 안에서만 실행해 중복 요청을 방지한다.
6. 목록은 최대 10건만 반환하며 자세한 본문은 '보기 번호' 또는 5분 메뉴 번호 선택 때만 표시한다.
7. 제목 60자·본문 600자·검색어 60자·사용자당 500건을 제한하여 무제한 저장/과도한 답장을 막는다.
8. 날짜는 실제 달력 날짜로 검증하며 다가오는 일정은 한국 날짜를 기준으로 정렬한다.
9. 모든 조회·변경 SQL에는 room/sender/category/kind 조건을 바인딩해 다른 사용자의 ID를 알더라도 접근 못하게 한다.
10. 삭제는 '삭제 ID 확인'으로 명시적 재확인을 요구하며 기존 과거 로그는 임의로 삭제하지 않는다.
11. 외부 서버·Google/Samsung Notes·AI·검색 API·알림 발신/매매와 연결하지 않는다.
12. 검색에서는 LIKE 특수기호(%, _, 역슬래시)를 이스케이프하여 문자 그대로 검색한다.
13. 카카오톡/SQLite에는 내용이 남을 수 있으므로 비밀번호·계좌 비밀·민감한 인증정보는 저장하지 않는다.
14. 메뉴용 조회 함수와 카톡 명령어를 하나의 모듈로 분리해 메뉴 코드의 수정 범위를 최소화한다.
"""
from __future__ import annotations

import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

PERSONAL_COMMANDS = frozenset({'부동산', '투자', '금융', '메모', '일정', '기록'})
CATEGORIES = ('부동산', '금융·투자', '개인')
KST = timezone(timedelta(hours=9))
MAX_RECORDS_PER_SCOPE = 500
LIST_LIMIT = 10


class RecordError(ValueError):
    """사람에게 표시해도 안전한 개인 기록 명령 오류."""


@dataclass(frozen=True)
class Record:
    id: int
    category: str
    kind: str
    title: str
    body: str
    due_date: str | None


@dataclass(frozen=True)
class RecordResult:
    reply: str
    rows: tuple[Record, ...] | None = None
    sector: str = '개인'


def init_records_schema(db: sqlite3.Connection) -> None:
    """기존 테이블에 손대지 않고 신규 스키마만 생성한다."""
    db.execute("""CREATE TABLE IF NOT EXISTS personal_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room TEXT NOT NULL, sender TEXT NOT NULL,
        category TEXT NOT NULL CHECK (category IN ('부동산','금융·투자','개인')),
        kind TEXT NOT NULL CHECK (kind IN ('note','schedule')),
        title TEXT NOT NULL, body TEXT NOT NULL DEFAULT '',
        due_date TEXT,
        created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL
    )""")
    db.execute("""CREATE INDEX IF NOT EXISTS idx_personal_records_scope
        ON personal_records(room,sender,category,kind,updated_at DESC)""")
    db.execute("""CREATE INDEX IF NOT EXISTS idx_personal_records_schedule
        ON personal_records(room,sender,kind,due_date)""")


def _scope(room: str, sender: str) -> None:
    if not room.strip() or not sender.strip():
        raise RecordError('개인 기록은 채팅방과 발신자가 확인된 경우에만 이용할 수 있습니다.')


def _category(command: str) -> tuple[str | None, str | None]:
    if command == '부동산':
        return '부동산', 'note'
    if command in {'투자', '금융'}:
        return '금융·투자', 'note'
    if command == '메모':
        return '개인', 'note'
    if command == '일정':
        return '개인', 'schedule'
    if command == '기록':
        return None, None
    raise RecordError('등록되지 않은 기록 분야입니다.')


def _date(value: str) -> str:
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise RecordError('날짜 형식: 2026-12-01 (YYYY-MM-DD)')
    try:
        datetime.strptime(value, '%Y-%m-%d')
    except ValueError as error:
        raise RecordError('달력에 존재하는 날짜를 입력하세요.') from error
    return value


def _parse_id(value: str) -> int:
    if not re.fullmatch(r'[1-9][0-9]{0,8}', value):
        raise RecordError('기록 번호는 양의 정수여야 합니다. 예: 메모 보기 12')
    return int(value)


def _payload(text: str, kind: str) -> tuple[str, str, str | None]:
    value = text.strip()
    due = None
    if kind == 'schedule':
        date_str, sep, tail = value.partition(' ')
        if not sep:
            raise RecordError('일정 추가 사용법: 일정 추가 2026-12-01 제목 | 내용')
        due = _date(date_str)
        value = tail.strip()
    title, delimiter, body = value.partition('|')
    title = title.strip()
    body = body.strip() if delimiter else ''
    if not title or len(title) > 60:
        raise RecordError('제목은 1~60자로 입력하세요.')
    if len(body) > 600:
        raise RecordError('내용은 600자 이내로 입력하세요.')
    if any(ord(c) < 32 and c not in '\n\t' for c in title + body):
        raise RecordError('제어문자는 사용할 수 없습니다.')
    return title, body, due


def _row(row: tuple) -> Record:
    return Record(int(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]),
                  str(row[5]) if row[5] is not None else None)


def list_records(db: sqlite3.Connection, room: str, sender: str, *,
                 category: str | None = None, kind: str | None = None,
                 query: str | None = None, upcoming: bool = False,
                 limit: int = LIST_LIMIT) -> tuple[Record, ...]:
    """반환 건수·검색 문자·스코프를 제한한 안전한 읽기 쿼리."""
    _scope(room, sender)
    if category is not None and category not in CATEGORIES:
        raise RecordError('지원하지 않는 기록 분야입니다.')
    if kind is not None and kind not in ('note', 'schedule'):
        raise RecordError('지원하지 않는 기록 유형입니다.')
    clauses = ['room=?', 'sender=?']
    params: list = [room, sender]
    if category is not None:
        clauses.append('category=?')
        params.append(category)
    if kind is not None:
        clauses.append('kind=?')
        params.append(kind)
    if query is not None:
        word = query.strip()
        if not word or len(word) > 60:
            raise RecordError('검색어는 1~60자로 입력하세요.')
        escaped = word.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        clauses.append("(title LIKE ? ESCAPE '\\' OR body LIKE ? ESCAPE '\\')")
        params.extend(['%' + escaped + '%', '%' + escaped + '%'])
    if upcoming:
        clauses.append("kind='schedule'")
        clauses.append('due_date>=?')
        params.append(datetime.now(KST).date().isoformat())
    order = 'due_date ASC,id ASC' if upcoming else 'updated_at DESC,id DESC'
    statement = ('SELECT id,category,kind,title,body,due_date FROM personal_records WHERE ' +
                 ' AND '.join(clauses) + ' ORDER BY ' + order + ' LIMIT ?')
    params.append(max(1, min(int(limit), LIST_LIMIT)))
    return tuple(_row(row) for row in db.execute(statement, params).fetchall())


def get_record(db: sqlite3.Connection, room: str, sender: str, identifier: int, *,
               category: str | None = None, kind: str | None = None) -> Record:
    _scope(room, sender)
    where = ['id=?', 'room=?', 'sender=?']
    args: list = [identifier, room, sender]
    if category:
        where.append('category=?')
        args.append(category)
    if kind:
        where.append('kind=?')
        args.append(kind)
    sql = 'SELECT id,category,kind,title,body,due_date FROM personal_records WHERE ' + ' AND '.join(where)
    row = db.execute(sql, args).fetchone()
    if row is None:
        raise RecordError('기록을 찾지 못했습니다. 번호 또는 접근 가능한 채팅방을 확인하세요.')
    return _row(row)


def record_detail(record: Record) -> str:
    heading = '📅 일정' if record.kind == 'schedule' else '📒 메모'
    date_label = f' · {record.due_date}' if record.due_date else ''
    return (f'{heading} #{record.id} · {record.category}{date_label}\n'
            f'{record.title}\n{record.body or "(내용 없음)"}\n'
            f'※ 수정/삭제: 해당 분야 명령 + 번호 (도움말 참조)')


def record_preview(record: Record) -> str:
    title = ' '.join(record.title.split())[:32]
    date = (record.due_date + ' ') if record.due_date else ''
    return f'{date}{title} (#{record.id})'


def help_text(command: str) -> str:
    if command == '기록':
        return ('📚 전체 기록 검색\n기록 검색 키워드 · 기록 목록 · 기록 보기 번호\n'
                '※ 모든 분야를 통합 검색합니다. 등록은 분야별 명령을 이용하세요.')
    if command == '일정':
        return ('📅 개인 일정\n일정 추가 2026-12-01 제목 | 내용\n'
                '일정 목록 · 일정 검색 키워드 · 일정 보기 번호\n'
                '일정 수정 번호 2026-12-01 제목 | 내용\n일정 삭제 번호 확인')
    category = '개인 메모' if command == '메모' else '금융·투자' if command in {'투자', '금융'} else '부동산'
    name = command
    return (f'📒 {category} 관리\n{name} 추가 제목 | 내용\n'
            f'{name} 목록 · {name} 검색 키워드 · {name} 보기 번호\n'
            f'{name} 수정 번호 제목 | 내용\n{name} 삭제 번호 확인')


def execute_record_command(db: sqlite3.Connection, room: str, sender: str,
                           command: str, argument: str) -> RecordResult:
    """기존 jobs 트랜잭션 안에서 호출되며 개인 기록 외 데이터는 갱신하지 않는다."""
    _scope(room, sender)
    category, kind = _category(command)
    action, sep, remainder = argument.strip().partition(' ')
    remainder = remainder.strip()
    if not action or action == '도움말':
        return RecordResult(help_text(command), sector=category or '전체')
    if action in {'목록', '검색', '다가오는'}:
        if action == '검색' and not remainder:
            raise RecordError(f'검색어를 입력하세요. 예: {command} 검색 계약')
        if action != '검색' and remainder:
            raise RecordError('목록 명령에는 추가 인수가 필요하지 않습니다.')
        upcoming = action == '다가오는' or (command == '일정' and action == '목록')
        if upcoming and command not in {'일정', '기록'}:
            raise RecordError('다가오는 일정은 일정 목록으로 확인하세요.')
        rows = list_records(db, room, sender, category=category, kind=kind,
                            query=remainder if action == '검색' else None, upcoming=upcoming)
        title = '검색 결과' if action == '검색' else '다가오는 일정' if upcoming else '최근 기록'
        return RecordResult(f'🗂 {title}', rows=rows, sector=category or '전체')
    if action == '보기':
        record = get_record(db, room, sender, _parse_id(remainder), category=category, kind=kind)
        return RecordResult(record_detail(record), sector=record.category)
    if action == '추가':
        if command == '기록':
            raise RecordError('등록은 메모/일정/부동산/투자 명령으로 입력하세요.')
        title, body, due = _payload(remainder, kind or 'note')
        count = db.execute('SELECT COUNT(*) FROM personal_records WHERE room=? AND sender=?',
                           (room, sender)).fetchone()[0]
        if count >= MAX_RECORDS_PER_SCOPE:
            raise RecordError('기록이 500건입니다. 불필요한 기록을 정리하세요.')
        now = int(time.time())
        cursor = db.execute('''INSERT INTO personal_records
             (room,sender,category,kind,title,body,due_date,created_at,updated_at)
             VALUES (?,?,?,?,?,?,?,?,?)''',
             (room, sender, category, kind, title, body, due, now, now))
        return RecordResult(f'✅ {category} {"일정" if kind == "schedule" else "메모"} 등록 #{cursor.lastrowid}\n'
                            f'{title[:32]}\n※ {command} 보기 {cursor.lastrowid}', sector=category or '개인')
    if action in {'수정', '삭제'}:
        if command == '기록':
            raise RecordError('변경은 등록했던 분야 명령을 이용하세요.')
        id_text, delimiter, rest = remainder.partition(' ')
        identifier = _parse_id(id_text)
        record = get_record(db, room, sender, identifier, category=category, kind=kind)
        if action == '삭제':
            if rest.strip() != '확인':
                raise RecordError(f'삭제하려면 {command} 삭제 {identifier} 확인 을 입력하세요.')
            db.execute('DELETE FROM personal_records WHERE id=? AND room=? AND sender=? AND category=? AND kind=?',
                       (identifier, room, sender, record.category, record.kind))
            return RecordResult(f'🗑 {record.category} 기록 #{identifier} 삭제 완료', sector=record.category)
        if not delimiter:
            raise RecordError(f'수정 사용법: {command} 수정 {identifier} 제목 | 내용')
        title, body, due = _payload(rest, kind or 'note')
        db.execute('''UPDATE personal_records SET title=?,body=?,due_date=?,updated_at=?
             WHERE id=? AND room=? AND sender=? AND category=? AND kind=?''',
             (title, body, due, int(time.time()), identifier, room, sender, record.category, record.kind))
        return RecordResult(f'✅ {record.category} 기록 #{identifier} 수정 완료', sector=record.category)
    raise RecordError(help_text(command))
