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
53. 통합 메뉴 명령은 기존 인증 FastAPI/SQLite 요청 중복 방지/작업·이벤트 로그를 그대로 사용한다.
54. 홈/주식/배드민턴/요리/여행/종친/영어 메뉴와 0 이전·00 홈을 주식 기존 선택 상태에서 통합 관리한다.
55. 홈에서 기존 주식 시세·분석을 선택하면 기존 stock/history/watchlists 모듈로 전달하며 DB·AI/Android 로그는 보존한다.
56. 미개발 콘텐츠 기능은 안내만 제공하며 외부 AI 호출/파일 변경/개인정보 조회를 실행하지 않는다.
57. v0.6.0 홈 6번은 날씨로, 7번은 읽기 전용 설정·운영 메뉴로 대체/추가한다.
58. 현재 Core 상태/배포 정보/설정 요약/현재 방·발신자의 명령 로그만 조회하며 민감 정보는 노출하지 않는다.
59. '메뉴 경로 주식 2 2' 등 연속 번호 메뉴 점프는 최종 항목만 실행해 불필요한 외부 시세 호출을 방지한다.
60. 각 메뉴 점프는 최대 5개 정확한 숫자로 제한하며 기존 인증·중복 요청·jobs/events 로깅·TTL 보호를 재사용한다.
61. 기존 주식 분석/관심목록/AI/설정/배터리/Android UI/DB 스키마 및 기존 명령은 제거하지 않는다.
62. v0.6.1 인증 Core health에는 실제 S20+ 배포 기록의 branch/sha를 선택 필드로 제공한다.
63. 모든 명령 응답에 module_source를 덧붙여 Android가 담당 소스 모듈을 공통 하단에 표기하도록 한다.
64. 신규 메타 필드는 기존 reply/menu_active/duplicate/request_id·jobs/events·API 호환을 보존한다.
65. 배포기록이 없으면 빈 값을 반환하며 main이라고 추측하거나 GitHub에 외부 요청하지 않는다.
66. 설정 7번 전체 메뉴 트리 조회를 기존 인증/중복방지/메뉴 활성화/작업·이벤트 로그 경로에 연결한다.
67. 메뉴 트리 렌더링은 selection_menu.py의 공통 선택지 정의를 사용하며 DB 스키마/UI/명령을 변경하지 않는다.
68. v0.6.2 설정 8번 간결 도움말 및 설정 1번 통합 상태를 제공하고 기존 설정 번호/로그를 유지한다.
69. 운영 상태는 Core·감시·SSH·가동시간·배포정보를 읽기 전용으로 표시하며 기존 상세상태 명령도 보존한다.
70. 카카오톡 사용자 명령만 비활성화하므로 계산/AI 레거시 내부 API·DB/사용자 로그는 호환성을 유지한다.
71. v0.7.0 개인 기록: 인증된 방·발신자별 부동산/금융·투자/개인 메모·일정 별도 SQLite 테이블을 생성한다.
72. 메모·일정의 등록/수정/삭제는 기존 jobs/events 단일 트랜잭션·request_id 중복방지를 재사용한다.
73. 목록·검색·상세보기 번호는 5분 메뉴의 기존 인증·0/00 경로를 재사용하며 카톡 수동 입력만 지원한다.
74. Samsung Notes 자동 연동·민감정보 암호화·알림 예약은 구현하지 않고 사용자가 중요 메모만 입력하도록 한다.
75. v0.7.1 요청한 홈 1~10 재배치·금/개 단축과 도움말/트리 번호를 반영하며 기존 기능·로그·DB 스키마를 유지한다.
44. 주식 선택 0은 현재 화면의 이전 메뉴를 열고 기존 인증·로그·5분 세션을 보존한다.
45. 그룹 시세 화면의 진입 출처를 유지해 메인 메뉴/관심그룹 목록 중 올바른 이전 화면으로 돌아간다.
76. 날씨 오늘·내일·주간 실시간 조회는 기존 인증/중복검사 이후 DB 쓰기 잠금 밖에서 실행한다.
77. 날씨 지역 설정만 별도 weather_locations 테이블에 저장하고 기존 jobs/events 로그를 그대로 남긴다.
78. 날씨 단축/하위 메뉴 응답의 5분 번호 세션과 전용 기능 모듈 정보를 기존 Android Bridge에 전달한다.
79. 공급자 장애 및 잘못된 지역은 기존 COMMAND_REJECTED와 경고 응답으로 기록하며 가짜 예보를 출력하지 않는다.
80. 부동산 실거래가: 서울 구·법정동 5자리 매매/전세/월세 조회를 국토부 XML API로 지원한다.
81. '부 지역 강남구' 조회 지역은 별도 SQLite 테이블에 보존하고 기존 부동산 개인메모 CRUD는 유지한다.
82. 메뉴 2→3/4/5 실거래 조회와 단축어 부 매매/전세/월세/시세는 DB 쓰기 락 밖에서 수행한다.
83. API 키 미설정·연결 장애·취소 계약은 보수적으로 처리하며 기존 인증·중복 방지·jobs/events 로그·module_source를 보존한다.
84. Android UI/배터리·주식/날씨/AI 및 기존 SQLite 테이블은 수정/초기화하지 않는다.
85. 주식 메뉴 7번 상세보기는 제거하고 메모리7과 모든 그룹의 상세보기는 시세표 99를 통해 기존 인증·로그 경로로 실행한다.
86. 기본 메모리7과 사용자 그룹은 한 종목 한 줄로 표기하고 상세는 원본 시세/장외/출처를 별도 표기하지만 DB와 선택 세션 구조는 유지한다.
87. 메모리7 및 모든 그룹 간략 화면의 99번 상세보기와 상세 화면 99번 간략보기는 기존 메뉴 choose 경로로 전환한다.
88. 메모리7의 기존 1~8 분석과 5분 선택 권한·중복방지·jobs/events 로그·모듈명·배터리 표시를 보존한다.
89. 메모리7 이외의 관심그룹 1~10 번호와 주식 메인 메뉴 번호는 변경하지 않는다.
90. 메뉴 숫자 0은 직전 화면 상태를 선택기에서 복원하고 메모리7 상세→간략, 분석/설정/날씨/기록/그룹의 상위 이동을 유지한다.
91. 복원된 시세는 기존 시세 조회 함수로 출력만 재생성하며 선택기 화면 스냅샷을 덮어쓰지 않아 연속 0으로 단계별 복귀할 수 있다.
92. 메뉴 선택 00 홈/5분 만료·방/발신자 격리·중복요청·DB 락 외부 시세 조회·로그·Android 출력 기능을 그대로 유지한다.
93. 메뉴에서 1~8번 종목 분석을 선택한 결과 화면도 0을 눌러 이전 시세/분석 메뉴로 복귀하며 00으로 홈으로 돌아간다.
94. 부동산 실거래 조회·지역 안내 역시 메뉴 선택 시 직전 부동산 메뉴를 보관하여 0으로 복귀하고 별도의 DB/로그를 추가하지 않는다.
95. 메모리7 및 모든 사용자 관심그룹(반도체·미국시총10 포함)은 기존 짧은 시세 화면을 기본으로 하고 99번 선택에 한해 현재 그룹의 상세 출처·장외 체결·정규 종가를 재조회한다.
96. 주식 메뉴의 기존 1~6번을 보존하고 전용 메모리7 상세 7번을 제거하며 99/0/00 선택은 공통 메뉴 상태·로그에서 처리한다.
97. 99 그룹 상세는 이전 화면이 동일 그룹 시세표일 때만 실행하고 개인 그룹 소유자·조회 권한을 다시 확인하며 DB/인증/Android 하단 정보는 보존한다.
98. 주식 메뉴 7 AI 주도주(13), 8 반도체 및 기자재(19), 9 데센 및 네트워크(5) 고정 읽기 전용 섹터 시세를 제공하며 1~6 기능·위치를 유지한다.
99. 섹터당 최대 10개 종목을 한 화면에 조회해 카카오톡 전체보기 문제를 줄이고 97 이전 페이지/98 다음 페이지/99 상세를 기존 숫자 메뉴로 처리한다.
100. 섹터 1~10 종목 분석은 현재 페이지의 실제 티커에 연결하고 0은 이전 시세/페이지, 00은 홈으로 이동하며 5분·인증·jobs/events·배터리/Android 표시를 유지한다.
101. 섹터는 기존 SQLite stock_groups 및 사용자별 관심그룹 CRUD와 무관한 읽기 전용 목록이며 외부 가격은 각 시세 조회 시 검증된 공급자에서만 가져온다.
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
from .ops import (details, command_stats, recent_errors, uptime_report,
                  deployment_report, recent_command_log, configuration_report, deployment_identity,
                  unified_status)
from .module_info import module_for
from .market import StockQuoteError, execute_stock_command, WATCHLIST
from .watchlists import (init_schema, is_group_quote_request, load_group, group_report,
                         execute_group_command, resolve_stock, resolve_saved_alias)
from .history import is_analysis_request, individual_report, group_report as history_group_report, fetch_history
from .sector_watchlists import parse_sector_request, get_page as get_sector_page, sector_report
from .selection_menu import StockSelectionMenus, CONTENT_ITEMS
from .personal_records import (PERSONAL_COMMANDS, CATEGORIES as PERSONAL_SECTORS,
                               RecordError, init_records_schema, execute_record_command)
from .weather import (WeatherError, init_weather_schema, get_location, resolve_location,
                      save_location, forecast_text, location_help)
from .real_estate import (RealEstateError, init_real_estate_schema, resolve_district,
                          save_district, parse_transaction_query, region_help,
                          transaction_report)

VERSION = "0.7.3"
SUPPORTED = {"계산", "시간", "서버상태", "질문", "요약", "AI상태", "대화초기화", "상세상태", "통계", "최근오류", "가동시간", "주식", "메모리7", "메뉴", "날씨", "실거래"} | PERSONAL_COMMANDS


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
        # 독립 메모/일정 테이블만 새로 생성. 기존 주식/AI/이벤트 테이블에는 변경 없음.
        init_records_schema(db)
        init_weather_schema(db)
        init_real_estate_schema(db)

    api = FastAPI(title="AngaeBot Core", version=VERSION, docs_url=None, redoc_url=None, openapi_url=None)

    def authenticated(x_angaebot_token: Annotated[str | None, Header()] = None):
        if x_angaebot_token is None or not hmac.compare_digest(x_angaebot_token, secret):
            raise HTTPException(status_code=401, detail="인증 실패")

    @api.get("/v1/health", dependencies=[Depends(authenticated)])
    def health():
        revision = deployment_identity()
        return {"ok": True, "version": VERSION, "uptime_seconds": int(time.monotonic() - began),
                "deployment_branch": revision["branch"], "deployment_sha": revision["sha"]}

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
        selection_previous = None
        selection_restored = False
        weather_update = None
        estate_update = None
        estate_request = (request.command == "실거래" or
                          (request.command == "부동산" and
                           request.argument.strip().split(" ", 1)[0] in
                           {"지역", "시세", "매매", "전세", "월세", "실거래"}))
        if request.command in {"주식", "메모리7", "메뉴", "날씨", "실거래"} or estate_request:
            with closing(connect()) as read_db:
                old = read_db.execute("SELECT command,argument,result,ok FROM jobs WHERE request_id=?", (request.request_id,)).fetchone()
            if old is not None:
                if old[0] != request.command or old[1] != request.argument:
                    raise HTTPException(status_code=409, detail="동일 요청 ID에 다른 명령을 사용할 수 없습니다.")
                return {"ok": bool(old[3]), "reply": old[2], "request_id": request.request_id,
                        "duplicate": True,
                        "module_source": module_for(request.command, request.argument, old[2])}
            try:
                # 메뉴도 주식과 동일한 인증·중복 요청·jobs/events 로그 경로를 통과한다.
                if estate_request:
                    action = " ".join(request.argument.split())
                    if action.startswith("지역 "):
                        estate_update = resolve_district(action[3:].strip())
                    elif action in {"", "지역", "도움말", "실거래", "메뉴"}:
                        with closing(connect()) as read_db:
                            stock_reply = region_help(read_db, request.room, request.sender)
                        selection_menus.open_record_sector(request.room, request.sender, "부동산")
                        stock_menu_active = True
                    else:
                        with closing(connect()) as read_db:
                            kind, district, apartment = parse_transaction_query(
                                read_db, request.room, request.sender, action)
                        stock_reply = transaction_report(kind, district, apartment)
                        selection_menus.open_record_sector(request.room, request.sender, "부동산")
                        stock_reply += "\n※ 부 3~5 재조회 · 0 이전 · 00 홈"
                        stock_menu_active = True
                if request.command == "날씨":
                    action = request.argument.strip()
                    if action in ("", "메뉴"):
                        menu = selection_menus.open_category(request.room, request.sender, "날씨")
                        stock_reply, stock_menu_active = menu.reply, menu.menu_active
                    elif action.startswith("지역 "):
                        weather_update = resolve_location(action[3:].strip())
                    elif action in {"오늘", "내일", "주간"}:
                        resolved_argument = "날씨조회 " + action
                    elif action == "지역":
                        resolved_argument = "날씨설정 안내"
                    else:
                        raise WeatherError("사용법: 날 / 날 1~4 / 날 지역 서울 / 앙개야 날씨 오늘")
                if request.command == "메뉴":
                    action = request.argument.strip()
                    if action in ("", "홈"):
                        menu = selection_menus.open_home(request.room, request.sender)
                    elif action == "주식":
                        menu = selection_menus.open(request.room, request.sender, back='home')
                    elif action in CONTENT_ITEMS:
                        menu = selection_menus.open_category(request.room, request.sender, action)
                    elif action in PERSONAL_SECTORS:
                        menu = selection_menus.open_record_sector(request.room, request.sender, action)
                    elif action == "설정":
                        menu = selection_menus.open_settings(request.room, request.sender)
                    elif action.startswith("경로 "):
                        parts = action.split()
                        if len(parts) < 3:
                            raise StockQuoteError("메뉴 점프 사용법: 주 2 2 / 앙 1 2 / 설 3")
                        with closing(connect()) as read_db:
                            menu = selection_menus.navigate_path(read_db, request.room, request.sender,
                                                               parts[1], tuple(parts[2:]))
                    elif action.startswith("선택 "):
                        with closing(connect()) as read_db:
                            menu = selection_menus.choose(read_db, request.room, request.sender,
                                                          action[3:].strip())
                    else:
                        raise StockQuoteError("메뉴 사용법: 앙/주/부/금/개/여/민/요/종/날/설 또는 번호 선택")
                    stock_reply, stock_menu_active = menu.reply or None, menu.menu_active
                    resolved_argument = menu.execute_argument
                    selection_back = menu.back
                    selection_previous = menu.previous
                    selection_restored = menu.restored
                elif request.command == "주식" and request.argument.strip() == "메뉴":
                    menu = selection_menus.open(request.room, request.sender, back='home')
                    stock_reply, stock_menu_active = menu.reply, menu.menu_active
                elif request.command == "주식" and request.argument.startswith("선택 "):
                    with closing(connect()) as read_db:
                        menu = selection_menus.choose(read_db, request.room, request.sender,
                                                      request.argument[3:].strip())
                    stock_reply, stock_menu_active = menu.reply or None, menu.menu_active
                    resolved_argument = menu.execute_argument
                    selection_back = menu.back
                    selection_previous = menu.previous
                    selection_restored = menu.restored
                # 이미 검증된 메모리7을 그대로 유지하면서, 사용자 그룹 조회만 새 경로로 분리한다.
                if stock_reply is not None or weather_update is not None or estate_update is not None:
                    pass
                elif request.command == "메뉴" and resolved_argument.startswith("실거래조회 "):
                    with closing(connect()) as read_db:
                        kind, district, apartment = parse_transaction_query(
                            read_db, request.room, request.sender, resolved_argument)
                    stock_reply = transaction_report(kind, district, apartment)
                    selection_menus.open_record_sector(request.room, request.sender, "부동산",
                                                      previous=selection_previous)
                    stock_reply += "\n※ 부 3~5 재조회 · 0 이전 · 00 홈"
                    stock_menu_active = True
                elif request.command == "메뉴" and resolved_argument == "실거래설정 안내":
                    with closing(connect()) as read_db:
                        stock_reply = region_help(read_db, request.room, request.sender)
                    selection_menus.open_record_sector(request.room, request.sender, "부동산",
                                                      previous=selection_previous)
                    stock_menu_active = True
                elif request.command in {"메뉴", "날씨"} and resolved_argument.startswith("날씨조회 "):
                    with closing(connect()) as read_db:
                        location = get_location(read_db, request.room, request.sender)
                    stock_reply = forecast_text(location, resolved_argument.split(" ", 1)[1])
                    # 일회성 조회 이후에도 기존 5분 메뉴/0/00 사용을 유지한다.
                    if not selection_restored:
                        selection_menus.open_category(request.room, request.sender, "날씨",
                                                      previous=selection_previous)
                    stock_reply += "\n※ 날 1~4 다른 조회 · 0 이전 · 00 홈"
                    stock_menu_active = True
                elif request.command in {"메뉴", "날씨"} and resolved_argument == "날씨설정 안내":
                    with closing(connect()) as read_db:
                        stock_reply = location_help(read_db, request.room, request.sender)
                    if not selection_restored:
                        selection_menus.open_category(request.room, request.sender, "날씨",
                                                      previous=selection_previous)
                    stock_menu_active = True
                elif request.command == "메뉴" and resolved_argument.startswith("설정보기 "):
                    view = resolved_argument.split(" ", 1)[1]
                    if view == "status":
                        report = unified_status(int(time.monotonic() - began), VERSION)
                    elif view == "deployment":
                        report = deployment_report(VERSION)
                    elif view == "configuration":
                        report = configuration_report(AISettings.from_env().status_text())
                    elif view == "tree":
                        report = selection_menus.menu_tree()
                    elif view == "help":
                        report = selection_menus.help_report()
                    elif view in {"logs", "stats", "errors"}:
                        with closing(connect()) as read_db:
                            if view == "logs":
                                report = recent_command_log(read_db, request.room, request.sender)
                            elif view == "stats":
                                report = command_stats(read_db, request.room, request.sender)
                            else:
                                report = recent_errors(read_db, request.room, request.sender)
                    else:
                        raise StockQuoteError("등록되지 않은 설정 메뉴 항목입니다.")
                    refreshed = selection_menus.open_settings(request.room, request.sender,
                                                              previous=selection_previous)
                    # 상태/도움말은 긴 설정 목록을 중복 출력하지 않지만 번호 선택 세션은 유지한다.
                    if view in {"status", "help"}:
                        stock_reply = report + "\n※ 설정 1~8 다른 항목 선택 · 0/00 홈"
                    else:
                        stock_reply = report + "\n\n" + refreshed.reply
                    stock_menu_active = True
                elif request.command == "메모리7" or (request.command in {"주식", "메뉴"} and resolved_argument.strip() in {"메모리7", "메모리7 상세", "상세"}):
                    stock_reply = execute_stock_command("주식" if request.command == "메뉴" else request.command, resolved_argument)
                    # 기존 메모리7 8개 줄과 같은 순서로 숫자 선택 -> 종목 분석을 연결.
                    if request.room.strip() and request.sender.strip():
                        mode = resolved_argument.strip()
                        detail_view = mode in ('메모리7 상세', '상세')
                        if not selection_restored:
                            selection_menus.open_quotes(request.room, request.sender, WATCHLIST,
                                                        back=selection_back,
                                                        memory7_view='detail' if detail_view else 'compact',
                                                        previous=selection_previous)
                        stock_menu_active = True
                elif request.command in {"주식", "메뉴"} and is_analysis_request(resolved_argument):
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
                    # 이전 번호 선택의 시세/분석 목록을 0으로 복원. 본문/가격은 저장하지 않는다.
                    if selection_menus.open_readonly_result(
                            request.room, request.sender, previous=selection_previous):
                        # 종목 분석 본문과 기존 UI 문자열을 변경하지 않고 0/00 선택만 활성화한다.
                        stock_menu_active = True
                elif request.command in {"주식", "메뉴"} and resolved_argument.startswith('섹터시세'):
                    # 고정 섹터는 운영 DB에 저장하지 않고 허용된 키·페이지·보기 모드만 검증한다.
                    request_sector = parse_sector_request(resolved_argument)
                    if request_sector is None:
                        raise StockQuoteError('섹터 시세 명령을 확인하세요.')
                    key_name, page, detailed = request_sector
                    stocks = get_sector_page(key_name, page)
                    stock_reply = sector_report(key_name, page, detailed=detailed)
                    if not selection_restored:
                        selection_menus.open_sector_quotes(
                            request.room, request.sender, key_name, page, detailed,
                            back=selection_back, previous=selection_previous)
                    stock_menu_active = True
                elif request.command in {"주식", "메뉴"} and resolved_argument.startswith('상세시세 '):
                    # 사용자 그룹의 실제 시세표에서 99를 입력한 경우에만 상세조회 허용.
                    if not selection_restored and not (selection_previous is not None and
                             selection_previous.origin.startswith('quotes:group:')):
                        raise StockQuoteError('상세 시세는 관심그룹 간략 화면에서 99를 입력하세요.')
                    group_name = resolved_argument.split(' ', 1)[1].strip()
                    with closing(connect()) as read_db:
                        stocks = load_group(read_db, request.room, request.sender, group_name)
                    stock_reply = group_report(group_name, stocks, detailed=True)
                    if stocks:
                        if not selection_restored:
                            selection_menus.open_quotes(
                                request.room, request.sender, stocks,
                                back=selection_back, previous=selection_previous,
                                group_name=group_name, group_view='detail')
                        stock_menu_active = True
                elif request.command in {"주식", "메뉴"} and is_group_quote_request(resolved_argument):
                    with closing(connect()) as read_db:
                        stocks = load_group(read_db, request.room, request.sender, resolved_argument.strip())
                    stock_reply = group_report(resolved_argument.strip(), stocks)
                    # 방/발신자에 실제 등록된 그룹 종목만 원래 출력 순서대로 선택 가능.
                    if stocks:
                        if not selection_restored:
                            selection_menus.open_quotes(request.room, request.sender, stocks,
                                back=selection_back, previous=selection_previous,
                                group_name=resolved_argument.strip())
                        stock_menu_active = True
            except (StockQuoteError, RecordError, WeatherError, RealEstateError) as error:
                stock_error = error
        with lock:
            with closing(connect()) as db, db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT command, argument, result, ok FROM jobs WHERE request_id=?", (request.request_id,)).fetchone()
                if row:
                    if row[0] != request.command or row[1] != request.argument:
                        raise HTTPException(status_code=409, detail="동일 요청 ID에 다른 명령을 사용할 수 없습니다.")
                    return {"ok": bool(row[3]), "reply": row[2], "request_id": request.request_id,
                            "duplicate": True,
                            "module_source": module_for(request.command, request.argument, row[2])}
                try:
                    if request.command in {"주식", "메모리7", "메뉴", "날씨", "실거래"} or estate_request:
                        if stock_error is not None:
                            raise stock_error
                        if estate_update is not None:
                            save_district(db, request.room, request.sender, estate_update)
                            selection_menus.open_record_sector(request.room, request.sender, "부동산")
                            stock_menu_active = True
                            reply = (f"✅ 부동산 조회 지역: {estate_update.name} ({estate_update.code})"
                                     "\n※ 부 3~5 실거래 조회 · 0 이전 · 00 홈")
                        elif weather_update is not None:
                            save_location(db, request.room, request.sender, weather_update)
                            selection_menus.open_category(request.room, request.sender, "날씨")
                            stock_menu_active = True
                            reply = (f"✅ 날씨 지역 설정 완료: {weather_update.name}"
                                     "\n※ 날 1~4 조회 · 0 이전 · 00 홈")
                        elif stock_reply is not None:
                            reply = stock_reply
                        elif request.command in {"주식", "메뉴"}:
                            reply = execute_group_command(db, request.room, request.sender, resolved_argument)
                            if resolved_argument.strip() == '목록':
                                selection_menus.open_groups(db, request.room, request.sender,
                                                            previous=selection_previous)
                                stock_menu_active = True
                        else:
                            # 메모리7에 잘못된 인수가 있으면 기존 사용법 오류를 그대로 반환한다.
                            reply = execute_stock_command(request.command, request.argument)
                    elif request.command in PERSONAL_COMMANDS:
                        result = execute_record_command(db, request.room, request.sender,
                                                        request.command, request.argument)
                        if result.rows is not None:
                            menu = selection_menus.open_record_results(
                                request.room, request.sender, result.rows,
                                sector=result.sector, heading=result.reply.replace('🗂 ', ''))
                            reply = menu.reply
                            stock_menu_active = menu.menu_active
                        else:
                            reply = result.reply
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
                except (CommandError, AIError, StockQuoteError, RecordError, WeatherError, RealEstateError) as error:
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
                "menu_active": stock_menu_active if ok else False,
                "module_source": module_for(request.command, resolved_argument, reply)}

    return api


# Production entry point; secret must be configured before starting uvicorn.
app = create_app()
