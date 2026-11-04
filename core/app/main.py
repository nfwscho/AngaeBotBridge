"""
앙개봇 v0.2.0 FastAPI 서버 — 전체 기능 상세 안내
1. S20+ 내부 loopback(127.0.0.1:8765)에서만 구동되도록 시작 스크립트가 제한한다.
2. 모든 HTTP 엔드포인트에 X-AngaeBot-Token 인증을 요구하고 compare_digest로 검사한다.
3. GET /v1/health: 인증 후 Python 엔진의 버전/상태를 간단히 반환한다.
4. POST /v1/commands: 요청 ID로 중복 실행을 막고 허용 명령만 실행한다.
5. SQLite jobs, events 테이블에 명령 수신/결과/실패를 저장하며 자동 로그 삭제하지 않는다.
6. 임의 셸 명령, 파일 조작, 외부 PC 원격 작업을 수행하지 않는다.
7. 토큰은 환경 변수에서만 읽고 DB, 응답, 로그에 기록하지 않는다.
8. 기존 Android의 카톡 수신/RemoteInput/허용 채팅방/로그/UI 동작을 수정하지 않는다.
9. create_app() 주입 방식으로 API 단위 테스트 가능; 중복 요청은 저장된 응답을 돌려준다.
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

VERSION = "0.2.0"
SUPPORTED = {"계산", "시간", "서버상태"}


class CommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=8, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$")
    command: str = Field(min_length=1, max_length=24)
    argument: str = Field(default="", max_length=160)
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
        with lock:
            with closing(connect()) as db, db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT command, argument, result, ok FROM jobs WHERE request_id=?", (request.request_id,)).fetchone()
                if row:
                    if row[0] != request.command or row[1] != request.argument:
                        raise HTTPException(status_code=409, detail="동일 요청 ID에 다른 명령을 사용할 수 없습니다.")
                    return {"ok": bool(row[3]), "reply": row[2], "request_id": request.request_id, "duplicate": True}
                try:
                    reply = execute_command(request.command, request.argument, int(time.monotonic() - began))
                    ok = True
                except CommandError as error:
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
