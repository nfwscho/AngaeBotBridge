"""
앙개봇 Python Core v0.5.2 과거 시세·실현변동성 — 전체 기능과 안전 제약 상세 설명
1. 기존 메모리7(8종목)/사용자 관심그룹(최대 10종목)/미국시총10 프리셋을 수정하지 않는다.
2. '앙개야 주식 분석 MU' 또는 '주식 분석 005930/285A.T'로 단일 종목을 분석한다.
3. '앙개야 주식 분석 그룹명'으로 기존 관심그룹의 종목별 5일·1개월·3개월 성과를 비교한다.
4. '앙개야 주식 분석 메모리7'은 고정 8종목을 대상으로 개별 종목 시세와 별도로 요약한다.
5. 5거래일 일별 종가와 전 거래일 대비 수익률, 5거래일 누적수익률을 계산한다.
6. 약 1개월=최근 21거래일, 약 3개월=최근 63거래일로 정의하고 각 누적수익률을 계산한다.
7. 각 기간의 실현변동성은 일간 로그수익률 표본표준편차(ddof=1) × sqrt(252) × 100%로 연율화한다.
8. 과거 가격의 일별 OHLC 종가/수정종가를 검증하고 수정종가가 유효하면 수익률·변동성 계산에 사용한다.
9. 일별 가격 표시에는 실제 종가를 사용하며, 수정종가 기준 수익률과 혼동하지 않게 안내한다.
10. Yahoo Finance chart 6mo/1d를 우선 조회하고, 한국 종목은 네이버 일봉 차트(기존 무료 공급자)를 우선 사용한다.
11. 한국 종목이 네이버에서 실패하면 Yahoo, 일본 종목이 Yahoo에서 실패하면 네이버 해외 일봉을 보조로 시도한다.
12. 사용자 지정 호스트/URL/티커 임의 접속을 허용하지 않고 기존 watchlists.resolve_stock의 형식 검증을 사용한다.
13. 최근 데이터가 오래되거나 시점/통화/종목코드가 잘못되면 임의 숫자를 출력하지 않는다.
14. 장중 미완성 일봉은 분석에서 제외하고 현지 정규장 종가와 해당 거래일을 기준으로 한다.
15. 1개월·3개월 표본이 부족하면 기간별 '데이터 부족'을 표시하고 다른 기간·다른 종목을 보존한다.
16. 제공처별 실패/요청시간 초과/JSON 오류를 해당 종목에만 격리해 계산·운영 명령의 정상 응답을 유지한다.
17. 원격 호출은 3초 내외 타임아웃·응답 크기 제한을 적용하며 그룹 조회는 동시 5개 이내로 제한한다.
18. 동일 종목의 짧은 시간 내 재조회는 5분 메모리 캐시로 완화하고 최신 호가로 위장하지 않는다.
19. 모든 결과는 기존 FastAPI 토큰 인증과 jobs/events 중복 요청/에러 기록 흐름을 그대로 사용한다.
20. Android 알림 수신/RemoteInput, SQLite 사용자 그룹, AI OFF, 기존 서버/Watchdog/SSH/로그는 변경하지 않는다.
21. 주가 분석은 조회 시에만 실행하며 자동 가격 감시·목표가 알림·예약 발송·주식 주문은 구현하지 않는다.
22. 공급자 정보는 무료 비공식/지연 데이터이므로 실제 증권사·거래소와 차이가 날 수 있음을 표시한다.
23. 테스트용 opener/fetcher/now 주입을 허용하여 외부 인터넷 없이 시차·수익률·변동성·장애를 회귀 검증한다.
"""
from __future__ import annotations

import json
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime, time as clock_time, timedelta, timezone
from statistics import stdev
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from .market import Stock, WATCHLIST, StockQuoteError
from .watchlists import resolve_stock

# 공급자 원문을 영구 저장하지 않으며 캐시 내 종가 데이터를 최대 5분만 유지한다.
HISTORY_CACHE_SECONDS = 300.0
HISTORY_REQUEST_TIMEOUT = 3.0
HISTORY_MAX_BYTES = 480_000
MIN_LATEST_AGE_DAYS = 10
_ONE_MONTH_SESSIONS = 21
_THREE_MONTH_SESSIONS = 63
_CACHE_LOCK = threading.Lock()
_CACHE: dict[tuple[str, str], tuple[float, tuple['DailyBar', ...]]] = {}


@dataclass(frozen=True)
class DailyBar:
    date: date
    close: float
    adjusted: float


@dataclass(frozen=True)
class PeriodResult:
    sessions: int
    cumulative_pct: float | None
    volatility_pct: float | None


@dataclass(frozen=True)
class HistoryResult:
    stock: Stock
    bars: tuple[DailyBar, ...]
    source: str


def _finite_positive(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.replace(',', '').strip()
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def _local_now(stock: Stock, now: datetime | None = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise StockQuoteError('시각 정보가 불완전합니다.')
    return now.astimezone(ZoneInfo(stock.timezone_name))


def _is_finished_session(stock: Stock, trade_date: date, now: datetime) -> bool:
    local = _local_now(stock, now)
    if trade_date > local.date():
        return False
    if trade_date < local.date():
        return True
    # 거래소별 종가 이후 15분이 지나지 않은 일봉은 미확정으로 처리한다.
    close = clock_time(16, 15) if stock.market == '미국' else clock_time(15, 45)
    return local.time() >= close


def _clean_bars(stock: Stock, bars: list[DailyBar], now: datetime | None = None) -> tuple[DailyBar, ...]:
    now = now or datetime.now(timezone.utc)
    valid = {}
    for bar in bars:
        if (_finite_positive(bar.close) is not None and
            _finite_positive(bar.adjusted) is not None and
            _is_finished_session(stock, bar.date, now)):
            valid[bar.date] = bar
    ordered = tuple(sorted(valid.values(), key=lambda item: item.date))
    if not ordered:
        raise StockQuoteError('완료된 거래일의 종가 데이터가 없습니다.')
    age = (_local_now(stock, now).date() - ordered[-1].date).days
    if age < 0 or age > MIN_LATEST_AGE_DAYS:
        raise StockQuoteError('최신 종가가 오래되었거나 거래일이 잘못되었습니다.')
    return ordered


def parse_yahoo_history(stock: Stock, payload: dict, *, now: datetime | None = None) -> tuple[DailyBar, ...]:
    """Yahoo 일봉: 확정된 1일봉의 실제 종가와 선택적 수정종가를 결합한다."""
    try:
        result = payload['chart']['result'][0]
        meta = result['meta']
        if meta.get('symbol', '').upper() != stock.ticker.upper() or meta.get('currency') != stock.currency:
            raise StockQuoteError('시세 종목코드 또는 통화가 일치하지 않습니다.')
        if meta.get('dataGranularity', '1d') != '1d':
            raise StockQuoteError('일봉 데이터가 아닙니다.')
        dates = result['timestamp']
        candles = result['indicators']['quote'][0]['close']
        adjusted_items = result['indicators'].get('adjclose') or []
        adjusted = adjusted_items[0].get('adjclose', []) if adjusted_items else []
        if not isinstance(dates, list) or not isinstance(candles, list) or len(dates) != len(candles):
            raise StockQuoteError('일봉 날짜와 종가 수가 다릅니다.')
        if not isinstance(adjusted, list):
            adjusted = []
        tz = ZoneInfo(stock.timezone_name)
        # 수정종가 일부가 누락된 경우 서로 다른 조정 기준을 섞지 않고 전체를 원종가 기준으로 계산.
        valid_close_indices = [i for i, c in enumerate(candles) if _finite_positive(c) is not None]
        fully_adjusted = (len(adjusted) == len(dates) and
                          all(_finite_positive(adjusted[i]) is not None for i in valid_close_indices))
        bars = []
        for index, stamp in enumerate(dates):
            if isinstance(stamp, bool) or not isinstance(stamp, (int, float)) or not math.isfinite(stamp):
                continue
            raw = _finite_positive(candles[index])
            if raw is None:
                continue
            adj = _finite_positive(adjusted[index]) if fully_adjusted else None
            local_date = datetime.fromtimestamp(stamp, tz=tz).date()
            bars.append(DailyBar(local_date, raw, adj if adj is not None else raw))
        return _clean_bars(stock, bars, now)
    except (IndexError, ValueError, TypeError, KeyError, OverflowError, OSError) as exc:
        if isinstance(exc, StockQuoteError):
            raise
        raise StockQuoteError('Yahoo 과거 시세 데이터 형식 오류') from exc


def _parse_yyyymmdd(value: object) -> date:
    string = str(value).strip().replace('-', '')
    if len(string) != 8 or not string.isascii() or not string.isdigit():
        raise ValueError('잘못된 거래일')
    return datetime.strptime(string, '%Y%m%d').date()


def parse_naver_history(stock: Stock, payload: object, *, now: datetime | None = None) -> tuple[DailyBar, ...]:
    """네이버 일봉의 priceInfos만 허용하고 타 종목/월봉 자료는 거부한다."""
    try:
        if not isinstance(payload, dict):
            raise StockQuoteError('네이버 일봉 JSON 오류')
        if ('itemCode' in payload and str(payload['itemCode']).upper() not in
            (stock.ticker.upper(), stock.ticker.split('.')[0].upper())):
            raise StockQuoteError('네이버 종목코드가 일치하지 않습니다.')
        rows = payload.get('priceInfos')
        if rows is None:
            rows = payload.get('priceInfoList')
        if not isinstance(rows, list):
            raise StockQuoteError('네이버 일봉 목록이 없습니다.')
        parsed = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            value = _finite_positive(row.get('closePrice'))
            if value is None:
                continue
            try:
                day = _parse_yyyymmdd(row.get('localDate'))
            except ValueError:
                continue
            # 네이버 차트 종가는 해당 공급자의 일봉 기준이다. 수정종가 보장하지 않는다.
            parsed.append(DailyBar(day, value, value))
        return _clean_bars(stock, parsed, now)
    except (IndexError, TypeError, ValueError, KeyError) as exc:
        if isinstance(exc, StockQuoteError):
            raise
        raise StockQuoteError('네이버 과거 시세 데이터 형식 오류') from exc


def _read_json(url: str, opener, timeout: float = HISTORY_REQUEST_TIMEOUT) -> dict:
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (AngaeBotPersonal/0.5.2)',
                                    'Accept': 'application/json'}, method='GET')
    with opener(request, timeout=timeout) as response:
        raw = response.read(HISTORY_MAX_BYTES + 1)
    if len(raw) > HISTORY_MAX_BYTES:
        raise StockQuoteError('시세 응답 크기 초과')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise StockQuoteError('시세 응답 형식 오류')
    return value


def fetch_history(stock: Stock, *, opener=urlopen, now: datetime | None = None,
                  use_cache: bool = True) -> HistoryResult:
    """국내 네이버→Yahoo, 일본/미국 Yahoo→네이버(일본 보조). 실패 시 오류 원문을 외부 공개하지 않는다."""
    if not (stock.market in {'한국', '일본', '미국'} and
            stock.currency in {'KRW', 'JPY', 'USD'}):
        raise StockQuoteError('지원되지 않는 시장입니다.')
    from .watchlists import resolve_stock as validate
    normal = validate(stock.ticker)
    if (normal.ticker, normal.market, normal.currency) != (stock.ticker, stock.market, stock.currency):
        raise StockQuoteError('허용되지 않은 종목코드입니다.')
    key = (stock.ticker, stock.currency)
    current = time.monotonic()
    if use_cache and opener is urlopen:
        with _CACHE_LOCK:
            saved = _CACHE.get(key)
            if saved and current - saved[0] < HISTORY_CACHE_SECONDS:
                return HistoryResult(stock, saved[1], '5분 이내 캐시')
    symbol = quote(stock.ticker, safe='.')
    code = stock.ticker.split('.')[0]
    sources = []
    if stock.market == '한국':
        sources.append(('네이버 일봉', 'https://api.stock.naver.com/chart/domestic/item/' +
                        code + '?periodType=dayCandle', parse_naver_history))
    for host in ('query1.finance.yahoo.com', 'query2.finance.yahoo.com'):
        sources.append(('Yahoo 일봉', f'https://{host}/v8/finance/chart/{symbol}?range=6mo&interval=1d&includeAdjustedClose=true',
                        parse_yahoo_history))
    if stock.market == '일본':
        sources.append(('네이버 해외 일봉', 'https://api.stock.naver.com/chart/foreign/item/' +
                        symbol + '?periodType=dayCandle', parse_naver_history))
    for source, url, parser in sources:
        try:
            data = _read_json(url, opener)
            bars = parser(stock, data, now=now)
            if use_cache and opener is urlopen:
                with _CACHE_LOCK:
                    _CACHE[key] = (time.monotonic(), bars)
            return HistoryResult(stock, bars, source)
        except (HTTPError, URLError, TimeoutError, OSError, StockQuoteError, ValueError,
                json.JSONDecodeError, TypeError):
            continue
    raise StockQuoteError('과거 시세 조회 실패 (무료 공급자 연결/데이터 확인 필요)')


def period_result(bars: tuple[DailyBar, ...], sessions: int) -> PeriodResult:
    """최근 N개 거래일의 N개 로그수익률; N+1개의 수정종가가 필요하다."""
    if len(bars) < sessions + 1:
        return PeriodResult(sessions, None, None)
    values = [bar.adjusted for bar in bars[-(sessions + 1):]]
    if any(value <= 0 or not math.isfinite(value) for value in values):
        return PeriodResult(sessions, None, None)
    returns = [math.log(values[index] / values[index - 1]) for index in range(1, len(values))]
    cumulative = (values[-1] / values[0] - 1) * 100
    volatility = stdev(returns) * math.sqrt(252) * 100 if sessions >= 2 else None
    return PeriodResult(sessions, cumulative, volatility)


def _sign(percent: float | None) -> str:
    return '데이터 부족' if percent is None else f'{percent:+.2f}%'


def _currency_close(stock: Stock, value: float) -> str:
    if stock.currency == 'KRW':
        return f'{value:,.0f}원'
    if stock.currency == 'JPY':
        return f'¥{value:,.1f}'
    return f'${value:,.2f}'


def _period_text(bars: tuple[DailyBar, ...], sessions: int) -> str:
    metrics = period_result(bars, sessions)
    if metrics.cumulative_pct is None or metrics.volatility_pct is None:
        return '데이터 부족'
    return f'{_sign(metrics.cumulative_pct)} / 연변동성 {metrics.volatility_pct:.1f}%'


def individual_report(history: HistoryResult, *, fetched_at: datetime | None = None) -> str:
    stock, bars = history.stock, history.bars
    lines = [f'📈 {stock.name} ({stock.ticker}) 최근 5거래일 종가']
    last_five = bars[-5:]
    for index, bar in enumerate(last_five):
        previous = bars[-len(last_five) + index - 1] if len(bars) > len(last_five) or index > 0 else None
        daily = ((bar.adjusted / previous.adjusted - 1) * 100) if previous else None
        lines.append(f'{bar.date:%m/%d} {_currency_close(stock, bar.close)} ({_sign(daily)})')
    lines.append('5거래일 누적: ' + _sign(period_result(bars, 5).cumulative_pct))
    lines.append('1개월(21일): ' + _period_text(bars, _ONE_MONTH_SESSIONS))
    lines.append('3개월(63일): ' + _period_text(bars, _THREE_MONTH_SESSIONS))
    lines.append(f'기준 거래일 {bars[-1].date:%Y-%m-%d} · {history.source}')
    lines.append('※ 일별은 종가·수익률은 수정종가 우선. 변동성=일간 로그수익률 표준편차×√252, 연율화.')
    lines.append('※ 장마감 종가 기준, 비공식/지연 데이터. 알림·자동매매 없음.')
    return '\n'.join(lines)


def group_report(name: str, stocks: tuple[Stock, ...], *, fetcher=None) -> str:
    """그룹은 10종목까지 각 5일, 1/3개월 수익률·변동성 요약. 추가 쓰기 없음."""
    if not stocks:
        return f'📈 {name} 그룹의 등록 종목이 없습니다.'
    lookup = fetcher or fetch_history
    def one(stock):
        try:
            return lookup(stock)
        except (StockQuoteError, ValueError, OSError, TimeoutError):
            return None
    # 10개 그룹에서도 Android 23초 제한 내 응답하도록 요청당 최대 10종목을 병렬 실행.
    with ThreadPoolExecutor(max_workers=min(10, len(stocks))) as pool:
        results = list(pool.map(one, stocks))
    lines = [f'📊 {name} 그룹 5일·1개월·3개월 변동성']
    available = 0
    for stock, result in zip(stocks, results):
        if result is None:
            lines.append(f'{stock.name}: 조회 불가')
            continue
        available += 1
        p5 = period_result(result.bars, 5)
        p1 = period_result(result.bars, 21)
        p3 = period_result(result.bars, 63)
        one_month = _sign(p1.cumulative_pct) + (f'/σ{p1.volatility_pct:.0f}%' if p1.volatility_pct is not None else '')
        three_month = _sign(p3.cumulative_pct) + (f'/σ{p3.volatility_pct:.0f}%' if p3.volatility_pct is not None else '')
        lines.append(f'{stock.name}[{result.bars[-1].date:%m/%d}] 5일 {_sign(p5.cumulative_pct)} | 1M {one_month} | 3M {three_month}')
    if available == 0:
        raise StockQuoteError(f'{name} 그룹의 과거 종가를 조회하지 못했습니다.')
    lines.append('※ 1M=21일·3M=63거래일 / σ=연율화 실현변동성(%, 표준편차×√252).')
    lines.append('※ 장마감 종가·수정종가 우선 / 비공식·지연 시세. 자동 알림 없음.')
    return '\n'.join(lines)


def analyze_single(value: str) -> str:
    """종목코드는 기존 관심종목과 동일한 허용 규칙만 사용한다."""
    stock = resolve_stock(value)
    return individual_report(fetch_history(stock))


def analyze_group(name: str, stocks: tuple[Stock, ...]) -> str:
    return group_report(name, stocks)


def is_analysis_request(argument: str) -> bool:
    parts = argument.split()
    return len(parts) > 1 and parts[0] == '분석'
