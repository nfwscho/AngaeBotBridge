"""
앙개봇 미국 프리·애프터 시세 모듈 — 전체 기능 및 안전 제약
1. 미국 거래소 동부시간(뉴욕 IANA DST 적용) 04:00~09:30 프리, 09:30~16:00 정규, 16:00~20:00 애프터를 구별한다.
2. Yahoo Finance Chart 1일/1분봉 includePrePost=true에서 동일 티커·USD·거래량 있는 실제 체결분봉만 추출한다.
3. 프리·애프터 가격은 원래 정규장 시세를 덮지 않고 별도의 불변 데이터 구조로 반환한다.
4. 프리는 직전 정규장 종가, 애프터는 당일 정규장 마지막가와 비교해 등락률을 재계산한다.
5. 날짜·미래 거래·종목·통화·거래 세션·숫자·거래량·최신성·응답 크기를 검증한다.
6. Yahoo 실패 시 Nasdaq 공개 웹의 marketStatus와 secondaryData에 있는 장외 가격·거래시각을 보조적으로 활용한다.
7. 현재 거래일 이외의 오래된 애프터가를 현재가로 표시하지 않고, 장외 미제공 시 정규장 시세를 복제하지 않는다.
8. 공급자 실패/HTTP 제한은 기존 정규장 시세, DB, 인증, AI, 로그, 관심그룹, Android 배터리/UI에 영향을 주지 않는다.
9. 자동주문·상시 모니터링·추가 API 키·새 백그라운드 작업은 도입하지 않는다.
10. 단위 테스트를 위해 시각·HTTP opener·기준 정규장 시세를 주입한다.
11. 미국 프리장 초반 1일 차트가 전 거래일만 보유할 수 있으므로 Yahoo 5거래일 1분봉으로 최신 세션 거래를 검색한다.
12. 5거래일 분봉의 최대 수량과 응답 크기를 제한하고 당일 세션의 검증된 분봉만 추출해 오래된 가격을 재사용하지 않는다.
13. 장외 분봉이 비어도 Yahoo chart.meta에 명시된 preMarketPrice/postMarketPrice와 세션별 Unix 체결시각을 검증해 별도 보조 시세로 사용한다.
14. Yahoo 메타데이터는 가격·시각 모두 필요하고 같은 현지 거래일의 실제 프리/애프터 구간일 때만 허용한다.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.request import Request
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class SessionPrice:
    """정규장과 명확하게 구별되는 검증된 미국 장외 거래 가격."""
    session: str
    price: float
    percent: float
    market_time: datetime
    source: str


def session_of(local: datetime) -> str:
    """미국 주식 현지 시간 기준 장외 세션 종류. 09:30~16:00은 정규장."""
    if local.weekday() >= 5:
        return ''
    hhmm = (local.hour, local.minute)
    if (4, 0) <= hhmm < (9, 30):
        return '프리'
    if (16, 0) <= hhmm < (20, 0):
        return '애프터'
    return ''


def should_fetch(stock, now: datetime) -> bool:
    if stock.market != '미국' or stock.currency != 'USD':
        return False
    try:
        local = now.astimezone(ZoneInfo('America/New_York'))
    except ZoneInfoNotFoundError:
        return False  # DST 확인 불가: 정규장 시세만 유지
    # 정규장 동안에는 기존 시세를 그대로 사용해 호출 수와 카카오톡 지연을 늘리지 않는다.
    # 장외 장마감 후에도 같은 거래일의 최종 애프터 체결은 조회할 수 있다.
    return (local.weekday() < 5 and
            (bool(session_of(local)) or (20, 0) <= (local.hour, local.minute) <= (23, 59)))


def _positive(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    val = float(value)
    return val if math.isfinite(val) and 0 < val < 1e10 else None


def _session_price(stock, regular, now: datetime, traded: datetime,
                   price: float, session: str, source: str) -> SessionPrice | None:
    try:
        local_now = now.astimezone(ZoneInfo('America/New_York'))
    except ZoneInfoNotFoundError:
        return None
    if (traded.date() != local_now.date() or session_of(traded) != session
            or not 0 <= (now - traded).total_seconds() <= 20 * 3600):
        return None
    if session == '프리':
        reference = (regular.previous_close if regular.market_time.date() == traded.date()
                     else regular.price)
    else:
        if regular.market_time.date() != traded.date():
            return None
        reference = regular.price
    if reference <= 0:
        return None
    pct = (price / reference - 1) * 100
    if not math.isfinite(pct) or not -99.9 < pct < 1000:
        return None
    return SessionPrice(session, price, pct, traded, source)


def parse_yahoo(stock, payload: dict, regular, *, now: datetime) -> tuple[SessionPrice, ...]:
    """동일 종목의 1분봉 실제 거래량 우선, 메타 장외 체결시각으로 보완."""
    if stock.currency != 'USD' or stock.market != '미국':
        return ()
    try:
        record = payload['chart']['result'][0]
        meta = record['meta']
        if meta.get('currency') != 'USD' or str(meta.get('symbol', '')).upper() != stock.ticker.upper():
            return ()
    except (KeyError, IndexError, TypeError, ValueError):
        return ()
    try:
        bars = record['indicators']['quote'][0]
        stamps = record['timestamp']
        closes = bars['close']
        volumes = bars['volume']
        if not (isinstance(stamps, list) and isinstance(closes, list) and isinstance(volumes, list)
                and len(stamps) == len(closes) == len(volumes) and len(stamps) <= 6000):
            stamps, closes, volumes = (), (), ()
    except (KeyError, IndexError, TypeError, ValueError):
        stamps, closes, volumes = (), (), ()
    result = {}
    try:
        zone = ZoneInfo('America/New_York')
    except ZoneInfoNotFoundError:
        return ()
    for stamp, close, volume in zip(stamps, closes, volumes):
        if (isinstance(stamp, bool) or not isinstance(stamp, (int, float))
                or not math.isfinite(stamp) or _positive(close) is None
                or _positive(volume) is None):
            continue
        try:
            traded = datetime.fromtimestamp(stamp, timezone.utc).astimezone(zone)
        except (OSError, ValueError, OverflowError):
            continue
        session = session_of(traded)
        if not session:
            continue
        value = _session_price(stock, regular, now, traded, float(close), session, 'Yahoo 1분봉')
        if value is not None and (session not in result or traded > result[session].market_time):
            result[session] = value
    # chart.meta의 장외 필드를 사용하더라도 반드시 가격과 *실제 장외 체결시각*
    # 두 값이 함께 있고, 새 거래일·ET 세션 검증을 통과해야 한다.
    for session, price_key, time_key in (
        ('프리', 'preMarketPrice', 'preMarketTime'),
        ('애프터', 'postMarketPrice', 'postMarketTime'),
    ):
        value = _positive(meta.get(price_key))
        epoch = meta.get(time_key)
        if value is None or isinstance(epoch, bool) or not isinstance(epoch, (int, float)):
            continue
        if not math.isfinite(epoch):
            continue
        try:
            stamp = datetime.fromtimestamp(epoch, timezone.utc).astimezone(zone)
        except (OSError, OverflowError, ValueError):
            continue
        validated = _session_price(stock, regular, now, stamp, value, session, 'Yahoo 메타')
        if validated and (session not in result or stamp > result[session].market_time):
            result[session] = validated
    return tuple(result[name] for name in ('프리', '애프터') if name in result)


def parse_nasdaq(stock, data: dict, regular, *, now: datetime) -> tuple[SessionPrice, ...]:
    """나스닥 보조 세션의 명시된 장상태·티커·시각만 사용; 없는 값을 만들지 않는다."""
    if stock.market != '미국' or stock.currency != 'USD' or not isinstance(data, dict):
        return ()
    if str(data.get('symbol', '')).upper() != stock.ticker.upper():
        return ()
    status = str(data.get('marketStatus') or '').lower().replace('_', '-')
    session = ('프리' if status in ('pre-market', 'premarket')
               else '애프터' if status in ('after-hours', 'afterhours') else '')
    secondary = data.get('secondaryData')
    if not session or not isinstance(secondary, dict):
        return ()
    raw = secondary.get('lastSalePrice')
    if isinstance(raw, str):
        raw = raw.strip().replace('$', '').replace(',', '')
        try:
            raw = float(raw)
        except ValueError:
            return ()
    price = _positive(raw)
    stamp = secondary.get('lastTradeTimestamp')
    if price is None or not isinstance(stamp, str):
        return ()
    from .market import _nasdaq_local_time, StockQuoteError
    try:
        traded = _nasdaq_local_time(stamp, stock, now)
    except StockQuoteError:
        return ()
    value = _session_price(stock, regular, now, traded, price, session, '나스닥 웹')
    return (value,) if value is not None else ()


def fetch_yahoo(stock, regular, *, opener, now: datetime, timeout: float,
                max_bytes: int, user_agent: str) -> tuple[SessionPrice, ...]:
    """미국 허용 종목만 Yahoo 1분봉 조회, HTTP 차단 시 호출측이 정상 종가를 보존."""
    from .market import _URLS
    from urllib.parse import quote
    uri = (_URLS[0] + quote(stock.ticker, safe='.') +
           '?range=5d&interval=1m&includePrePost=true')
    req = Request(uri, headers={'User-Agent': user_agent, 'Accept': 'application/json'},
                  method='GET')
    with opener(req, timeout=timeout) as response:
        raw = response.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError('미국 장외 분봉 응답 크기 제한')
    return parse_yahoo(stock, json.loads(raw), regular, now=now)
