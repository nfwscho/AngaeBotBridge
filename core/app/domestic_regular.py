"""
앙개봇 국내 정규장 종가 검증 보조 모듈 — 전체 기능·보존 사항
1. 한국 네이버 장외 세션에서 closePrice가 장외 체결가로 바뀐 경우 15:30 정규장 종가를 별도 확인한다.
2. 기존 Yahoo 정규장 가격 검증 실패 시 네이버 KRX dayCandle 일봉의 종가 필드를 보조 기준으로 확인한다.
3. 삼성전자 005930 및 하이닉스 000660 고정 종목만 접근하며 임의 URL/티커/사용자 네트워크 입력을 사용하지 않는다.
4. 오늘 거래일과 동일한 YYYYMMDD 또는 YYYY-MM-DD 일봉만 허용하고 어제 종가를 오늘 종가로 위장하지 않는다.
5. 일봉 closePrice는 양수·유한 숫자이고 원 시세의 전일 기준가와 수익률 정합성이 있는 경우에만 사용한다.
6. 일봉 거래시각 15:30 KST는 거래소의 정규장 종가 기준시각을 뜻하며 분봉 실체결 시각이라고 주장하지 않는다.
7. 서버가 시세를 제공하지 않으면 정규 종가 미확인으로 처리하고 원래 장외 체결가는 별도로 보존한다.
8. API 최대 응답 180KB·3초 제한을 따르고 인증키, DB, 운영 .env, 기존 로그, Android Bridge를 건드리지 않는다.
9. 기존 주식 그룹, 메모리7, 일본·미국 시세 및 이전 검증·오류 처리 경로를 유지하며 테스트에서는 가상 데이터를 사용한다.
10. 다음날 00시 이후·주말에도 가장 최근 한국 정규장(15:30) 일봉 기준일은 실제 마지막 장외 체결일로 확인한다.
11. 다음 정규시장 거래일 08:00 KST 전까지만 직전 장외 종가를 유효한 마지막 시장가격으로 보며 거래일이 시작되면 예전 장외가격을 대표로 쓰지 않는다.
12. 당일/마지막 장외 체결일과 상이한 날짜의 일봉은 정규 종가로 인정하지 않고 KRX 데이터와 네이버 통합 장외가격을 혼합하지 않는다.
13. 종가 확인 실패 및 이전 성공한 시세는 로그/원본 Quote를 그대로 보존하며 날짜를 넘어간 시세 복구 과정도 모의 테스트로 재현한다.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, time, timezone, timedelta
from urllib.request import Request

_ENDPOINT = 'https://api.stock.naver.com/chart/domestic/item/{code}?periodType=dayCandle'
_KST = timezone(timedelta(hours=9))


def last_after_displayable(after, *, now: datetime) -> bool:
    """마지막 장후 체결이 아직 가장 최근 한국 시장 체결인지 보수적으로 판단한다.

    금요일 20시 체결은 토·일과 월요일 08시 전까지 마지막 체결로 간주한다.
    공휴일 달력은 추측하지 않으며 다음 평일 08시가 되면 과거 장외가를
    현재 대표가격으로 사용하지 않는다.
    """
    if after is None or after.session != '장후' or now.tzinfo is None:
        return False
    traded = after.market_time.astimezone(_KST)
    current = now.astimezone(_KST)
    age = (current - traded).total_seconds()
    if age < 0 or age > 4 * 86400 or traded.weekday() >= 5:
        return False
    if current.date() == traded.date():
        return True
    next_market_day = traded.date() + timedelta(days=1)
    while next_market_day.weekday() >= 5:
        next_market_day += timedelta(days=1)
    expiry = datetime.combine(next_market_day, time(8, 0), _KST)
    return current < expiry


def _value(raw):
    if isinstance(raw, bool):
        return None
    if isinstance(raw, str):
        try:
            raw = float(raw.strip().replace(',', ''))
        except ValueError:
            return None
    if not isinstance(raw, (float, int)):
        return None
    num = float(raw)
    return num if math.isfinite(num) and 0 < num < 1e10 else None


def parse_daily_regular(stock, payload, latest, *, now: datetime):
    """반드시 당일 일봉을 확인; 일봉 데이터가 불명확하면 반환하지 않는다."""
    if stock.market != '한국' or stock.ticker not in ('005930.KS','000660.KS'):
        return None
    records = payload if isinstance(payload, list) else []
    if isinstance(payload, dict):
        for key in ('priceInfos','priceInfo','prices','data','result'):
            value = payload.get(key)
            if isinstance(value, list):
                records = value
                break
            if isinstance(value, dict) and isinstance(value.get('priceInfos'), list):
                records = value['priceInfos']
                break
    # 00시 이후(특히 금요일 장후→토요일)에는 now 날짜로 KRX 일봉을
    # 검색하면 거래가 없으므로, 검증된 마지막 장후 *체결일*을 사용한다.
    meta = getattr(latest, 'domestic', None)
    after = getattr(meta, 'after_market', None) if meta is not None else None
    if after is not None and after.session == '장후':
        if not last_after_displayable(after, now=now):
            return None
        reference_day = after.market_time.astimezone(_KST).date()
    else:
        reference_day = now.astimezone(_KST).date()
    day = reference_day.strftime('%Y%m%d')
    matched = []
    for item in records:
        if not isinstance(item, dict):
            continue
        record_day = str(item.get('localDate') or item.get('tradedAt') or '').replace('-', '')
        if record_day != day:
            continue
        price = _value(item.get('closePrice'))
        if price is None or _value(latest.previous_close) is None:
            continue
        pct = (price / latest.previous_close - 1) * 100
        if not math.isfinite(pct) or not -99.9 < pct < 1000:
            continue
        matched.append((price, pct))
    if len(matched) != 1:
        return None
    stamp = datetime.combine(reference_day, time(15, 30), _KST)
    return (*matched[0], stamp, '네이버 KRX 일봉')


def fetch_daily_regular(stock, latest, *, opener, now: datetime, timeout: float, max_bytes: int,
                        user_agent: str):
    if stock.market != '한국' or stock.ticker not in ('005930.KS','000660.KS'):
        return None
    code = stock.ticker.split('.')[0]
    req = Request(_ENDPOINT.format(code=code),
                  headers={'User-Agent': user_agent,
                           'Accept': 'application/json',
                           'Referer': 'https://stock.naver.com/'},
                  method='GET')
    with opener(req, timeout=timeout) as response:
        raw = response.read(max_bytes+1)
    if len(raw) > max_bytes:
        raise ValueError('일봉 JSON 크기 초과')
    return parse_daily_regular(stock,json.loads(raw),latest,now=now)
