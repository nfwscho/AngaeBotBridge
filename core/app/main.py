"""
앙개봇 Python Core v0.4.1 FastAPI 서버 — 전체 구현 기능 상세 설명
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
from .market import StockQuoteError, execute_stock_command

VERSION = "0.4.1"
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
        if request.command in {"주식", "메모리7"}:
            with closing(connect()) as read_db:
                old = read_db.execute("SELECT command,argument,result,ok FROM jobs WHERE request_id=?", (request.request_id,)).fetchone()
            if old is not None:
                if old[0] != request.command or old[1] != request.argument:
                    raise HTTPException(status_code=409, detail="동일 요청 ID에 다른 명령을 사용할 수 없습니다.")
                return {"ok": bool(old[3]), "reply": old[2], "request_id": request.request_id, "duplicate": True}
            try:
                stock_reply = execute_stock_command(request.command, request.argument)
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
                        reply = stock_reply
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
                        reply = "🧠 이 대화의 이전 AI 문맥을 초기화했습니다. (기존 로그는 보존됩니다.)"
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
        return {"ok": ok, "reply": reply, "request_id": request.request_id, "duplicate": False}

    return api


# Production entry point; secret must be configured before starting uvicorn.
app = create_app()
