"""
앙개봇 미국 주식 네이버 장외 시세 공급 모듈 — 전체 기능과 안전 제약
1. 기존 Yahoo 정규장 시세와 분리하여 네이버 증권 해외 주식 공개 폴링 응답에서 프리/애프터 체결가만 수집한다.
2. 확인된 나스닥 종목은 Reuters code '.O'와 연결하며 티커 문자를 검증하고 외부 입력 URL/호스트는 사용하지 않는다.
3. 네이버 공개 폴링 /api/polling/worldstock/stock?reutersCodes= 를 우선 조회한다.
4. 폴링에 체결가가 없거나 차단되면 공개 종목 basic /api/securityService/stock/{reuters}/basic 을 보조 확인한다.
5. 자료의 reutersCode/symbolCode/itemCode 등 동일 종목코드가 명시적으로 일치해야만 가격을 인정한다.
6. 응답의 marketSessionType 또는 overMarketPriceInfo.tradingSessionType으로 프리·애프터 상태를 증명한다.
7. localTradedAt은 타임존이 명시된 거래시각만 수용하고 America/New_York 기준 거래일·시장시간을 검증한다.
8. 가격은 양수·유한값·USD만 수용하며 20시간 초과 과거 시세나 미래 체결·정규장 체결을 장외로 둔갑시키지 않는다.
9. 프리 등락률은 직전 정규장 대비, 애프터 등락률은 당일 정규장 대비로 계산한다.
10. 공급자의 응답 형식이 다르거나 가격이 없으면 반환값은 빈 튜플이며 정규장 가격을 임의 복사하지 않는다.
11. 모든 공급자 조회는 고정 HTTPS 호스트·짧은 타임아웃·응답 크기 제한을 사용하고 수집 결과를 DB/운영 로그에 저장하지 않는다.
12. 기존 인증/메모리7/관심종목 그룹/AI OFF/Android Bridge/배터리/원본 로그·에러 복구 경로를 변경하지 않는다.
13. 동일 네이버 호스트에서 HTTP 403/429가 확인되면 즉시 중단해 과도한 재시도·휴대폰 응답 지연을 방지한다.
14. 폴링 응답의 알려진 data/result 중첩 래퍼를 최대 32개 노드까지만 탐색해 실제 체결 객체를 확인한다.
15. DNS/타임아웃처럼 호스트 전체 연결이 어려운 경우에는 두 번째 API를 시도하지 않는다.
16. 동일 응답에서 명시적인 overMarketPriceInfo가 확인되면 루트 closePrice로 덮어써서 본장·장외를 혼동하지 않는다.
17. 공식 나스닥 상장 SPCX(스페이스X) 신규 티커를 공개 네이버 해외 프리·애프터 조회 허용종목에 추가한다.
18. NYSE 상장 LLY(일라이릴리)는 공식 Reuters RIC LLY.N만 허용하여 나스닥 .O를 임의 적용하거나 다른 종목을 혼동하지 않는다.
19. SPCX.O/LLY.N 모두 네이버 응답의 종목코드·현지 거래시각·명시적 세션 검증을 통과할 때만 프리·애프터 대표값으로 채택한다.
20. 지원 목록 외 종목·불확실한 코드·누락된 시간외 체결은 기존 정규장 시세 유지, 오류 로그/DB/Android/인증은 변경하지 않는다.
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime
from urllib.parse import quote as urlquote
from urllib.request import Request
from urllib.error import URLError
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .extended_sessions import SessionPrice, _session_price


# 2026년 11월 기준 공개 Nasdaq 등록 종목. 임의 NYSE 티커를 .O로 추측하지 않는다.
_NAVER_NASDAQ = frozenset({
    'MU', 'SKHY', 'SNDK', 'STX', 'WDC', 'NVDA', 'AAPL', 'MSFT',
    'GOOG', 'GOOGL', 'AMZN', 'META', 'AVGO', 'AMD', 'INTC',
    'ADBE', 'COST', 'NFLX', 'TSLA', 'SPCX',
})
# 검증된 뉴욕증권거래소 종목. 임의의 미확인 ticker.N을 생성하지 않는다.
_NAVER_NYSE = {'LLY': 'LLY.N'}
_POLLING = 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes='
_BASIC = 'https://stock.naver.com/api/securityService/stock/{reuters}/basic'
_NUMBER_RE = re.compile(r'^[+]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)$')


def reuters_code(stock) -> str:
    if stock.market != '미국' or stock.currency != 'USD':
        return ''
    if stock.ticker in _NAVER_NASDAQ:
        return stock.ticker + '.O'
    return _NAVER_NYSE.get(stock.ticker, '')


def _price(value) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.strip().replace(',', '').replace('$', '')
        if not _NUMBER_RE.fullmatch(value):
            return None
        value = float(value)
    if not isinstance(value, (int, float)):
        return None
    n = float(value)
    return n if math.isfinite(n) and 0 < n < 1e10 else None


def _session(value) -> str:
    key = re.sub(r'[^a-z]', '', str(value or '').lower())
    if key in ('premarket', 'beforemarket', 'pre'):
        return '프리'
    if key in ('aftermarket', 'postmarket', 'afterhours', 'post'):
        return '애프터'
    return ''


def _timestamp(value) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        return None
    try:
        return stamp.astimezone(ZoneInfo('America/New_York'))
    except (ValueError, OverflowError, ZoneInfoNotFoundError):
        return None


def _records(payload: dict, expected: str):
    """기본 시세와 폴링 데이터 구조 모두 지원하되 신원 필드의 일치를 필수로 한다."""
    if not isinstance(payload, dict):
        return ()
    queue = [payload]
    candidates = []
    visited = 0
    while queue and visited < 32:
        item = queue.pop(0)
        visited += 1
        if isinstance(item, list):
            queue.extend(value for value in item[:30] if isinstance(value, (list, dict)))
            continue
        if not isinstance(item, dict):
            continue
        identifiers = [item.get(k) for k in ('reutersCode', 'symbolCode', 'stockCode', 'itemCode', 'ticker')]
        provided = [str(v).upper() for v in identifiers if isinstance(v, str) and v]
        if provided and all(value in (expected, expected.split('.')[0]) for value in provided):
            candidates.append(item)
        for key in ('datas', 'data', 'items', 'result', expected):
            value = item.get(key)
            if isinstance(value, (list, dict)):
                queue.append(value)
    return tuple(candidates)


def parse_naver_extended(stock, payload: dict, regular, *, now: datetime) -> tuple[SessionPrice, ...]:
    """공급자 세션·거래시각·통화·가격 검증, 현재 거래일 장외 체결만 반환."""
    code = reuters_code(stock)
    if not code:
        return ()
    result = {}
    for item in _records(payload, code):
        currency = item.get('currencyType', item.get('currency'))
        if isinstance(currency, dict):
            currency = currency.get('name') or currency.get('code')
        if currency and currency != 'USD':
            continue
        candidates = []
        for name, default in (
            ('overMarketPriceInfo', ''),
            ('preMarketPriceInfo', '프리'),
            ('afterMarketPriceInfo', '애프터'),
            ('nxtOverMarketPriceInfo', ''),
        ):
            value = item.get(name)
            if isinstance(value, dict):
                period = _session(value.get('tradingSessionType') or value.get('marketSessionType')) or default
                if period:
                    candidates.append((period, value, ('overPrice', 'closePrice', 'lastPrice', 'price'), True))
        period = _session(item.get('marketSessionType') or item.get('tradingSessionType'))
        if period:
            candidates.append((period, item, ('closePrice', 'lastPrice', 'price'), False))
        verified_explicit = set()
        for session, value, keys, explicit in candidates:
            if not explicit and session in verified_explicit:
                continue  # 명시적인 장외 거래가 확인됐으면 루트(정규가 가능)로 대체 금지
            raw_price = next((_price(value[k]) for k in keys if _price(value.get(k)) is not None), None)
            if raw_price is None:
                continue
            traded = _timestamp(value.get('localTradedAt') or value.get('lastTradedAt') or value.get('lastTradeTimestamp'))
            if traded is None:
                continue
            verified = _session_price(stock, regular, now, traded, raw_price, session, '네이버 해외')
            if verified is not None:
                if explicit:
                    verified_explicit.add(session)
                if session not in result or traded > result[session].market_time:
                    result[session] = verified
    return tuple(result[key] for key in ('프리', '애프터') if key in result)


def fetch_naver_extended(stock, regular, *, opener, now: datetime,
                         timeout: float, max_bytes: int, user_agent: str) -> tuple[SessionPrice, ...]:
    """두 가지 고정된 네이버 시세 경로만 요청한다. 전체 실패는 호출자가 정규장 시세를 보존."""
    code = reuters_code(stock)
    if not code:
        return ()
    errors = []
    for uri in (_POLLING + urlquote(code, safe='.'), _BASIC.format(reuters=urlquote(code, safe='.'))):
        req = Request(uri, headers={'User-Agent': user_agent,
                                    'Accept': 'application/json',
                                    'Referer': 'https://stock.naver.com/'}, method='GET')
        try:
            with opener(req, timeout=timeout) as response:
                raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                raise ValueError('네이버 해외 응답 용량 초과')
            result = parse_naver_extended(stock, json.loads(raw), regular, now=now)
            if result:
                return result
        except (OSError, TimeoutError, ValueError) as e:
            errors.append(type(e).__name__ + (f' HTTP {e.code}' if hasattr(e, 'code') else ''))
            if getattr(e, 'code', None) in (403, 429) or isinstance(e, (TimeoutError, URLError)):
                break  # 권한 거부·요청 제한·네트워크 장애 시 동일 호스트에 다시 요청하지 않는다.
    if errors:
        raise ValueError('네이버 해외 공개 API 조회 실패: ' + ', '.join(errors))
    return ()
