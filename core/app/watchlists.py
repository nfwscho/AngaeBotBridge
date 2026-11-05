"""
앙개봇 Python Core v0.5.2 관심종목 그룹 관리 모듈 — 전체 기능 상세 설명
1. 기존 고정 '주식 메모리7' 8종목, 가격·등락률·시장별 거래일·캐시·원본 로그는 그대로 둔다.
2. '주식 목록', '주식 그룹생성 그룹명', '주식 그룹삭제 그룹명 확인' 명령을 추가한다.
3. '주식 추가 그룹명 티커 [별칭]', '주식 삭제 그룹명 티커', '주식 그룹명'을 추가한다.
4. 그룹과 종목은 room/sender별 SQLite의 신규 stock_groups/stock_items 테이블에만 저장한다.
5. 기존 jobs/events/AI 테이블, 인증 토큰, Android 설정 및 운영 로그는 변경하거나 삭제하지 않는다.
6. 메모리7은 읽기 전용으로 보호하며 그룹 최대 10개, 그룹당 종목 최대 10개로 제한한다.
7. 삼성·하이닉스 등 기존 8종목 이름·코드와 안전한 미국/한국/일본 종목코드를 입력할 수 있다.
8. 티커는 엄격히 검증·정규화하고 사용자 입력 URL/호스트/셸 명령을 실행하지 않는다.
9. 실제 시세는 기존 market.fetch_quote를 재사용하고 공급자 실패 시 '조회 불가'로 정확히 표시한다.
10. 미국·한국·일본의 현지 통화/최근 거래일을 표시하며 가격을 추측하거나 임의 보충하지 않는다.
11. 읽기 조회는 SQLite 쓰기 트랜잭션 밖에서 실행할 수 있도록 목록 스냅샷과 시세 조회를 분리한다.
12. 명령 중복 기록·요청 ID 충돌·인증·유저별 접근제한은 기존 FastAPI main이 처리한다.
13. 관리자/다른 채팅방에 종목정보가 혼합되지 않게 빈 scope는 거부한다.
14. 주식 자동매매/예약발송/유료 API/AI 호출은 지원하지 않으며 비공식 시세임을 명시한다.
15. 단위 테스트에서 독립 DB와 네트워크 모의 응답을 사용하도록 fetcher를 주입할 수 있다.
16. v0.5.1 '주식 프리셋 미국시총10'을 추가해 미국 기업 시가총액 상위 10개를 한 번에 등록한다.
17. 프리셋은 2026-11-04 공개 순위를 바탕으로 한 고정 스냅샷이며 자동 순위 재편성이나 매수·매도를 하지 않는다.
18. Alphabet 복수 종류 주식은 한 기업으로 묶고, 미국 국적 기업만 포함하며 해외 발행사의 미국 ADR은 제외한다.
19. 이미 존재하는 그룹·종목을 덮어쓰지 않고 기존 메모리7 및 다른 사용자 그룹·SQLite·로그를 모두 보존한다.
20. 10개 종목 가격은 기존 무료 공급자로 병렬 조회하고 요청 시간 제한 내에 답장을 반환하도록 동시성을 조정한다.
21. v0.5.2 주식 도움말에 조회 전용 5거래일/1개월/3개월 변동성 분석 명령을 추가한다.
22. 과거 가격 분석은 history.py에서만 처리하므로 기존 그룹 등록·수정·삭제·소유자 구분을 변경하지 않는다.
23. 목표가 알림·예약·자동발송·주식 주문 기능은 포함하지 않으며 기존 DB·로그 보존 정책을 유지한다.
24. v0.5.6은 기존 사용자 관심그룹 시세 요약에 실제 저장 순서대로 1~10 번호를 붙인다.
25. 숫자 번호는 동일 사용자·채팅방의 5분 메뉴 선택에서만 기존 종목 분석으로 연결되며 그룹 CRUD/DB는 변경하지 않는다.
24. v0.5.3 종목 분석·추가·삭제에 한글 기업명/영문 티커·한국 종목코드를 모두 허용한다.
25. 미국시총10 기업명과 기존 메모리7의 한국·미국·일본 별칭, 구글/웨스턴 디지털 등 명확한 동의어를 지원한다.
26. 사용자가 부여한 별칭은 동일 방·발신자에게만 보이고, 모호한 별칭은 종목을 추정하지 않고 오류를 표시한다.
27. 이름에서 티커로만 변환하며 조회 공급자·기존 SQLite·메모리7·운영 로그와 AI OFF는 변경하지 않는다.
28. v0.5.9 관심종목 그룹 시세표는 가격·등락률과 기존 번호 선택을 유지하고 한국·미국·일본 출처/최신 거래시각/지연상태를 목록 하단에만 표시한다.
29. 그룹 안에서 공급자·체결시각이 다른 종목은 혼합·종목별 시각 차이를 명시하며, 시간외 가격은 각 종목의 별도 행으로 보존한다.
30. 기존 그룹 CRUD/보안 범위/가격 소스/실패 처리/날짜/SQLite 로그/Android 배터리·권한/AI OFF는 변경하지 않는다.
"""
from __future__ import annotations

import re
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Callable

from .market import Stock, WATCHLIST, StockQuoteError, fetch_quote, quote_line, market_source_summary, compact_quote_line, compact_source_summary

MAX_GROUPS = 10
MAX_ITEMS = 10
# ASCII 대문자/숫자 이외 임의 URL, 경로, 셸 메타문자 금지.
_US_TICKER = re.compile(r"^[A-Z]{1,5}(?:-[A-Z])?$")
_KR_TICKER = re.compile(r"^\d{6}\.(?:KS|KQ)$")
_JP_TICKER = re.compile(r"^[0-9A-Z]{3,5}\.T$")
_GROUP = re.compile(r"^[가-힣A-Za-z0-9_-]{1,16}$")
_ALIAS = re.compile(r"^[가-힣A-Za-z0-9_.-]{1,24}$")
_RESERVED = {"목록", "도움말", "그룹생성", "그룹삭제", "추가", "삭제", "메모리7", "프리셋"}
# 2026-11-04 미국 국적 상장기업 시가총액 상위권 고정 스냅샷(종목 구성 자동 갱신 안 함).
# 출처: finhacker.cz/en/largest-us-companies-by-market-cap/ 와 stockanalysis.com/list/largest-us-companies/
# 한 기업은 한 번만: Alphabet GOOGL 선택; 미국 상장 해외 법인(TSM 등)은 포함하지 않음.
US_MARKET_CAP_PRESET_DATE = "2026-11-04"
US_MARKET_CAP_PRESET_NAME = "미국시총10"
US_MARKET_CAP_PRESET = (
    ("NVDA", "엔비디아"),
    ("AAPL", "애플"),
    ("MSFT", "마이크로소프트"),
    ("GOOGL", "알파벳"),
    ("AMZN", "아마존"),
    ("SPCX", "스페이스X"),
    ("AVGO", "브로드컴"),
    ("META", "메타"),
    ("TSLA", "테슬라"),
    ("LLY", "일라이릴리"),
)


def init_schema(db: sqlite3.Connection) -> None:
    """기존 테이블 변경 없이 관심종목 관리 테이블 두 개만 생성."""
    db.execute("""CREATE TABLE IF NOT EXISTS stock_groups (
        room TEXT NOT NULL, sender TEXT NOT NULL, name TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        PRIMARY KEY(room, sender, name))""")
    db.execute("""CREATE TABLE IF NOT EXISTS stock_items (
        room TEXT NOT NULL, sender TEXT NOT NULL, group_name TEXT NOT NULL,
        ticker TEXT NOT NULL, alias TEXT NOT NULL,
        currency TEXT NOT NULL, market TEXT NOT NULL, timezone_name TEXT NOT NULL,
        sort_order INTEGER NOT NULL,
        PRIMARY KEY(room, sender, group_name, ticker))""")
    db.execute("""CREATE INDEX IF NOT EXISTS idx_stock_items_order
        ON stock_items(room,sender,group_name,sort_order)""")


def _scope(room: str, sender: str) -> None:
    if not room.strip() or not sender.strip():
        raise StockQuoteError("관심종목은 채팅방과 발신자 정보가 확인된 경우에만 사용할 수 있습니다.")


def _name(text: str, *, allow_reserved: bool = False) -> str:
    name = text.strip()
    if not _GROUP.fullmatch(name) or (not allow_reserved and name in _RESERVED):
        raise StockQuoteError("그룹명은 한글·영문·숫자·_·- 1~16자로 지정하세요. (메모리7은 고정)")
    return name


# 알려진 종목만 한글 이름으로 매칭한다. 데이터 제공자·티커/통화는 기존 설정을 그대로 사용.
_KNOWN_NAME_TICKERS = {s.name.replace(' ', '').upper(): s.ticker for s in WATCHLIST}
_KNOWN_NAME_TICKERS.update({name.replace(' ', '').upper(): ticker for ticker, name in US_MARKET_CAP_PRESET})
_KNOWN_NAME_TICKERS.update({
    'SK하이닉스': '000660.KS', '에스케이하이닉스': '000660.KS',
    'SK하이닉스ADR': 'SKHY', '하이닉스ADR': 'SKHY',
    '구글': 'GOOGL', '시게이트': 'STX',
    '웨스턴디지털': 'WDC', '스페이스엑스': 'SPCX',
})


def resolve_saved_alias(db: sqlite3.Connection, room: str, sender: str, name: str) -> Stock | None:
    """본인 채팅방에 저장한 정확한 별칭만 조회한다. 서로 다른 티커가 중복되면 거부."""
    _scope(room, sender)
    target = name.strip()
    if not _ALIAS.fullmatch(target):
        return None
    matches = db.execute("""SELECT alias,ticker,currency,market,timezone_name FROM stock_items
        WHERE room=? AND sender=? AND alias=? ORDER BY sort_order""",
        (room, sender, target)).fetchall()
    unique = {row[1]: Stock(*row) for row in matches}
    if len(unique) > 1:
        raise StockQuoteError(f"'{target}' 별칭이 여러 종목에 사용됩니다. 종목명을 고유하게 지정하거나 티커를 사용하세요.")
    return next(iter(unique.values()), None)


def resolve_stock(value: str, alias: str = "") -> Stock:
    """메모리7·미국시총10의 기업명과 동의어를 기존 정확한 티커/통화로 변환."""
    readable = value.strip()
    normalized_name = ''.join(readable.split()).upper()
    mapped_ticker = _KNOWN_NAME_TICKERS.get(normalized_name)
    v = mapped_ticker or readable.upper()
    if re.fullmatch(r"\d{6}", v):
        v += ".KS"
    known = next((s for s in WATCHLIST if s.ticker.upper() == v or s.name.upper() == v), None)
    if known is not None:
        ticker, currency, market, tz, default_alias = (known.ticker, known.currency,
            known.market, known.timezone_name, known.name)
    else:
        if _KR_TICKER.fullmatch(v):
            ticker, currency, market, tz = v, "KRW", "한국", "Asia/Seoul"
        elif _JP_TICKER.fullmatch(v):
            ticker, currency, market, tz = v, "JPY", "일본", "Asia/Tokyo"
        elif _US_TICKER.fullmatch(v):
            ticker, currency, market, tz = v, "USD", "미국", "America/New_York"
        else:
            raise StockQuoteError("종목코드 형식이 올바르지 않습니다. 예: MU / 005930 / 285A.T")
        default_alias = ticker
    # 한글 이름으로 요청한 경우 친숙한 이름을 출력한다. 티커 입력 시 기존 표시 방식 유지.
    display = alias.strip() or (normalized_name if mapped_ticker else default_alias)
    if not _ALIAS.fullmatch(display):
        raise StockQuoteError("종목 별칭은 공백 없이 한글·영문·숫자·.·_·- 1~24자로 지정하세요.")
    return Stock(display, ticker, currency, market, tz)


def command_help() -> str:
    """기존 모든 주식 명령을 유지하며 중복 예시만 줄인 도움말."""
    return "\n".join(['📋 주식 명령','주식 목록 / 주식 메모리7','주식 그룹생성 반도체','주식 프리셋 미국시총10','주식 추가 반도체 삼성전자','주식 반도체 / 주식 분석 반도체','주식 분석 마이크론','주식 삭제 반도체 마이크론','주식 그룹삭제 반도체 확인','※ 그룹 최대 10종목 · 메모리7 보호','※ 미국시총10 고정 구성 · AI 불필요'])


def is_group_quote_request(argument: str) -> bool:
    """단일 그룹명 요청만 외부 시세 조회로 분류. CRUD는 DB 락 내부에서 처리."""
    parts = argument.split()
    return len(parts) == 1 and parts[0] not in _RESERVED


def load_group(db: sqlite3.Connection, room: str, sender: str, name: str) -> tuple[Stock, ...]:
    _scope(room, sender)
    key = _name(name)
    if not db.execute("SELECT 1 FROM stock_groups WHERE room=? AND sender=? AND name=?",
                      (room, sender, key)).fetchone():
        raise StockQuoteError(f"'{key}' 관심종목 그룹이 없습니다. 사용법: 앙개야 주식 목록 / 그룹생성 {key}")
    rows = db.execute("""SELECT alias,ticker,currency,market,timezone_name FROM stock_items
        WHERE room=? AND sender=? AND group_name=? ORDER BY sort_order,ticker""",
        (room, sender, key)).fetchall()
    return tuple(Stock(*row) for row in rows)


def group_report(name: str, stocks: tuple[Stock, ...], *, fetcher: Callable[[Stock], object] | None = None) -> str:
    """기존 market.fetch_quote로만 가격 조회; 실패값은 임의 생성하지 않음."""
    if not stocks:
        return f"📂 {name} 관심종목 그룹은 비어 있습니다.\n주식 추가 {name} MU 마이크론"
    lookup = fetcher or fetch_quote
    def one(stock: Stock):
        try:
            return lookup(stock)
        except (StockQuoteError, OSError, ValueError, TimeoutError):
            return None
    with ThreadPoolExecutor(max_workers=min(5, len(stocks))) as pool:
        quotes = list(pool.map(one, stocks))
    lines = [f"📊 {name} 관심종목 시세 요약"]
    dates: dict[str, str] = {}
    failed = 0
    for index, (stock, quote) in enumerate(zip(stocks, quotes), start=1):
        if quote is None:
            lines.append(f"{index}. {stock.name} : 조회 불가")
            failed += 1
        else:
            lines.append(f"{index}. {compact_quote_line(quote)}")
            dates[stock.market] = quote.market_time.strftime("%m/%d")
    if failed == len(stocks):
        raise StockQuoteError(f"'{name}' 그룹의 모든 시세를 조회하지 못했습니다.")
    if dates:
        pass  # 거래일/기준시각은 압축 출처에서 표시
    lines.append('')
    lines.extend(compact_source_summary(quotes))
    if failed:
        lines.append(f"※ {failed}종목 조회 실패 · 임의 수치 보충 없음")
    lines.append("※ 무료·지연 가능·실시간 아님")
    lines.append(f"※ 5분 내 1~{len(stocks)}: 종목 분석")
    return "\n".join(lines)


def execute_group_command(db: sqlite3.Connection, room: str, sender: str, argument: str) -> str:
    """관심그룹 CRUD/목록. 기존 FastAPI jobs/events와 동일한 트랜잭션 안에서 호출."""
    _scope(room, sender)
    parts = argument.split()
    if not parts or parts[0] == "도움말":
        return command_help()
    action = parts[0]
    if action == "목록":
        if len(parts) != 1:
            raise StockQuoteError("사용법: 앙개야 주식 목록")
        rows = db.execute("""SELECT g.name, COUNT(i.ticker) FROM stock_groups g
            LEFT JOIN stock_items i ON i.room=g.room AND i.sender=g.sender AND i.group_name=g.name
            WHERE g.room=? AND g.sender=? GROUP BY g.name ORDER BY g.created_at,g.name""",
            (room, sender)).fetchall()
        lines = ["📂 관심그룹", "메모리7 8종목 · 기본"]
        lines.extend(f"{name} {count}종목" for name, count in rows)
        lines.append("※ 추가: 주식 그룹생성 그룹명")
        return "\n".join(lines)
    if action == "프리셋":
        if len(parts) != 2 or parts[1] != US_MARKET_CAP_PRESET_NAME:
            raise StockQuoteError("사용법: 앙개야 주식 프리셋 미국시총10")
        name = US_MARKET_CAP_PRESET_NAME
        if db.execute("SELECT 1 FROM stock_groups WHERE room=? AND sender=? AND name=?",
                      (room, sender, name)).fetchone():
            raise StockQuoteError("'미국시총10' 그룹이 이미 존재합니다. 기존 종목을 덮어쓰지 않습니다.")
        count = db.execute("SELECT COUNT(*) FROM stock_groups WHERE room=? AND sender=?",
                           (room, sender)).fetchone()[0]
        if count >= MAX_GROUPS:
            raise StockQuoteError(f"관심종목 그룹은 최대 {MAX_GROUPS}개까지 등록할 수 있습니다.")
        if len(US_MARKET_CAP_PRESET) > MAX_ITEMS:
            raise StockQuoteError("시총 프리셋 수가 그룹 제한을 초과했습니다.")
        # SQLite 기존 요청 트랜잭션 안에서 그룹과 종목을 한꺼번에 생성한다.
        # 코드와 이름을 모두 고정한 안전한 템플릿이며 기존 테이블/기록은 삭제하지 않는다.
        stocks = tuple(resolve_stock(ticker, alias) for ticker, alias in US_MARKET_CAP_PRESET)
        db.execute("INSERT INTO stock_groups(room,sender,name,created_at) VALUES (?,?,?,?)",
                   (room, sender, name, int(time.time())))
        db.executemany("""INSERT INTO stock_items
            (room,sender,group_name,ticker,alias,currency,market,timezone_name,sort_order)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            [(room, sender, name, item.ticker, item.name, item.currency, item.market,
              item.timezone_name, idx) for idx, item in enumerate(stocks, start=1)])
        return (f"✅ {name} 10종목 등록\n"
                f"조회: 주식 {name}\n"
                f"※ {US_MARKET_CAP_PRESET_DATE} 고정 구성 · 순위 자동 갱신 없음")
    if action == "그룹생성":
        if len(parts) != 2:
            raise StockQuoteError("사용법: 앙개야 주식 그룹생성 반도체")
        name = _name(parts[1])
        if db.execute("SELECT 1 FROM stock_groups WHERE room=? AND sender=? AND name=?",
                      (room, sender, name)).fetchone():
            raise StockQuoteError("이미 존재하는 관심종목 그룹입니다.")
        count = db.execute("SELECT COUNT(*) FROM stock_groups WHERE room=? AND sender=?",
                           (room, sender)).fetchone()[0]
        if count >= MAX_GROUPS:
            raise StockQuoteError(f"관심종목 그룹은 최대 {MAX_GROUPS}개까지 등록할 수 있습니다.")
        db.execute("INSERT INTO stock_groups(room,sender,name,created_at) VALUES (?,?,?,?)",
                   (room, sender, name, int(time.time())))
        return f"✅ {name} 그룹 생성\n추가: 주식 추가 {name} MU 마이크론"
    if action == "그룹삭제":
        if len(parts) != 3 or parts[2] != "확인":
            raise StockQuoteError("그룹 전체 삭제를 확인하려면: 앙개야 주식 그룹삭제 그룹명 확인")
        name = _name(parts[1])
        rows = db.execute("DELETE FROM stock_groups WHERE room=? AND sender=? AND name=?",
                          (room, sender, name)).rowcount
        if not rows:
            raise StockQuoteError("해당 관심종목 그룹이 없습니다.")
        db.execute("DELETE FROM stock_items WHERE room=? AND sender=? AND group_name=?",
                   (room, sender, name))
        return f"✅ {name} 그룹 삭제"
    if action == "추가":
        if not 3 <= len(parts) <= 4:
            raise StockQuoteError("사용법: 앙개야 주식 추가 반도체 MU 마이크론")
        name = _name(parts[1]); stock = resolve_stock(parts[2], parts[3] if len(parts) == 4 else "")
        if not db.execute("SELECT 1 FROM stock_groups WHERE room=? AND sender=? AND name=?",
                          (room, sender, name)).fetchone():
            raise StockQuoteError("관심종목 그룹이 없습니다. '주식 그룹생성 그룹명'으로 먼저 만드세요.")
        count = db.execute("SELECT COUNT(*) FROM stock_items WHERE room=? AND sender=? AND group_name=?",
                           (room, sender, name)).fetchone()[0]
        exists = db.execute("SELECT 1 FROM stock_items WHERE room=? AND sender=? AND group_name=? AND ticker=?",
                            (room, sender, name, stock.ticker)).fetchone()
        if exists:
            raise StockQuoteError("이미 이 그룹에 등록된 종목입니다.")
        if count >= MAX_ITEMS:
            raise StockQuoteError(f"그룹당 종목은 최대 {MAX_ITEMS}개입니다.")
        db.execute("""INSERT INTO stock_items
            (room,sender,group_name,ticker,alias,currency,market,timezone_name,sort_order)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (room, sender, name, stock.ticker, stock.name, stock.currency, stock.market,
             stock.timezone_name, count + 1))
        return f"✅ {name} +{stock.name} ({stock.ticker}) · {count+1}/{MAX_ITEMS}"
    if action == "삭제":
        if len(parts) != 3:
            raise StockQuoteError("사용법: 앙개야 주식 삭제 반도체 MU")
        name = _name(parts[1])
        try:
            stock = resolve_stock(parts[2])
        except StockQuoteError as error:
            # 기존 그룹에 직접 등록한 별칭도 삭제 허용. 다른 채팅방/그룹은 절대 조회하지 않음.
            row = db.execute("""SELECT ticker FROM stock_items
                WHERE room=? AND sender=? AND group_name=? AND alias=?""",
                (room, sender, name, parts[2])).fetchone()
            if row is None:
                raise error
            stock = resolve_stock(row[0])
        result = db.execute("DELETE FROM stock_items WHERE room=? AND sender=? AND group_name=? AND ticker=?",
                            (room, sender, name, stock.ticker)).rowcount
        if not result:
            raise StockQuoteError("해당 그룹에 등록된 종목이 없습니다.")
        return f"✅ {name} -{stock.ticker} 삭제"
    raise StockQuoteError("지원하지 않는 관심종목 명령입니다. '주식 도움말'을 확인하세요.")
