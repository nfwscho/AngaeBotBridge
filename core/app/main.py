"""
앙개봇 Python Core v0.5.10 FastAPI 서버 — 전체 구현 기능 상세 설명
1. v0.2의 127.0.0.1:8765 바인딩, X-AngaeBot-Token 인증/constant-time 검사 유지.
2. GET /v1/health, POST /v1/commands의 기존 응답 필드·호환성 유지.
3. 계산/시간/서버상태 허용 명령, 요청 ID 기반 SQLite 중복 방지, events/jobs 로그 유지.
4. v0.3 새 명령 '질문', '요약', 'AI상태', '대화초기화'를 안전하게 추가한다.
5. AI 제공자는 OpenAI 또는 Ollama의 호환 Chat Completions API를 환경변수로 선택한다.
6. 기존 .env의 인증키와 모든 SQLite 데이터/이전 작업 로그/Android UI를 변경·삭제하지 않는다.
7. AI 기능은 기본 OFF이며 활성화/설정 전에는 외부로 사용자 질문을 보내지 않는다.
8. 대화는 표시 채팅방·발신자 단위의 SQLite 별도 테이블로 분리하고 최근 6회(설정값)만 문맥에 사용한다.
9. '대화초기화'는 새 세대로 전환할 뿐 기존 jobs/events/대화 로그를 삭제하지 않는다.
10. AI 응답 실패 시 기존 로컬 Python 명령은 계속 동작하고 비밀키/원문을 에러 로그로 노출하지 않는다.
11. 기존 create_app 주입 테스트 구조와 응답 중복 필드를 유지한다.
12. 임의 셸·파일 접근, 외부 PC 제어, AI 도구 호출 등 위험한 실행 기능은 제공하지 않는다.
13. v0.3.1 서버 단일 실행/로그 보관/runit 복구는 별도 운영 스크립트가 처리하며 API 호환은 유지한다.
14. v0.4.0 상세상태/통계/최근오류/가동시간 명령을 추가하고 기존 모든 명령/로그·DB 구조를 보존한다.
15. 운영 조회는 같은 채팅방·발신자 기록만 반환하며 AI OFF에서 작동하고 별도 원격 실행은 없다.
16. v0.4.1 주식 메모리7/메모리7 명령을 추가하며 한국·미국·일본 8개 종목의 전일 대비 등락률을 제공한다.
17. 시세 조회는 외부 무료 HTTPS 시세 API만 사용하며 OpenAI API/앱 권한/기존 로그·DB를 변경하지 않는다.
18. 중복 요청 확인 후 시세 조회는 SQLite 쓰기 잠금 밖에서 진행해 기존 명령 지연을 최소화한다.
19. v0.4.3 국내 주식 네이버 금융과 키오시아 일본 공급자 폴백을 추가하고 API/로그 호환을 유지한다.
20. v0.5.0 '주식 목록/그룹생성/추가/삭제/그룹삭제/그룹조회'를 추가하며 메모리7 원본을 보호한다.
21. 관심종목은 room/sender별 신규 stock_groups/stock_items 테이블에만 저장하며 기존 DB/로그는 보존한다.
22. 그룹 CRUD는 jobs/events 기록과 같은 SQLite 트랜잭션에서 실행하여 요청 ID 중복 실행을 막는다.
23. 관심그룹 시세 조회는 SQLite 쓰기 락 밖에서 시행하고 다른 명령의 응답 및 로그를 유지한다.
24. v0.5.1 '주식 프리셋 미국시총10'과 일반 그룹 최대 10종목을 기존 인증 API/SQLite 트랜잭션에 추가한다.
25. 그룹 이름·종목의 기존 CRUD/조회, 날짜·무료 시세/오류/로그, AI OFF, 메모리7 8종목을 유지한다.
26. 새 기능은 기존 Android Bridge '주식' 명령을 그대로 사용해 APK 재설치 및 AI 설정을 요구하지 않는다.
27. v0.5.2 주식 분석 [티커/그룹명/메모리7]으로 5거래일 종가와 21·63거래일의 수익률·실현변동성을 조회한다.
28. 모든 역사적 시세 조회는 DB 쓰기 락 밖에서만 시행하고 SQLite 테이블·인증키·메모리7 기존 가격 모듈은 그대로 유지한다.
29. 그룹 분석은 해당 room/sender의 기존 그룹만 접근할 수 있고 5분 캐시·요청시간 제한으로 과도한 트래픽을 피한다.
30. 가격 조건 알림·예약/자동발신·주식 자동주문은 구현하지 않으며 OpenAI/Ollama의 활성화 없이 분석 명령을 실행한다.
31. v0.5.3 주식 분석의 대상 종목을 한글 기업명/티커·사용자별 저장 별칭으로 조회하며 그룹명 우선순위를 유지한다.
32. 중복 또는 다른 사용자의 별칭을 무단 조회하지 않고 종목코드가 모호하면 명확하게 거부한다.
33. 기존 FastAPI 인증·중복 실행 방지·DB 잠금 밖 시세 조회·전체 운영 로그 및 과거 시세 로직을 보존한다.
34. v0.5.4 SQLite 자원 정리: 기존 FastAPI 모든 연결의 명시적 close 보증을 별도 회귀 테스트로 검사하며 동작·로그·DB는 그대로 보존한다.
35. 기존 주식명·별칭·그룹·메모리7·과거시세·AI OFF 및 인증/중복요청 흐름은 변경하지 않는다.
36. v0.5.5은 '주식 메뉴' / '주식 선택 숫자' 요청을 인증된 기존 API에서 처리한다.
37. 1~6 숫자 메뉴는 채팅방·발신자별 5분 세션에서만 동작하고 AI/등록/삭제/매매는 재실행하지 않는다.
38. 기존 성공한 읽기 명령만 최근 메뉴에서 가져오며 DB 스키마·jobs/events 원형·로그를 보존한다.
39. API의 신규 menu_active 값은 Android에 메뉴 유지 여부를 알리고 기존 응답 필드는 바꾸지 않는다.
40. v0.5.6은 성공한 메모리7/관심그룹 시세 조회 직후 동일 방·발신자 범위에 최대 10개 번호 선택 세션을 활성화한다.
41. 숫자 선택은 기존 메뉴 분석 경로·인증·jobs/events·dedup·쓰기 잠금 밖 시세 조회를 재사용하며 추가 DB 테이블이 없다.
42. 시세 공급자 전체 실패 시 메뉴를 새로 열지 않고, 기존 S20+ 배터리/앱 UI/로그·설정은 그대로 보존한다.
43. v0.5.7 한국 두 종목은 네이버 폴링 우선·지연/시장상태/체결시각 검증 결과를 기존 응답에 함께 표시한다.
44. 네이버 시간외 가격은 KRX 본장과 분리하며 사용자 그룹·숫자 선택·이벤트/작업 로그·인증·AI OFF는 유지한다.
45. Android Bridge 앱/배터리 정보·DB 스키마/세션·과거 종가/변동성 계산은 변경하지 않는다.
46. v0.5.8 미국 종목의 Yahoo Chart 오류 발생 시 나스닥 공개 웹 시세 보조 조회는 market.py에서만 수행한다.
47. 해당 보조 조회는 원래 DB 락 외부/인증/요청 중복·로깅 흐름으로 실행하고 인증키/사용자 데이터/스키마는 변경하지 않는다.
48. 나스닥 시세는 지연 여부를 임의로 실시간이라고 표시하지 않고, 실패하면 종목별 조회 불가로 격리한다.
49. 국내 네이버·일본 키오시아·기존 과거 데이터 분석·숫자 메뉴·Android 배터리·AI OFF·전체 로그를 그대로 유지한다.
50. v0.5.10 조회 응답에서는 마켓별 시세 출처와 최신 거래시각을 목록 하단으로 모아 가독성을 높이며 기존 API/명령/로그·DB/숫자 선택·AI OFF를 유지한다.

51. v0.5.10 미국 시세 백업 조회(나스닥 확정 일봉·네이버 해외 일봉)는 market.py만 확장하며 기존 기능/명령/SQLite/로그/UI/배터리를 보존한다.
52. 주식 목록 응답은 그룹 번호 선택 세션을 활성화하고 기존 선택/시세/인증/로그 흐름을 그대로 재사용한다.
44. 주식 선택 0은 현재 화면의 이전 메뉴를 열고 기존 인증·로그·5분 세션을 보존한다.
45. 그룹 시세 화면의 진입 출처를 유지해 메인 메뉴/관심그룹 목록 중 올바른 이전 화면으로 돌아간다.
"""
from __future__ import annotations

import hmac
import os
import sqlite3
import time
from pathlib import Path
from contextlib import closing
from threading import RLock
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from .commands import CommandError, execute_command
from .ai_engine import AIError, AISettings, get_ai_reply
from .ops import details, command_stats, recent_errors, uptime_report
from .market import StockQuoteError, execute_stock_command, WATCHLIST
from .watchlists import (init_schema, is_group_quote_request, load_group, group_report,
                         execute_group_command, resolve_stock, resolve_saved_alias)
from .history import is_analysis_request, individual_report, group_report as history_group_report, fetch_history
from .selection_menu import StockSelectionMenus

VERSION = "0.5.10"
SUPPORTED = {"계산", "시간", "서버상태", "질문", "요약", "AI상태", "대화초기화", "상세상태", "통계", "최근오류", "가동시간", "주식", "메모리7"}


class CommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=8, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$")
    command: str = Field(min_length=1, max_length=24)
    argument: str = Field(default="", max_length=1000)
    room: str = Field(default="", max_length=100)
    sender: str = Field(default="", max_length=100)


def create_app(token: str | None = None, database_path: str | Path | None = None) -> FastAPI:
    secret = token if token is not None else os.environ.get("ANGAE_TOKEN", "")
    if len(secret) < 32:
        raise RuntimeError("ANGAE_TOKEN 환경 변수에 32자 이상 랜덤 토큰이 필요합니다.")
    path = Path(database_path or os.environ.get("ANGAE_DB", "data/angaebot_core.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = RLock()
    selection_menus = StockSelectionMenus()
    began = time.monotonic()

    def connect():
        connection = sqlite3.connect(str(path), timeout=5)
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    with closing(connect()) as db, db:
        db.execute("""CREATE TABLE IF NOT EXISTS jobs (
            request_id TEXT PRIMARY KEY, command TEXT NOT NULL, argument TEXT NOT NULL,
            room TEXT NOT NULL, sender TEXT NOT NULL, result TEXT NOT NULL,
            ok INTEGER NOT NULL, created_at INTEGER NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, event_time INTEGER NOT NULL,
            level TEXT NOT NULL, stage TEXT NOT NULL, detail TEXT NOT NULL)""")
        # 새 테이블만 추가. 기존 jobs/events와 이전 로그는 절대 변경하거나 삭제하지 않는다.
        db.execute("""CREATE TABLE IF NOT EXISTS ai_sessions (
            room TEXT NOT NULL, sender TEXT NOT NULL, generation INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(room, sender))""")
        db.execute("""CREATE TABLE IF NOT EXISTS ai_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT NOT NULL UNIQUE,
            room TEXT NOT NULL, sender TEXT NOT NULL, generation INTEGER NOT NULL,
            prompt TEXT NOT NULL, reply TEXT NOT NULL, created_at INTEGER NOT NULL)""")
        db.execute("""CREATE INDEX IF NOT EXISTS idx_ai_turn_context
            ON ai_turns(room, sender, generation, id)""")
        # v0.5.0: 관심종목 테이블만 추가. 기존 jobs/events/ai 데이터는 절대 변경하지 않는다.
        init_schema(db)

    api = FastAPI(title="AngaeBot Core", version=VERSION, docs_url=None, redoc_url=None, openapi_url=None)

    def authenticated(x_angaebot_token: Annotated[str | None, Header()] = None):
        if x_angaebot_token is None or not hmac.compare_digest(x_angaebot_token, secret):
            raise HTTPException(status_code=401, detail="인증 실패")

    @api.get("/v1/health", dependencies=[Depends(authenticated)])
    def health():
        return {"ok": True, "version": VERSION, "uptime_seconds": int(time.monotonic() - began)}

    @api.post("/v1/commands", dependencies=[Depends(authenticated)])
    def command(request: CommandRequest):
        if request.command not in SUPPORTED:
            raise HTTPException(status_code=400, detail="지원하지 않는 명령")
        # 외부 주식 시세는 DB의 쓰기 트랜잭션 밖에서 조회해 다른 명령 처리 지연을 막는다.
        # 중복 요청은 조회 전에 확인하고, 기록 시에는 아래의 기존 잠금으로 다시 검증한다.
        stock_reply = None
        stock_error = None
        stock_menu_active = False
        resolved_argument = request.argument
        selection_back = 'menu'
        if request.command in {"주식", "메모리7"}:
            with closing(connect()) as read_db:
                old = read_db.execute("SELECT command,argument,result,ok FROM jobs WHERE request_id=?", (request.request_id,)).fetchone()
            if old is not None:
                if old[0] != request.command or old[1] != request.argument:
                    raise HTTPException(status_code=409, detail="동일 요청 ID에 다른 명령을 사용할 수 없습니다.")
                return {"ok": bool(old[3]), "reply": old[2], "request_id": request.request_id, "duplicate": True}
            try:
                # 짧은 메뉴/번호 선택은 동일한 인증·dedup·jobs/events 흐름에서 먼저 해석한다.
                if request.command == "주식" and request.argument.strip() == "메뉴":
                    menu = selection_menus.open(request.room, request.sender)
                    stock_reply, stock_menu_active = menu.reply, menu.menu_active
                elif request.command == "주식" and request.argument.startswith("선택 "):
                    with closing(connect()) as read_db:
                        menu = selection_menus.choose(read_db, request.room, request.sender,
                                                      request.argument[3:].strip())
                    stock_reply, stock_menu_active = menu.reply or None, menu.menu_active
                    resolved_argument = menu.execute_argument
                    selection_back = menu.back
                # 이미 검증된 메모리7을 그대로 유지하면서, 사용자 그룹 조회만 새 경로로 분리한다.
                if stock_reply is not None:
                    pass
                elif request.command == "메모리7" or (request.command == "주식" and resolved_argument.strip() == "메모리7"):
                    stock_reply = execute_stock_command(request.command, resolved_argument)
                    # 기존 메모리7 8개 줄과 같은 순서로 숫자 선택 -> 종목 분석을 연결.
                    if request.room.strip() and request.sender.strip():
                        selection_menus.open_quotes(request.room, request.sender, WATCHLIST)
                        stock_menu_active = True
                elif request.command == "주식" and is_analysis_request(resolved_argument):
                    parts = resolved_argument.split()
                    if len(parts) < 2:
                        raise StockQuoteError("사용법: 앙개야 주식 분석 마이크론 (또는 삼성전자/하이닉스/그룹명)")
                    target = ' '.join(parts[1:])
                    if target == "메모리7":
                        stock_reply = history_group_report("메모리7", WATCHLIST)
                    else:
                        # 그룹의 room/sender 소유권을 검사하고, 없는 그룹명만 안전한 종목 티커로 판정.
                        with closing(connect()) as read_db:
                            belongs = read_db.execute(
                                "SELECT 1 FROM stock_groups WHERE room=? AND sender=? AND name=?",
                                (request.room, request.sender, target)).fetchone()
                            stocks = load_group(read_db, request.room, request.sender, target) if belongs else None
                        if stocks is not None:
                            stock_reply = history_group_report(target, stocks)
                        else:
                            try:
                                stock = resolve_stock(target)
                            except StockQuoteError as invalid_name:
                                with closing(connect()) as read_db:
                                    stock = resolve_saved_alias(read_db, request.room, request.sender, target)
                                if stock is None:
                                    raise invalid_name
                            stock_reply = individual_report(fetch_history(stock))
                elif request.command == "주식" and is_group_quote_request(resolved_argument):
                    with closing(connect()) as read_db:
                        stocks = load_group(read_db, request.room, request.sender, resolved_argument.strip())
                    stock_reply = group_report(resolved_argument.strip(), stocks)
                    # 방/발신자에 실제 등록된 그룹 종목만 원래 출력 순서대로 선택 가능.
                    if stocks:
                        selection_menus.open_quotes(request.room, request.sender, stocks,
                            back=selection_back)
                        stock_menu_active = True
            except StockQuoteError as error:
                stock_error = error
        with lock:
            with closing(connect()) as db, db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT command, argument, result, ok FROM jobs WHERE request_id=?", (request.request_id,)).fetchone()
                if row:
                    if row[0] != request.command or row[1] != request.argument:
                        raise HTTPException(status_code=409, detail="동일 요청 ID에 다른 명령을 사용할 수 없습니다.")
                    return {"ok": bool(row[3]), "reply": row[2], "request_id": request.request_id, "duplicate": True}
                try:
                    if request.command in {"주식", "메모리7"}:
                        if stock_error is not None:
                            raise stock_error
                        if stock_reply is not None:
                            reply = stock_reply
                        elif request.command == "주식":
                            reply = execute_group_command(db, request.room, request.sender, resolved_argument)
                            if resolved_argument.strip() == '목록':
                                selection_menus.open_groups(db, request.room, request.sender)
                                stock_menu_active = True
                        else:
                            # 메모리7에 잘못된 인수가 있으면 기존 사용법 오류를 그대로 반환한다.
                            reply = execute_stock_command(request.command, request.argument)
                    elif request.command == "상세상태":
                        reply = details(int(time.monotonic() - began))
                    elif request.command == "통계":
                        reply = command_stats(db, request.room, request.sender)
                    elif request.command == "최근오류":
                        reply = recent_errors(db, request.room, request.sender)
                    elif request.command == "가동시간":
                        reply = uptime_report(int(time.monotonic() - began))
                    elif request.command == "AI상태":
                        reply = AISettings.from_env().status_text()
                    elif request.command == "대화초기화":
                        db.execute("""INSERT INTO ai_sessions(room,sender,generation)
                            VALUES (?,?,1) ON CONFLICT(room,sender)
                            DO UPDATE SET generation = generation + 1""", (request.room, request.sender))
                        reply = "🧠 AI 대화 문맥 초기화 완료"
                    elif request.command in {"질문", "요약"}:
                        settings = AISettings.from_env()
                        gen_row = db.execute("SELECT generation FROM ai_sessions WHERE room=? AND sender=?",
                                             (request.room, request.sender)).fetchone()
                        generation = gen_row[0] if gen_row else 0
                        history = []
                        if settings.memory_enabled and settings.context_turns > 0 and request.command == "질문":
                            history = db.execute("""SELECT prompt,reply FROM ai_turns
                                WHERE room=? AND sender=? AND generation=?
                                ORDER BY id DESC LIMIT ?""",
                                (request.room, request.sender, generation, settings.context_turns)).fetchall()
                            history = list(reversed(history))
                        reply = get_ai_reply(settings, request.argument,
                                             history=history, summarize=request.command == "요약")
                        if settings.memory_enabled and request.command == "질문":
                            db.execute("""INSERT INTO ai_turns
                                (request_id,room,sender,generation,prompt,reply,created_at)
                                VALUES (?,?,?,?,?,?,?)""",
                                (request.request_id, request.room, request.sender, generation,
                                 request.argument, reply, int(time.time())))
                    else:
                        reply = execute_command(request.command, request.argument, int(time.monotonic() - began))
                    ok = True
                except (CommandError, AIError, StockQuoteError) as error:
                    reply = "⚠️ " + str(error)
                    ok = False
                now = int(time.time())
                db.execute("""INSERT INTO jobs(request_id,command,argument,room,sender,result,ok,created_at)
                              VALUES (?,?,?,?,?,?,?,?)""", (request.request_id, request.command, request.argument,
                                                     request.room, request.sender, reply, int(ok), now))
                db.execute("INSERT INTO events(event_time,level,stage,detail) VALUES (?,?,?,?)",
                           (now, "INFO" if ok else "WARN", "COMMAND_DONE" if ok else "COMMAND_REJECTED",
                            f"request_id={request.request_id} command={request.command} ok={ok}"))
        return {"ok": ok, "reply": reply, "request_id": request.request_id, "duplicate": False,
                "menu_active": stock_menu_active if ok else False}

    return api


# Production entry point; secret must be configured before starting uvicorn.
app = create_app()
