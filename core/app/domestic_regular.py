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
14. 2026-11-06 실측에서 Naver KRX dayCandle closePrice가 15:30 공식 정규장 종가와 다를 수 있어 단순 일봉 closePrice를 정규 종가로 승격하지 않는다.
15. Daum 공개 /api/quote/A{code}/days에서 11/06 삼성·하이닉스 공식 정규장 종가가 일치함을 검증했고, 해당 날짜/티커/전일 종가/가격 변동률을 재검증하여 별도 기준가로 사용한다.
16. Daum 일봉 date=YYYY-MM-DD 00:00:00은 일별 인덱스이므로 00:00 실거래로 표기하지 않고 정규장 기준시각 15:30으로 표시한다.
17. 네이버 dayCandle은 명시적 regularClosePrice 및 15:30 시간 증거가 없으면 장외 최종가가 섞일 수 있어 보수적으로 거부하고 기존 조회 실패 로그를 유지한다.
18. 공개 quote JSON만 고정한 2개 국내 티커의 HTTPS URL로 조회하고 사용자의 토큰/DB/.env/메모/AI/Android UI를 읽거나 수정하지 않는다.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, time, timezone, timedelta
from urllib.request import Request

_ENDPOINT = 'https://api.stock.naver.com/chart/domestic/item/{code}?periodType=dayCandle'
_DAUM_ENDPOINT = ('https://finance.daum.net/api/quote/A{code}/days'
                  '?symbolCode=A{code}&page=1&perPage=10&pagination=true')
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


def _reference_day(latest, now: datetime):
    """정규장 일봉 기준일은 현재 달력일이 아닌 검증된 마지막 장후 체결일."""
    meta = getattr(latest, 'domestic', None)
    after = getattr(meta, 'after_market', None) if meta is not None else None
    if after is not None and after.session == '장후':
        if not last_after_displayable(after, now=now):
            return None
        return after.market_time.astimezone(_KST).date()
    return now.astimezone(_KST).date()


def parse_daum_daily_regular(stock, payload, latest, *, now: datetime):
    """Daum 일별 종가를 KRX 15:30 기준가로 채택할 때 독립 검증."""
    if (stock.market != '한국' or stock.ticker not in ('005930.KS','000660.KS')
            or not isinstance(payload, dict)):
        return None
    day = _reference_day(latest, now)
    if day is None:
        return None
    code = 'A' + stock.ticker.split('.')[0]
    records = payload.get('data')
    if not isinstance(records, list) or len(records) > 100:
        return None
    matches = []
    for item in records:
        if not isinstance(item, dict) or item.get('symbolCode') != code:
            continue
        if item.get('exchangeCountry') not in (None, 'KOREA'):
            continue
        if item.get('currency') not in (None, 'KRW'):
            continue
        raw_day = item.get('date')
        if not isinstance(raw_day, str) or not raw_day.startswith(day.isoformat()):
            continue
        if len(raw_day) > 10 and raw_day[10] not in (' ', 'T'):
            continue
        price = _value(item.get('tradePrice'))
        previous = _value(item.get('prevClosingPrice'))
        base_previous = _value(latest.previous_close)
        if price is None or previous is None or base_previous is None:
            continue
        if abs(previous / base_previous - 1) > 0.003:
            continue  # 네이버 장외 응답과 다음금융의 전일 정규종가가 일치해야 한다.
        percent = (price / base_previous - 1) * 100
        if not -30.0 <= percent <= 30.0 or not math.isfinite(percent):
            continue
        reported_rate = item.get('changeRate')
        if isinstance(reported_rate, (int, float)) and math.isfinite(reported_rate):
            if abs(float(reported_rate) * 100 - percent) > 0.4:
                continue
        matches.append((price, percent))
    if len(matches) != 1:
        return None
    stamp = datetime.combine(day, time(15, 30), _KST)
    return (*matches[0], stamp, '다음금융 정규 일봉')


def fetch_daum_regular(stock, latest, *, opener, now: datetime, timeout: float,
                       max_bytes: int, user_agent: str):
    """공개 Daum 일별 확정 종가만 조회; 현재가 API(20시 최종가)는 절대 사용하지 않는다."""
    if stock.market != '한국' or stock.ticker not in ('005930.KS','000660.KS'):
        return None
    code = stock.ticker.split('.')[0]
    req = Request(_DAUM_ENDPOINT.format(code=code),
                  headers={'User-Agent': user_agent,
                           'Accept': 'application/json',
                           'Referer': f'https://finance.daum.net/quotes/A{code}'},
                  method='GET')
    with opener(req, timeout=timeout) as response:
        raw = response.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError('다음금융 정규 일봉 응답 크기 초과')
    return parse_daum_daily_regular(stock, json.loads(raw), latest, now=now)


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
    reference_day = _reference_day(latest, now)
    if reference_day is None:
        return None
    day = reference_day.strftime('%Y%m%d')
    matched = []
    for item in records:
        if not isinstance(item, dict):
            continue
        record_day = str(item.get('localDate') or item.get('tradedAt') or '').replace('-', '')
        if record_day != day:
            continue
        # Naver KRX dayCandle의 closePrice는 20:00 KRX 애프터 최종가로
        # 바뀔 수 있다. 15:30 정규가를 명시한 필드/시각이 없는 경우 거부.
        explicit_stamp = item.get('regularCloseAt')
        if not isinstance(explicit_stamp, str):
            continue
        try:
            checked = datetime.fromisoformat(explicit_stamp.replace('Z', '+00:00'))
        except ValueError:
            continue
        if checked.tzinfo is None:
            continue
        local = checked.astimezone(_KST)
        if local.date() != reference_day or not (15, 20) <= (local.hour, local.minute) <= (15, 35):
            continue
        price = _value(item.get('regularClosePrice'))
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
