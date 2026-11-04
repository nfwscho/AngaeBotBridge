"""
앙개봇 Python Core v0.4.3 — 메모리7 무료 주식 시세 모듈 전체 기능 설명
1. '앙개야 주식 메모리7' 및 '앙개야 메모리7'의 지정된 8개 종목 시세를 조회한다.
2. 삼성전자 005930.KS, SK하이닉스 000660.KS, 마이크론 MU, SK하이닉스 ADR SKHY,
   샌디스크 SNDK, 키오시아 285A.T, 씨게이트 STX, 웨스턴디지털 WDC를 고정 순서로 표시한다.
3. 가격은 종목별 현지 통화 원/달러/엔으로 나타내며, 현지 전일 종가 대비 등락률을 계산한다.
4. 한국/미국/일본의 거래일과 조회 시각을 구분하고, 지연/휴장 시세를 당일 시세로 가장하지 않는다.
5. 공개 Yahoo Finance chart API를 참고한 비공식 무료 조회를 수행하며 API 키나 OpenAI는 사용하지 않는다.
6. 각 종목의 시세 숫자·전일종가는 원격 응답이 명확할 때만 표시하고 값이 없으면 조회 불가로 표시한다.
7. 네트워크 조회 실패/403/429/타임아웃을 부분 실패로 격리해 다른 종목과 기존 명령을 보존한다.
8. 동시에 최대 4개를 조회하고 요청당 짧은 타임아웃을 설정해 카카오톡 응답 지연을 제한한다.
9. 30초 메모리 캐시로 반복 명령의 호출을 줄이고 저장된 가격을 실시간 데이터로 위장하지 않는다.
10. 토큰·사용자 질문·방/발신자·원본 시세 응답을 로그/DB에 추가 기록하지 않으며 기존 jobs/events만 사용한다.
11. 임의의 입력 종목명/URL로 외부 접속을 하지 않고 고정 허용 티커와 HTTPS 호스트만 조회한다.
12. 웹 시세 출처/제공 지연/사용 한계가 있으므로 금융 거래용 실시간 호가로 사용하지 않는다.
13. 테스트용 전송/시간 주입을 지원하여 외부 인터넷 연결 없이 수치와 장애 동작을 검증한다.
14. 한국 종목은 네이버 금융 모바일 JSON → 네이버 실시간 폴링 → 기존 Yahoo Chart 순으로 조회한다.
15. 키오시아는 기존 Yahoo Chart 우선 시도 후 Yahoo Japan 공식 종목 페이지의 동경시장 시세만 검증해 보완한다.
16. 가격·변동률·종목 코드·거래일을 검증하며 야간 PTS 가격, 다른 종목 및 오래된 값을 사용하지 않는다.
17. 외부 시세 공급자별 실패를 격리하고 기존 미국 종목·메모리7 출력·캐시·이벤트 로그 흐름을 보존한다.
18. v0.4.3은 Yahoo Japan 본장 날짜를 시각·거래일 상세에서 유연하게 추출하여 HTML 구조 변화를 허용한다.
19. 키오시아는 기존 Yahoo(미국/일본) 조회 실패 시 일본 증권사 공개 시세 페이지에서 날짜·전일가·등락률을 검증한다.
20. 일본 현지 증권사 원문 날짜/가격/등락률의 정합성을 검증하고 야간 PTS·오래된 값은 채택하지 않는다.
21. 해외 시세 추가 경로는 키오시아 단일 종목만 허용하고 한국 2종목·미국 5종목·캐시/출력은 유지한다.
22. 모든 신규 오류는 기존 조회 불가로 격리하며 토큰/요청 원문은 기록하지 않는다.
23. 데이터 공급자는 비공식/지연/접근 차단 가능하고 재판매·실시간 거래용으로 사용하지 않는다.
24. v0.5.6은 메모리7 원본 8종목에 1~8 번호를 붙이고 조회 불가 항목도 자리/순서를 유지한다.
25. 기존 통화/시세/날짜/30초 캐시/무료 공급자 폴백/오류·로그는 그대로 보존한다.
26. 번호 실행은 별도 selection_menu.py에서 원래 종목 티커로 매핑해 5일·21일·63일 분석을 실행한다.
27. 가격 알림·자동거래·스케줄러·배터리 표시(Android 담당)에는 변경을 가하지 않는다.
28. v0.5.7은 국내 KRX 현재가를 네이버 폴링 JSON 우선으로 조회하고 모바일 JSON은 2순위로 사용한다.
29. 국내 시세는 KRX 본장 현재가와 네이버가 별도로 제공하는 장전·장후 가격을 구분해 출력한다.
30. KRX 실시간표시는 지연시간 0분, OPEN, 3분 이내 체결, 응답 시각의 신선도가 모두 확인된 경우에만 허용한다.
31. 장마감·오래된 체결·시세상태 미확인·Yahoo 대체 가격을 실시간으로 표시하지 않으며 시각과 출처를 함께 기록한다.
32. 시간외 거래소가 메타데이터에서 확인되지 않으면 NXT로 단정하지 않고 별도 시간외 시세로 표시한다.
33. 제공자 URL/개별 사용자 그룹·티커/로그/DB·가격 분석·메모리7 번호 메뉴·캐시·Android 배터리 기능은 모두 보존한다.
34. 추가 권한·인증키·AI API·주기적 폴링·자동 주문·가격 알림/예약 발신은 도입하지 않는다.
"""
from __future__ import annotations

import json
import math
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import date, datetime, time as dt_time, timedelta, timezone
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser
from urllib.parse import quote as encode_component
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class Stock:
    name: str
    ticker: str
    currency: str
    market: str
    timezone_name: str


WATCHLIST = (
    Stock('삼성전자', '005930.KS', 'KRW', '한국', 'Asia/Seoul'),
    Stock('하이닉스', '000660.KS', 'KRW', '한국', 'Asia/Seoul'),
    Stock('마이크론', 'MU', 'USD', '미국', 'America/New_York'),
    Stock('SKHY', 'SKHY', 'USD', '미국', 'America/New_York'),
    Stock('샌디스크', 'SNDK', 'USD', '미국', 'America/New_York'),
    Stock('키오시아', '285A.T', 'JPY', '일본', 'Asia/Tokyo'),
    Stock('씨게이트', 'STX', 'USD', '미국', 'America/New_York'),
    Stock('웬디', 'WDC', 'USD', '미국', 'America/New_York'),
)

CACHE_SECONDS = 30.0
FETCH_TIMEOUT = 3.2
MAX_RESPONSE_BYTES = 180_000
_URLS = ('https://query1.finance.yahoo.com/v8/finance/chart/',
         'https://query2.finance.yahoo.com/v8/finance/chart/')
_CACHE_LOCK = threading.Lock()
_CACHE: tuple[float, str] | None = None


class StockQuoteError(ValueError):
    """시세가 제공되지 않을 때 사용자에게 보여줄 안전한 메시지."""


@dataclass(frozen=True)
class AfterMarketQuote:
    """본장 시세와 섞지 않는 네이버 장전/장후 시장의 별도 체결 정보."""
    price: float
    percent: float
    market_time: datetime
    session: str
    status: str
    exchange: str


@dataclass(frozen=True)
class DomesticQuoteMetadata:
    """검증된 국내 시세의 공급자·세션·지연 표기·시간외 정보를 보존."""
    provider: str
    market_status: str
    delay_minutes: int | None
    snapshot_time: datetime | None
    after_market: AfterMarketQuote | None = None


@dataclass(frozen=True)
class Quote:
    stock: Stock
    price: float
    previous_close: float
    percent: float
    market_time: datetime
    fetched_at: datetime
    domestic: DomesticQuoteMetadata | None = None


def _timezone(name: str):
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return timezone.utc


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        return None
    number = float(value)
    return number if math.isfinite(number) and number > 0 else None


def parse_chart(stock: Stock, payload: dict, *, now: datetime | None = None) -> Quote:
    """Yahoo chart metadata + daily close. 데이터 검증 실패 시 가짜 시세를 사용하지 않는다."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    try:
        result = payload['chart']['result'][0]
        meta = result['meta']
        if meta.get('currency') != stock.currency:
            raise StockQuoteError('통화 불일치')
        if meta.get('symbol', '').upper() != stock.ticker.upper():
            raise StockQuoteError('티커 불일치')
        price = _number(meta.get('regularMarketPrice'))
        trade_epoch = meta.get('regularMarketTime')
        if not isinstance(trade_epoch, (int, float)) or not math.isfinite(trade_epoch):
            raise StockQuoteError('시각 정보 누락')
        trade_utc = datetime.fromtimestamp(trade_epoch, tz=timezone.utc)
        age = (now - trade_utc).total_seconds()
        if age < -900 or age > 10 * 86400:
            raise StockQuoteError('최근 거래일 시세 없음')
        if price is None:
            raise StockQuoteError('현재가 누락')
        previous = _number(meta.get('previousClose'))
        if previous is None:
            # chartPreviousClose는 range=5d의 첫 시점 이전 가격일 수 있어 사용하지 않는다.
            timestamps = result.get('timestamp', [])
            closes = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
            pairs = [(int(t), _number(c)) for t, c in zip(timestamps, closes) if _number(c)]
            # 마지막 일봉 날짜가 현재 regularMarketTime과 같을 때만 바로 전 일봉을 기준으로 사용한다.
            tz = _timezone(stock.timezone_name)
            if len(pairs) >= 2 and datetime.fromtimestamp(pairs[-1][0], tz=tz).date() == trade_utc.astimezone(tz).date():
                previous = pairs[-2][1]
        if previous is None:
            raise StockQuoteError('전일 종가 누락')
        pct = (price / previous - 1) * 100
        if not math.isfinite(pct) or abs(pct) > 1000:
            raise StockQuoteError('등락률 데이터 오류')
        tz = _timezone(stock.timezone_name)
        return Quote(stock, price, previous, pct, trade_utc.astimezone(tz), now.astimezone(timezone(timedelta(hours=9))))
    except (KeyError, TypeError, IndexError, ValueError, OverflowError, OSError) as exc:
        if isinstance(exc, StockQuoteError):
            raise
        raise StockQuoteError('응답 데이터 오류') from exc


def fetch_yahoo_quote(stock: Stock, *, opener=urlopen, now: datetime | None = None) -> Quote:
    """고정된 HTTPS 시세 엔드포인트만 사용; 일시적 오류는 대체 Yahoo 호스트에서 재시도."""
    failure = None
    for base in _URLS:
        url = base + encode_component(stock.ticker, safe='.') + '?range=5d&interval=1d&includePrePost=false'
        request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; AngaeBotPersonal/0.4.2)',
                                        'Accept': 'application/json'}, method='GET')
        try:
            with opener(request, timeout=FETCH_TIMEOUT) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise StockQuoteError('응답 용량 제한 초과')
            result = json.loads(raw)
            return parse_chart(stock, result, now=now)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            failure = exc
            continue
    raise StockQuoteError('시세 제공처 연결 불가') from failure



# 지역별 무료 공개 페이지에서 실제 시세를 확인한다. 사용자 지정 URL은 허용하지 않는다.
_NAVER_BASIC = 'https://m.stock.naver.com/api/stock/{code}/basic'
_NAVER_POLLING = 'https://polling.finance.naver.com/api/realtime/domestic/stock/{code}'
_YAHOO_JAPAN = 'https://finance.yahoo.co.jp/quote/285A.T'
_RAKUTEN_JAPAN = 'https://www.rakuten-sec.co.jp/smartphone/market/info/pagecontent?pid=305&ric=285A.T'
_LOCAL_TIMEOUT = 2.8
_PAGE_MAX_BYTES = 2_000_000


def _request_json(url: str, *, opener=urlopen, timeout: float = _LOCAL_TIMEOUT) -> dict:
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0',
                                    'Accept': 'application/json',
                                    'Referer': 'https://m.stock.naver.com/'})
    with opener(request, timeout=timeout) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise StockQuoteError('응답 용량 제한 초과')
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise StockQuoteError('JSON 형식 오류')
    return obj


def _numeric_text(value: object, *, allow_zero: bool = False) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (float, int)):
        n = float(value)
    elif isinstance(value, str):
        cleaned = value.strip().replace(',', '').replace('%','').replace('−','-').replace('＋','+')
        try:
            n = float(cleaned)
        except ValueError:
            return None
    else:
        return None
    if math.isfinite(n) and (n >= 0 if allow_zero else n > 0):
        return n
    return None


def _parse_local_market_time(value: object, now: datetime, tz_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise StockQuoteError('거래일시 누락')
    text = value.strip()
    if re.fullmatch(r'\d{8}', text):
        timestamp = datetime.strptime(text, '%Y%m%d')
    else:
        try:
            timestamp = datetime.fromisoformat(text.replace('Z', '+00:00'))
        except ValueError as err:
            raise StockQuoteError('거래일시 형식 오류') from err
    tz = _timezone(tz_name)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=tz)
    timestamp = timestamp.astimezone(tz)
    age = (now - timestamp.astimezone(timezone.utc)).total_seconds()
    if age < -900 or age > 10 * 86400:
        raise StockQuoteError('최근 거래일 시세 없음')
    return timestamp


def _naver_delay_minutes(data: dict) -> int | None:
    """실제 네이버 지연 메타데이터(0분/분 단위)만 신뢰한다."""
    exchange = data.get('stockExchangeType')
    if not isinstance(exchange, dict):
        return None
    value = exchange.get('delayTime')
    if isinstance(value, bool):
        return None
    if isinstance(value, str) and value.isdecimal():
        value = int(value)
    return value if isinstance(value, int) and 0 <= value <= 120 else None


def _naver_snapshot_time(value: object) -> datetime | None:
    """폴링 서버 응답의 기준 시각(yyyyMMddHHmmss)을 검증하되 값이 없으면 임의로 생성하지 않는다."""
    if not isinstance(value, str) or not re.fullmatch(r'\d{14}', value):
        return None
    try:
        return datetime.strptime(value, '%Y%m%d%H%M%S').replace(tzinfo=timezone(timedelta(hours=9)))
    except ValueError:
        return None


def _naver_after_market(data: dict, stock: Stock, now: datetime, regular_time: datetime,
                        previous_close: float) -> AfterMarketQuote | None:
    """시간외 가격을 선택적으로 해석하고 잘못된 값·거래일은 본장 가격에 반영하지 않는다."""
    # NXT를 이름으로 확인할 수 있는 응답과 거래소 정보 없는 이전 호환 응답을 구분한다.
    raw = data.get('nxtOverMarketPriceInfo')
    exchange = 'NXT'
    if not isinstance(raw, dict):
        raw = data.get('overMarketPriceInfo')
        exchange = '거래소 미확인'
    if not isinstance(raw, dict):
        return None
    period = raw.get('tradingSessionType')
    if period not in ('AFTER_MARKET', 'BEFORE_MARKET', 'PRE_MARKET'):
        return None
    price = _numeric_text(raw.get('overPrice'))
    if price is None:
        return None
    try:
        at = _parse_local_market_time(raw.get('localTradedAt'), now, stock.timezone_name)
    except StockQuoteError:
        return None
    if at.date() < regular_time.date():
        return None
    if period == 'AFTER_MARKET' and at <= regular_time:
        # 본장 마감 전에 남은 과거 시간외 값을 최신 별도 체결가로 출력하지 않는다.
        return None
    pct = (price / previous_close - 1) * 100
    if not math.isfinite(pct) or not -99.9 < pct < 1000:
        return None
    # 네이버 제공 시간외 등락률이 있으면 별도 체결가와 정합성 확인.
    listed = _numeric_text(raw.get('fluctuationsRatio'), allow_zero=True)
    if listed is None and isinstance(raw.get('fluctuationsRatio'), str):
        try:
            listed = float(raw['fluctuationsRatio'].replace(',', '').replace('−', '-'))
        except ValueError:
            listed = None
    if listed is not None and math.isfinite(listed):
        direction = raw.get('compareToPreviousPrice')
        if isinstance(direction, dict):
            direction = direction.get('name')
        if isinstance(direction, str):
            if direction.upper() in ('FALLING', 'LOWER', 'DOWN'):
                listed = -abs(listed)
            elif direction.upper() in ('RISING', 'HIGHER', 'UP'):
                listed = abs(listed)
            elif direction.upper() in ('UNCHANGED', 'SAME', 'FLAT'):
                listed = 0.0
        if abs(listed - pct) > 0.35:
            return None
    status = raw.get('overMarketStatus')
    return AfterMarketQuote(price, pct, at,
                            '장후' if period == 'AFTER_MARKET' else '장전',
                            status.upper() if isinstance(status, str) else '', exchange)


def parse_naver_quote(stock: Stock, data: dict, *, now: datetime | None = None,
                      provider: str = '모바일', snapshot_time: datetime | None = None) -> Quote:
    """네이버 공개 JSON: 본장/시간외 분리, 가격·시각·지연 메타데이터 검증."""
    if stock.ticker not in ('005930.KS', '000660.KS'):
        raise StockQuoteError('네이버 국내 종목만 지원')
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if not isinstance(data, dict):
        raise StockQuoteError('네이버 시세 데이터 형식 오류')
    code = stock.ticker.split('.')[0]
    if 'itemCode' in data and str(data['itemCode']) != code:
        raise StockQuoteError('네이버 종목코드 불일치')
    if 'stockCode' in data and str(data['stockCode']) != code:
        raise StockQuoteError('네이버 종목코드 불일치')
    if 'symbolCode' in data and str(data['symbolCode']) != code:
        raise StockQuoteError('네이버 종목코드 불일치')
    price = _numeric_text(data.get('closePrice'))
    pct_value = _numeric_text(data.get('fluctuationsRatio'), allow_zero=True)
    raw_pct = data.get('fluctuationsRatio')
    # 음의 등락률은 부호가 있으므로 절댓값 유효성 검사와 별도로 읽는다.
    if pct_value is None and isinstance(raw_pct, (int, float, str)):
        try:
            parsed = float(str(raw_pct).strip().replace(',', '').replace('%','').replace('−','-'))
            if math.isfinite(parsed):
                pct_value = parsed
        except ValueError:
            pass
    if price is None or pct_value is None or not -99.9 < pct_value < 1000:
        raise StockQuoteError('네이버 가격/등락률 누락')
    direction = data.get('compareToPreviousPrice')
    if isinstance(direction, dict):
        direction = direction.get('name')
    if isinstance(direction, str):
        direction = direction.upper()
        if direction in ('FALLING','LOWER','DOWN'):
            pct_value = -abs(pct_value)
        elif direction in ('RISING','HIGHER','UP'):
            pct_value = abs(pct_value)
        elif direction in ('UNCHANGED','SAME','FLAT'):
            pct_value = 0.0
    trade_time = _parse_local_market_time(data.get('localTradedAt') or data.get('localDate'), now, stock.timezone_name)
    previous = price / (1 + pct_value / 100)
    if not math.isfinite(previous) or previous <= 0:
        raise StockQuoteError('전일가 계산 실패')
    market_status = data.get('marketStatus')
    market_status = market_status.upper() if isinstance(market_status, str) else ''
    meta = DomesticQuoteMetadata(
        provider=provider,
        market_status=market_status,
        delay_minutes=_naver_delay_minutes(data),
        snapshot_time=snapshot_time,
        after_market=_naver_after_market(data, stock, now, trade_time, previous))
    return Quote(stock, price, previous, pct_value, trade_time,
                 now.astimezone(timezone(timedelta(hours=9))), meta)


def _should_retry_mobile(stock: Stock, quote: Quote, now: datetime) -> bool:
    """KRX 폴링 데이터가 장중 오래된 때만 모바일 조회를 추가하여 불필요한 호출/배터리를 절약."""
    meta = quote.domestic
    if meta is None or meta.provider != '폴링':
        return False
    kst = now.astimezone(timezone(timedelta(hours=9)))
    during_krx = (kst.weekday() < 5 and (9, 0) <= (kst.hour, kst.minute) < (15, 30))
    if meta.market_status == 'OPEN':
        age = (now - quote.market_time).total_seconds()
        snapshot_age = ((now - meta.snapshot_time).total_seconds()
                        if meta.snapshot_time is not None else float('inf'))
        return age > 180 or snapshot_age > 180 or meta.delay_minutes not in (0, None)
    if during_krx and quote.market_time.date() < kst.date():
        return True
    return False


def fetch_naver_quote(stock: Stock, *, opener=urlopen, now: datetime | None = None) -> Quote:
    """폴링 우선, 장중 폴링 갱신이 오래되면 모바일 신규 데이터도 비교. 실패 시 Yahoo는 fetch_quote 담당."""
    if stock.market != '한국':
        raise StockQuoteError('국내 종목만 조회 가능')
    code = stock.ticker.partition('.')[0]
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    polling_quote = None
    for url, source in ((_NAVER_POLLING.format(code=code), '폴링'),
                        (_NAVER_BASIC.format(code=code), '모바일')):
        try:
            payload = _request_json(url, opener=opener)
            snapshot_time = _naver_snapshot_time(payload.get('time')) if source == '폴링' else None
            if 'datas' in payload:
                data = payload['datas']
                if not isinstance(data, list) or not data:
                    raise StockQuoteError('네이버 응답 목록 비어 있음')
                data = next((item for item in data if isinstance(item, dict) and
                             str(item.get('itemCode') or item.get('stockCode') or '') == code), None)
                if data is None:
                    raise StockQuoteError('네이버 시세 종목 식별 오류')
            else:
                data = payload
            quote = parse_naver_quote(stock, data, now=now, provider=source, snapshot_time=snapshot_time)
            if source == '폴링':
                if not _should_retry_mobile(stock, quote, now):
                    return quote
                polling_quote = quote
                continue
            if polling_quote is None or quote.market_time > polling_quote.market_time:
                return quote
            return polling_quote
        except (StockQuoteError, HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError, TypeError, IndexError):
            continue
    if polling_quote is not None:
        return polling_quote
    raise StockQuoteError('네이버 무료 시세 조회 불가')


class _VisibleText(HTMLParser):
    """스크립트/스타일 내용을 제외하고 Yahoo Japan 페이지의 표시 텍스트만 읽는다."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ignore = 0
        self.chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self.ignore += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript') and self.ignore:
            self.ignore -= 1

    def handle_data(self, text):
        if not self.ignore:
            piece = text.strip()
            if piece:
                self.chunks.append(piece)


def parse_yahoo_japan_quote(stock: Stock, html: str, *, now: datetime | None = None) -> Quote:
    """Yahoo Japan 본장: 날짜가 11/4 또는 15:30으로 보이는 두 UI 모두 지원한다."""
    if stock.ticker != '285A.T':
        raise StockQuoteError('키오시아 이외 일본 페이지 미지원')
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    parser = _VisibleText()
    parser.feed(html)
    visible = ' '.join(parser.chunks)
    if 'キオクシア' not in visible or '285A' not in visible:
        raise StockQuoteError('키오시아 종목 식별 실패')
    # 첫 공개 정규장 시세만 사용한다. 뒤쪽 '夜間PTS' 값은 이 정규장 헤더와 불일치한다.
    pattern = (r'(?P<price>[\d,]+(?:\.\d+)?)\s*前日比\s*'
               r'(?P<delta>[+\-−]\s*[\d,]+(?:\.\d+)?)\s*'
               r'\(\s*(?P<pct>[+\-−]?\d+(?:\.\d+)?)%\s*\)\s*'
               r'リアルタイム株価')
    match = re.search(pattern, visible[:40_000])
    if match is None:
        raise StockQuoteError('Yahoo Japan 본장 시세 구조 변경 또는 데이터 없음')
    price = _numeric_text(match.group('price'))
    try:
        pct = float(match.group('pct').replace('−', '-'))
        delta = float(match.group('delta').replace(',', '').replace(' ', '').replace('−', '-'))
    except ValueError as error:
        raise StockQuoteError('Yahoo Japan 숫자 오류') from error
    if price is None or not math.isfinite(pct) or not math.isfinite(delta):
        raise StockQuoteError('Yahoo Japan 숫자 오류')
    previous = price - delta
    if previous <= 0 or abs(delta / previous * 100 - pct) > 0.15:
        raise StockQuoteError('Yahoo Japan 전일비 정합성 불일치')
    # 페이지 업데이트에 따라 'リアルタイム株価 11/4'가 'リアルタイム株価 15:30'으로 바뀐다.
    # 시간만 있으면 정규장 상세의 '始値 ... (11/04)' 날짜를 사용한다.
    trail = visible[match.end():match.end() + 100]
    explicit = re.match(r'\s*(\d{1,2})/(\d{1,2})(?!\d)', trail)
    if explicit:
        month, day = int(explicit.group(1)), int(explicit.group(2))
    else:
        details_start = visible.find('株価詳細値')
        if details_start < 0:
            raise StockQuoteError('Yahoo Japan 거래일 증빙 누락')
        details = visible[details_start:details_start + 4000].split('夜間PTSについて', 1)[0]
        details_date = re.search(r'始値.{0,100}?(\d{1,2})/(\d{1,2})(?!\d)', details)
        if details_date is None:
            raise StockQuoteError('Yahoo Japan 거래일 증빙 누락')
        month, day = int(details_date.group(1)), int(details_date.group(2))
    tokyo = _timezone('Asia/Tokyo')
    local_now = now.astimezone(tokyo)
    try:
        trading_day = date(local_now.year, month, day)
        if trading_day > local_now.date() + timedelta(days=1):
            trading_day = date(local_now.year - 1, month, day)
        trade_time = datetime.combine(trading_day, dt_time(15, 30), tzinfo=tokyo)
    except ValueError as error:
        raise StockQuoteError('Yahoo Japan 거래일 날짜 오류') from error
    age = (now - trade_time.astimezone(timezone.utc)).total_seconds()
    if age > 10 * 86400:
        raise StockQuoteError('Yahoo Japan 시세 오래됨')
    if age < -15 * 3600:
        raise StockQuoteError('Yahoo Japan 거래일 미래 날짜')
    if trade_time > local_now:
        trade_time = local_now
    return Quote(stock, price, previous, pct, trade_time,
                 now.astimezone(timezone(timedelta(hours=9))))


def parse_rakuten_quote(stock: Stock, html: str, *, now: datetime | None = None) -> Quote:
    """라쿠텐 증권의 동경증권거래소 285A 본장 정보: PTS 제외/날짜·등락률 교차검증."""
    if stock.ticker != '285A.T':
        raise StockQuoteError('키오시아 이외 라쿠텐 시세 미지원')
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    p = _VisibleText()
    p.feed(html)
    text = ' '.join(p.chunks)
    if '285A' not in text[:12000] or 'キオクシア' not in text[:12000]:
        raise StockQuoteError('라쿠텐 종목 식별 실패')
    # 실제 공개 페이지 예시: 東証P 10,735.0 -610.0-5.38% 26/11/04 15:30 前終(11/02) 11,345.0
    # PTS/체결 정보와 구분하려고 '東証' 바로 뒤의 첫 시세만 선택한다.
    pattern = (r'東証[\wＰP]*\s*'
               r'(?P<price>[\d,]+(?:\.\d+)?)\s*'
               r'(?P<delta>[+\-−][\d,]+(?:\.\d+)?)\s*'
               r'(?P<pct>[+\-−]\d+(?:\.\d+)?)\s*%\s*'
               r'(?P<year>\d{2,4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})\s*'
               r'(?P<hour>\d{1,2}):(?P<minute>\d{2})')
    m = re.search(pattern, text[:12000])
    if m is None:
        raise StockQuoteError('라쿠텐 본장 시세 형식 오류')
    price = _numeric_text(m.group('price'))
    try:
        delta = float(m.group('delta').replace(',', '').replace('−','-'))
        pct = float(m.group('pct').replace('−','-'))
    except ValueError as error:
        raise StockQuoteError('라쿠텐 숫자 오류') from error
    if price is None or not math.isfinite(delta) or not math.isfinite(pct):
        raise StockQuoteError('라쿠텐 숫자 오류')
    previous = price - delta
    if previous <= 0 or abs(delta / previous * 100 - pct) > 0.15:
        raise StockQuoteError('라쿠텐 전일비 정합성 불일치')
    year = int(m.group('year'))
    if year < 100:
        year += 2000
    tz = _timezone('Asia/Tokyo')
    try:
        market_time = datetime(year, int(m.group('month')), int(m.group('day')),
                               int(m.group('hour')), int(m.group('minute')), tzinfo=tz)
    except ValueError as error:
        raise StockQuoteError('라쿠텐 거래일 형식 오류') from error
    age = (now - market_time.astimezone(timezone.utc)).total_seconds()
    if age < -900 or age > 10 * 86400:
        raise StockQuoteError('라쿠텐 최근 거래일 시세 없음')
    # '前終'은 전 거래일 종가다. 가격·등락률 자체와 큰 차이가 있으면 오염된 데이터다.
    footer = text[m.end():m.end() + 250]
    prev_match = re.search(r'前終\s*\([^)]*\)\s*([\d,]+(?:\.\d+)?)', footer)
    if prev_match:
        reported_prev = _numeric_text(prev_match.group(1))
        if reported_prev is None or abs(reported_prev - previous) > max(2.0, previous * 0.002):
            raise StockQuoteError('라쿠텐 전일 종가 불일치')
    return Quote(stock, price, previous, pct, market_time,
                 now.astimezone(timezone(timedelta(hours=9))))


def fetch_rakuten_quote(stock: Stock, *, opener=urlopen, now: datetime | None = None) -> Quote:
    """키오시아만 고정 HTTPS 공개 페이지 접근; 실제 데이터가 아닐 때 fail closed."""
    if stock.ticker != '285A.T':
        raise StockQuoteError('라쿠텐 조회는 키오시아만 지원')
    req = Request(_RAKUTEN_JAPAN, headers={'User-Agent': 'Mozilla/5.0',
                                          'Accept': 'text/html,application/xhtml+xml'}, method='GET')
    try:
        with opener(req, timeout=_LOCAL_TIMEOUT) as resp:
            raw = resp.read(_PAGE_MAX_BYTES + 1)
        if len(raw) > _PAGE_MAX_BYTES:
            raise StockQuoteError('페이지 용량 제한 초과')
        html = raw.decode('utf-8', errors='replace')
        if 'キオクシア' not in html:
            html = raw.decode('cp932', errors='replace')
        return parse_rakuten_quote(stock, html, now=now)
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, ValueError) as error:
        if isinstance(error, StockQuoteError):
            raise
        raise StockQuoteError('라쿠텐 연결 실패') from error


def fetch_yahoo_japan_quote(stock: Stock, *, opener=urlopen, now: datetime | None = None) -> Quote:
    if stock.ticker != '285A.T':
        raise StockQuoteError('허용된 일본 종목만 조회')
    request = Request(_YAHOO_JAPAN, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'})
    try:
        with opener(request, timeout=_LOCAL_TIMEOUT) as response:
            raw = response.read(_PAGE_MAX_BYTES + 1)
        if len(raw) > _PAGE_MAX_BYTES:
            raise StockQuoteError('페이지 용량 초과')
        return parse_yahoo_japan_quote(stock, raw.decode('utf-8', errors='replace'), now=now)
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, ValueError) as error:
        if isinstance(error, StockQuoteError):
            raise
        raise StockQuoteError('Yahoo Japan 시세 연결 실패') from error


def fetch_quote(stock: Stock, *, opener=urlopen, now: datetime | None = None) -> Quote:
    """한국: 네이버 2개 → Yahoo / 일본: Yahoo → Yahoo Japan / 미국: 기존 Yahoo 2개."""
    if stock.market == '한국':
        try:
            return fetch_naver_quote(stock, opener=opener, now=now)
        except StockQuoteError:
            # 네이버 장애 시 기존 Yahoo 가격을 표시하되 실시간 인증 정보가 없음을 명시.
            quote = fetch_yahoo_quote(stock, opener=opener, now=now)
            return replace(quote, domestic=DomesticQuoteMetadata('Yahoo 대체', '', None, None))
    if stock.ticker == '285A.T':
        # 기존 Yahoo Finance → Yahoo Japan 순서를 유지하고, 두 제공처 모두 실패할 때
        # 라쿠텐 증권의 공개 본장 시세(PTS 제외)로 마지막 보완한다.
        try:
            return fetch_yahoo_quote(stock, opener=opener, now=now)
        except StockQuoteError:
            try:
                return fetch_yahoo_japan_quote(stock, opener=opener, now=now)
            except StockQuoteError:
                return fetch_rakuten_quote(stock, opener=opener, now=now)
    return fetch_yahoo_quote(stock, opener=opener, now=now)


def _formatted_price(value: float, currency: str) -> str:
    if currency == 'USD':
        return f'${value:,.2f}'
    if currency == 'KRW':
        return f'{value:,.0f}원'
    if currency == 'JPY':
        return f'¥{value:,.1f}'
    raise StockQuoteError('지원되지 않는 통화')


def _domestic_status_text(item: Quote) -> str:
    """네이버 시세의 지연/마감 상태를 실제 메타데이터와 거래시각으로 표시."""
    meta = item.domestic
    when = item.market_time.strftime('%m/%d %H:%M:%S')
    if meta is None:
        # Yahoo 폴백 등 공급자를 보증하지 못하는 경우 실시간이라고 표시하지 않는다.
        return f'   └ KRX {when} · 지연 여부 미확인(대체 시세)'
    status = meta.market_status
    delta = (item.fetched_at - item.market_time).total_seconds()
    freshness = (0 <= delta <= 180)
    server_fresh = (meta.snapshot_time is not None and
                    -30 <= (item.fetched_at - meta.snapshot_time).total_seconds() <= 180)
    if status in ('CLOSE', 'CLOSED', 'END'):
        label = '장마감 종가'
    elif status == 'OPEN':
        if meta.provider == '폴링' and meta.delay_minutes == 0 and freshness and server_fresh:
            label = '네이버 실시간표시(지연 0분)'
        elif delta > 180:
            label = '시세 갱신 지연/최종 체결가'
        elif meta.delay_minutes is not None and meta.delay_minutes > 0:
            label = f'지연 {meta.delay_minutes}분 표기'
        else:
            label = '실시간 여부 미확인'
    elif status in ('BEFORE_OPEN', 'PRE_OPEN', 'PREPARE'):
        label = '개장 전 최종가'
    else:
        label = '시장상태 미확인(최종 체결가)'
    return f'   └ KRX {when} · {label} · 네이버 {meta.provider}'


def _domestic_after_text(item: Quote) -> str:
    """시간외 종목별 시세를 KRX 종가에 덮어쓰지 않으며 출처·거래소 불확실성을 표시."""
    meta = item.domestic
    aft = meta.after_market if meta is not None else None
    if aft is None:
        return ''
    when = aft.market_time.strftime('%m/%d %H:%M:%S')
    arrow = '▲' if aft.percent > 0.00001 else ('▽' if aft.percent < -0.00001 else '－')
    status = '거래 중' if aft.status == 'OPEN' else ('마감' if aft.status == 'CLOSE' else '상태 미확인')
    exchange = 'NXT' if aft.exchange == 'NXT' else '시간외(거래소 미확인)'
    return (f'   └ {exchange} {aft.session} {_formatted_price(aft.price, item.stock.currency)} '
            f'({arrow}{abs(aft.percent):.2f}%) · {when} · {status}')


def quote_line(item: Quote) -> str:
    arrow = '▲' if item.percent > 0.00001 else ('▽' if item.percent < -0.00001 else '－')
    body = f'{item.stock.name} : {_formatted_price(item.price, item.stock.currency)} ({arrow}{abs(item.percent):.2f}%)'
    if item.stock.market != '한국' or item.domestic is None:
        # 종전 Quote 생성자/테스트 호출에 대해서는 출력 형식을 변경하지 않는다.
        return body
    extra = _domestic_after_text(item)
    return body + '\n' + _domestic_status_text(item) + ('\n' + extra if extra else '')


def memory7_report(*, fetcher=fetch_quote, now: datetime | None = None, use_cache: bool = True) -> str:
    """8개 결과를 고정 순서로 표시. 실패 종목은 조회 불가로 명확히 처리한다."""
    global _CACHE
    started = time.monotonic()
    if use_cache and fetcher is fetch_quote:
        with _CACHE_LOCK:
            if _CACHE is not None and started - _CACHE[0] < CACHE_SECONDS:
                return _CACHE[1]
    # URL/종목은 사용자 인수로 추가하지 못하며 네트워크 제한은 각 요청 단위로 적용.
    def get_one(stock):
        try:
            return fetcher(stock)
        except (StockQuoteError, TimeoutError, OSError, ValueError):
            return None

    with ThreadPoolExecutor(max_workers=4, thread_name_prefix='AngaeBotStock') as pool:
        quotes = list(pool.map(get_one, WATCHLIST))
    lines = ['💾 메모리7 시세 요약']
    dates: dict[str, str] = {}
    success = 0
    latest_dates = {}
    for item in quotes:
        if item is not None:
            day = item.market_time.date()
            latest_dates[item.stock.market] = max(day, latest_dates.get(item.stock.market, day))
    for index, (stock, item) in enumerate(zip(WATCHLIST, quotes), start=1):
        if item is None:
            lines.append(f'{index}. {stock.name} : 조회 불가')
        else:
            success += 1
            line = quote_line(item)
            if item.market_time.date() < latest_dates[stock.market]:
                line += ' [거래일 ' + item.market_time.strftime('%m/%d') + ']'
            lines.append(f'{index}. {line}')
            dates[stock.market] = item.market_time.strftime('%m/%d')
    if not success:
        raise StockQuoteError('8개 종목 시세를 가져오지 못했습니다. 시세 제공처의 접속/요청 제한을 확인하세요.')
    # 서로 다른 현지 거래일을 '오늘'이라는 단일 날짜로 오해하지 않도록 분리한다.
    if dates:
        lines.append('현지 거래일: ' + ' · '.join(f'{m} {dates[m]}' for m in ('한국', '미국', '일본') if m in dates))
    if success < len(WATCHLIST):
        lines.append(f'※ {len(WATCHLIST)-success}종목 조회 실패. 값은 임의 보충하지 않았습니다.')
    lines.append('※ 네이버 금융(한국) / Yahoo Finance·Japan(미국·일본) 공개/지연 시세 가능 · 정규장 기준')
    lines.append('※ 5분 내 번호 1~8만 보내면 해당 종목의 5일·1개월·3개월 분석')
    result = '\n'.join(lines)
    if use_cache and fetcher is fetch_quote:
        with _CACHE_LOCK:
            _CACHE = (time.monotonic(), result)
    return result


def execute_stock_command(command: str, argument: str) -> str:
    if command == '주식' and argument.strip() == '메모리7':
        return memory7_report()
    if command == '메모리7' and not argument.strip():
        return memory7_report()
    raise StockQuoteError('사용법: 앙개야 주식 메모리7 (또는 앙개야 메모리7)')
