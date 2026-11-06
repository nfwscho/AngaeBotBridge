"""
앙개봇 Python Core v0.5.8 — 메모리7·국내·해외 무료 주식 시세 전체 기능 설명
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
35. v0.5.8 미국 Yahoo 차트 요청은 표준 HTTP User-Agent로 전송하고 HTTP 403/429는 반복 호출하지 않는다.
36. Yahoo 미국 종목 조회 실패 시 공개 Nasdaq 종목 조회를 1회 보조 시도하며 요청 호스트/티커·응답 크기를 제한한다.
37. 나스닥 보조 응답의 종목코드·미국달러 가격·순증감·등락률·현지 거래시각을 모두 검증하여 원치 않는 다른 종목/통화/시장 혼동을 방지한다.
38. 보조 시세의 전일가와 등락률을 독립 재계산하고 오래된·미래·구조 불명 데이터는 거부한다.
39. 나스닥 웹 시세는 지연 여부 미확인으로 표기하며 실시간·정규장 체결 실시간으로 주장하지 않는다.
40. 모든 미국 종목 보조 조회 실패는 기존 조회 불가로 격리하고 기존 메모리7/관심그룹/번호/캐시·DB·로그·배터리·해외/국내 시세를 그대로 유지한다.
41. 원격 응답 내용/토큰/주소를 SQLite 또는 운영 로그에 신규 저장하지 않으며 공개 시세 제공자 실패 원인 코드는 진단 가능하게 유지한다.
42. 주식 주문·지속적 모니터링·새 앱 권한·유료 API/키는 추가하지 않는다.
43. v0.5.9 메모리7/관심그룹 목록에서는 가격·등락률을 한 줄로 표시하고 시장별 데이터 공급자·기준 거래시각·지연 상태를 하단에 통합한다.
44. 공급자/체결시각이 시장 안에서 서로 다르면 혼합 출처와 최신 거래시각(종목별 시각 상이)을 표시해 잘못된 단일 실시간 시세로 오인하지 않는다.
45. 기존 quote_line()의 기본 원문 상세 표시 및 KRX/NXT 장전·장후 가격 별도 표시, 30초 캐시, 기록, 번호, 예외 처리는 모두 보존한다.
46. 한국 네이버/미국 Yahoo·나스닥/일본 Yahoo Japan·라쿠텐 및 5일·1개월·3개월 분석, Android 배터리·UI·권한과 유료 API OFF를 변경하지 않는다.
43. v0.5.10 미국 Yahoo·나스닥 현재가가 모두 차단될 때 나스닥 과거 거래내역의 최근 확정 일봉 2건으로 종가·전일대비를 보완한다.
44. 나스닥 과거 일봉도 실패하면 독립된 네이버 해외 일봉 JSON 공급자를 마지막으로 시도한다(검증된 나스닥 상장 티커 한정).
45. 일봉 보조 시세는 거래일·종목·통화(USD)·정규장 마감 여부·전일 종가·수익률을 엄격히 검증하며 실시간으로 표시하지 않는다.
46. 실패 공급자별 HTTP/데이터 오류와 사용된 보조 공급자를 기존 서버 로그에 기록하되 토큰/원문/개인정보는 기록하지 않는다.
47. 한국 네이버 KRX/NXT·일본 키오시아·기존 메모리7/관심그룹·숫자 메뉴·배터리·전체 SQLite·AI/운영 로그는 보존한다.
48. 조회 실패가 전부인 경우에는 금액을 만들거나 직전 시세를 실시간인 양 표시하지 않고 종전 조회 불가를 유지한다.
26. 카카오톡 간결 시세 목록은 상승 🔺 +, 하락 ▽ -, 보합 ➖로 구분하며 기존 가격·등락률·출처·로그는 유지한다.
49. 미국 프리(04~09:30 ET)·정규(09:30~16 ET)·애프터(16~20 ET)를 Yahoo 1분봉/나스닥 보조 시세로 구분한다.
50. 미국 장외 시세는 당일 거래일·시간·USD·실거래량(야후) 및 명시된 세션(나스닥)을 검증하고 정규 시세와 분리한다.
51. 미국 장외 보조 조회 실패는 기존 무료 정규장 공급자 폴백·시세·오류 로그에 영향을 주지 않는다.
52. 네이버 한국 장외 체결은 정규장 응답 갱신시각과 별도로 검증해 프리/애프터 가격 누락을 방지한다.
53. 한국 KRX 장외 중 OPEN 응답을 KRX 본장 실시간으로 잘못 표기하지 않고 거래소 미확인 시 추정하지 않는다.
54. 메모리7/관심그룹 간결 목록과 단일 종목 상세에 프리·정규·애프터 시세를 명시한다.
55. 기존 DB·명령·UI·AI OFF·Android 배터리·인증·기존 운영 로그/시세 출처 표기를 유지한다.
56. 2026-11-06 한국 네이버 afterMarket closePrice가 시간외 체결가로 바뀌는 경우를 확인하고 정규장 종가로 오표기하지 않는다.
57. 한국 시간외 구간에서는 별도 Yahoo 정규장 종가를 시각·거래일 검증해 성공한 경우에만 정규 기준가로 표시한다.
58. 미국 장외는 네이버 해외 폴링/기본시세를 추가 조회하고 Yahoo 분봉·Nasdaq 공개 시세를 종전 장애 보조로 유지한다.
59. 미국 나스닥 SKHY ADR은 장외 전용 네이버 공급자에서만 허용하고 기존 해외 확정 일봉 검증 허용목록은 변경하지 않는다.
60. 운영 로그에는 공급자별 조회 실패/조회 성공 진단 코드를 추가하며 기존 US_QUOTE_FAILED 등의 로그를 보존한다.
61. 장외 미제공·정규장 종가 미확인 시 값을 꾸미지 않고 명시적으로 미확인을 출력한다.
62. Yahoo 정규 종가 불일치/장애 시 네이버 KRX 당일 일봉 종가를 독립 검증하고 전일 기준가와 비교해 복구한다.
63. 국내 네이버 root marketSessionType이 프리/애프터인데 overPriceInfo가 없어도 시각·상태 확인된 closePrice는 장외로만 표시한다.
64. 국내 프리장에서는 직전 정규장 종가의 독립 검증만 허용하고 당일 정규장 값은 아직 없는 것으로 처리한다.
65. 메모리7·관심그룹 기본 시세는 종목당 정확히 한 줄로 가격을 표시하고 프리/애프터 중 확인된 해당 세션 체결가를 대표값으로 선택한다.
66. 국내 애프터 등락률은 당일 정규장 종가, 국내 프리는 직전 정규장 종가를 기준으로 계산하고 전일 종가 대비 변동률과 구별한다.
67. 국내 기준 정규 종가 검증에 실패하면 장외 가격은 표시하지만 상승/하락률은 임의 계산하지 않고 기준가 미확인으로 표시한다.
68. 미국 장외 시세는 세션과 현지 거래일을 확인하고 프리/애프터 최신 체결값만 대표가격으로 사용하며 지연·실시간을 보증하지 않는다.
69. 상세보기(주식 메뉴 7번·메모리7 상세)는 기존 원본 Quote/시각·공급자·정규장/장외 가격을 여러 줄로 보여주고 간략 화면에는 반복하지 않는다.
70. 기존 1~8 번호 분석/메뉴/사용자 그룹/30초 기본 캐시 및 로그·DB·Android 하단 기능모듈·배터리·AI OFF를 보존한다.
71. 간결 시세 출처 행은 활성 프리/애프터 공급자의 실제 출처를 표시해 정규장 Yahoo 공급자와 혼동하지 않는다.
72. 구형 네이버 본장(15:30 확정)가와 별도 시간외 필드를 받는 경우도 현재 거래시간에는 장외 대표값과 정규장대비 상승률을 표시한다.
73. 시장별 간략 출처 및 최근 거래시각은 실제 선택된 국내 프리/애프터 체결과 미국 세션 체결 시각을 기준으로 표시한다.
74. 국내 장외 데이터는 현재 KST 거래일과 체결 날짜가 일치할 때만 대표 가격으로 사용해 이전 거래일 값을 당일 프리/애프터로 오표시하지 않는다.
75. 메모리7과 관심그룹의 한 줄 간략 시세에서 프리·애프터 명칭을 P/A 단일 문자로 표시하여 카카오톡 자동 줄바꿈을 최소화한다.
76. 메모리7 간략 요약은 공급자 설명을 상세보기로 이동하고 시장별 최신 현지시각 한 줄 및 짧은 주의문만 남겨 카카오톡 전체보기 접힘을 방지한다.
77. 메모리7 본문 9번 상세보기/상세보기 9번 간략보기는 1~8번 기존 종목분석과 5분 세션을 보존한다.
78. 미국 정규장 도중에는 이전 프리 체결가가 존재해도 현재 대표가격을 프리로 오표시하지 않는다.
79. 종목별 지연 거래일 꼬리표는 최신 검증 프리/애프터 시각을 기준으로 부착해 장외 당일가를 전일가로 잘못 표시하지 않는다.
80. 메모리7/관심그룹 간략 시세에서 상승 🔺+/하락 ▽-/보합 ➖의 화살표 뒤 공백 한 글자를 제거하여 좁은 카카오톡 말풍선의 P/A 줄바꿈을 방지하고 상세 시세 형식은 유지한다.
"""
from __future__ import annotations

import json
import logging
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
_YAHOO_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
_NASDAQ_QUOTE = 'https://api.nasdaq.com/api/quote/{ticker}/info?assetclass=stocks'
_NASDAQ_DAILY = 'https://api.nasdaq.com/api/quote/{ticker}/historical?assetclass=stocks&limit=10'
_NAVER_US_DAILY = 'https://api.stock.naver.com/chart/foreign/item/{reuters}?periodType=dayCandle'
# 개별 티커의 상장 거래소를 추측하지 않는다. 확인 가능한 나스닥 상장 종목만 해외 차트에 연결한다.
_NAVER_NASDAQ_SYMBOLS = frozenset({'MU','SNDK','WDC','STX','NVDA','AAPL','MSFT','GOOGL','GOOG','AMZN','META','TSLA','AVGO','INTC','AMD','ADBE','COST','NFLX'})
_US_TICKER_RE = re.compile(r'^[A-Z]{1,5}(?:-[A-Z])?$')
_MARKET_LOG = logging.getLogger(__name__)
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
    market_session: str = ''
    regular_price: float | None = None
    regular_percent: float | None = None
    regular_time: datetime | None = None
    regular_source: str = ''


@dataclass(frozen=True)
class Quote:
    stock: Stock
    price: float
    previous_close: float
    percent: float
    market_time: datetime
    fetched_at: datetime
    domestic: DomesticQuoteMetadata | None = None
    source: str = ''
    extended: tuple = ()


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
    """기존 Yahoo 2호스트 + 명확한 403/429 요청 제한 존중, 엄격한 가격 검증."""
    failure = None
    for base in _URLS:
        url = base + encode_component(stock.ticker, safe='.') + '?range=5d&interval=1d&includePrePost=false'
        request = Request(url, headers={'User-Agent': _YAHOO_USER_AGENT,
                                        'Accept': 'application/json'}, method='GET')
        try:
            with opener(request, timeout=FETCH_TIMEOUT) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise StockQuoteError('응답 용량 제한 초과')
            result = json.loads(raw)
            return parse_chart(stock, result, now=now)
        except HTTPError as exc:
            failure = exc
            # 액세스 거부/요청 제한을 단순 네트워크 장애로 보고 두 번 연속 요청하지 않는다.
            if exc.code in (403, 429):
                break
        except (URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            failure = exc
    if isinstance(failure, HTTPError):
        raise StockQuoteError(f'Yahoo HTTP {failure.code}') from failure
    raise StockQuoteError('시세 제공처 연결 불가') from failure


def _nasdaq_number(value: object, *, signed: bool = False) -> float | None:
    """나스닥 표시 숫자만 처리; 통화·HTML·무한대·음수 현재가는 차단."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (float, int)):
        result = float(value)
    elif isinstance(value, str):
        clean = value.strip().replace(',', '').replace('$', '').replace('%', '').replace('−', '-')
        if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d+)?|\.\d+)', clean):
            return None
        result = float(clean)
    else:
        return None
    if not math.isfinite(result) or abs(result) > 1e10:
        return None
    return result if signed or result > 0 else None


def _nasdaq_local_time(value: object, stock: Stock, now: datetime) -> datetime:
    """나스닥 공개 웹의 거래시각을 미국 동부 거래소 기준으로 해석; 날짜만 있으면 거부."""
    if not isinstance(value, str) or not value.strip():
        raise StockQuoteError('나스닥 거래시각 누락')
    raw = value.strip()
    parsed = None
    try:
        parsed = datetime.fromisoformat(raw.replace('Z', '+00:00'))
    except ValueError:
        pass
    if parsed is None:
        raw = re.sub(r'\s*\(?\b(?:ET|EST|EDT)\)?\s*$', '', raw, flags=re.IGNORECASE).strip()
        for fmt in ('%b %d, %Y %I:%M %p', '%b %d, %Y %I:%M:%S %p',
                    '%b %d, %Y %H:%M:%S', '%b %d, %Y %H:%M',
                    '%b %d %Y %I:%M %p'):
            try:
                parsed = datetime.strptime(raw, fmt)
                break
            except ValueError:
                pass
    if parsed is None:
        raise StockQuoteError('나스닥 거래시각 형식 불명')
    local = parsed.replace(tzinfo=_timezone(stock.timezone_name)) if parsed.tzinfo is None else parsed.astimezone(_timezone(stock.timezone_name))
    delta = (now - local.astimezone(timezone.utc)).total_seconds()
    if delta < -900 or delta > 10 * 86400:
        raise StockQuoteError('나스닥 거래시각이 오래되었거나 미래입니다.')
    return local


def parse_nasdaq_quote(stock: Stock, payload: dict, *, now: datetime | None = None) -> Quote:
    """공개 나스닥 웹 JSON에서 동일 티커·정확한 정규 시세만 안전하게 파싱한다."""
    if stock.market != '미국' or stock.currency != 'USD' or not _US_TICKER_RE.fullmatch(stock.ticker):
        raise StockQuoteError('나스닥 미국 종목만 지원합니다.')
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise StockQuoteError('기준시각 시간대 정보 누락')
    try:
        if not isinstance(payload, dict):
            raise StockQuoteError('나스닥 JSON 형식 오류')
        data = payload['data']
        if not isinstance(data, dict) or str(data.get('symbol', '')).upper() != stock.ticker:
            raise StockQuoteError('나스닥 티커 불일치')
        if data.get('assetClass') not in (None, '', 'STOCKS'):
            raise StockQuoteError('나스닥 자산유형 불일치')
        info = data['primaryData']
        if not isinstance(info, dict):
            raise StockQuoteError('나스닥 현재가 정보 누락')
        price = _nasdaq_number(info.get('lastSalePrice'))
        change = _nasdaq_number(info.get('netChange'), signed=True)
        pct_published = _nasdaq_number(info.get('percentageChange'), signed=True)
        if price is None or change is None or pct_published is None:
            raise StockQuoteError('나스닥 가격/전일비 누락')
        previous = price - change
        if previous <= 0 or not math.isfinite(previous):
            raise StockQuoteError('나스닥 전일가 오류')
        pct_computed = (price / previous - 1.0) * 100.0
        if abs(pct_computed - pct_published) > 0.20 or abs(pct_computed) > 1000:
            raise StockQuoteError('나스닥 가격/등락률 정합성 오류')
        local = _nasdaq_local_time(info.get('lastTradeTimestamp'), stock, now)
        result = Quote(stock, price, previous, pct_computed, local,
                       now.astimezone(timezone(timedelta(hours=9))), source='나스닥 웹')
        from .extended_sessions import parse_nasdaq
        return replace(result, extended=parse_nasdaq(stock, data, result, now=now))
    except (KeyError, TypeError, IndexError, ValueError, OverflowError) as exc:
        if isinstance(exc, StockQuoteError):
            raise
        raise StockQuoteError('나스닥 시세 데이터 오류') from exc


def fetch_nasdaq_quote(stock: Stock, *, opener=urlopen, now: datetime | None = None) -> Quote:
    """Yahoo 장애 시에만 호출하는 미인증 공개 웹 JSON 보조 경로(공식 보장 API 아님)."""
    if stock.market != '미국' or stock.currency != 'USD' or not _US_TICKER_RE.fullmatch(stock.ticker):
        raise StockQuoteError('나스닥 미국 종목만 지원합니다.')
    uri = _NASDAQ_QUOTE.format(ticker=stock.ticker)
    req = Request(uri, headers={'User-Agent': _YAHOO_USER_AGENT,
                                'Accept': 'application/json, text/plain, */*',
                                'Accept-Language': 'en-US,en;q=0.9',
                                'Origin': 'https://www.nasdaq.com',
                                'Referer': 'https://www.nasdaq.com/'}, method='GET')
    try:
        with opener(req, timeout=FETCH_TIMEOUT) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise StockQuoteError('나스닥 응답 용량 초과')
        data = json.loads(raw)
        return parse_nasdaq_quote(stock, data, now=now)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as error:
        if isinstance(error, StockQuoteError):
            raise
        if isinstance(error, HTTPError):
            raise StockQuoteError(f'나스닥 HTTP {error.code}') from error
        raise StockQuoteError('나스닥 공개 시세 조회 불가') from error



def _us_daily_quote(stock: Stock, records: object, *, now: datetime, source: str,
                    date_field: str, price_field: str, formats: tuple[str, ...]) -> Quote:
    """완료된 미 증시 일봉 두 건만 종가로 사용; 임의 시각·가격·등락률 보간을 금지."""
    if stock.market != '미국' or stock.currency != 'USD' or not _US_TICKER_RE.fullmatch(stock.ticker):
        raise StockQuoteError('미국 일봉은 검증된 미국 티커만 지원')
    if now.tzinfo is None:
        raise StockQuoteError('일봉 기준 시간대 누락')
    if not isinstance(records, list):
        raise StockQuoteError('미국 일봉 목록 형식 오류')
    local_now = now.astimezone(_timezone(stock.timezone_name))
    values: dict[date, float] = {}
    for row in records[:160]:
        if not isinstance(row, dict):
            continue
        raw_date = row.get(date_field)
        if not isinstance(raw_date, str):
            continue
        trade_day = None
        for fmt in formats:
            try:
                trade_day = datetime.strptime(raw_date,fmt).date()
                break
            except ValueError:
                continue
        if trade_day is None or trade_day > local_now.date():
            continue
        if trade_day == local_now.date() and local_now.time() < dt_time(16,15):
            # 장중 미확정 종가 또는 정규장 직후 미완성 데이터는 절대 사용하지 않는다.
            continue
        price = _nasdaq_number(row.get(price_field))
        if price is None:
            continue
        if trade_day in values and abs(values[trade_day] - price) > 1e-8:
            raise StockQuoteError('같은 거래일의 미국 종가가 서로 다릅니다.')
        values[trade_day] = price
    days = sorted(values, reverse=True)
    if len(days) < 2:
        raise StockQuoteError('미국 정규장 확정 종가가 2건 미만입니다.')
    latest, previous_day = days[:2]
    if (local_now.date()-latest).days > 10 or (latest-previous_day).days > 10:
        raise StockQuoteError('미국 종가 거래일이 너무 오래되었습니다.')
    price, prev_price = values[latest], values[previous_day]
    change = (price / prev_price - 1.0) * 100
    if not math.isfinite(change) or abs(change) > 1000:
        raise StockQuoteError('미국 종가 등락률 오류')
    market_time = datetime.combine(latest, dt_time(16, 0), tzinfo=_timezone(stock.timezone_name))
    return Quote(stock, price, prev_price, change, market_time,
                 now.astimezone(timezone(timedelta(hours=9))),source=source)


def parse_nasdaq_daily_quote(stock: Stock, payload: dict, *, now: datetime | None = None) -> Quote:
    """Nasdaq 공개 종목 과거 거래내역의 일별 종가(정규장 종료 후)만 사용한다."""
    now = now or datetime.now(timezone.utc)
    if not isinstance(payload,dict) or not isinstance(payload.get('data'),dict):
        raise StockQuoteError('나스닥 과거 시세 응답 형식 오류')
    data=payload['data']
    if data.get('symbol') not in (None, '', stock.ticker):
        raise StockQuoteError('나스닥 과거 시세 티커 불일치')
    table=data.get('tradesTable')
    if not isinstance(table,dict):
        raise StockQuoteError('나스닥 과거 거래내역이 없습니다.')
    return _us_daily_quote(stock,table.get('rows'),now=now,source='나스닥 확정 종가',
                           date_field='date',price_field='close',formats=('%m/%d/%Y',))


def fetch_nasdaq_daily_quote(stock: Stock, *, opener=urlopen, now: datetime | None = None) -> Quote:
    """공개 Nasdaq historical 일봉 대체 경로. API 사용은 보장되지 않는다."""
    if stock.market != '미국' or stock.currency != 'USD' or not _US_TICKER_RE.fullmatch(stock.ticker):
        raise StockQuoteError('나스닥 미국 종목만 지원')
    req = Request(_NASDAQ_DAILY.format(ticker=stock.ticker),
                  headers={'User-Agent': _YAHOO_USER_AGENT,
                           'Accept': 'application/json, text/plain, */*',
                           'Accept-Language': 'en-US,en;q=0.9',
                           'Origin': 'https://www.nasdaq.com',
                           'Referer': 'https://www.nasdaq.com/'}, method='GET')
    try:
        with opener(req,timeout=FETCH_TIMEOUT) as response:
            raw=response.read(MAX_RESPONSE_BYTES+1)
        if len(raw)>MAX_RESPONSE_BYTES:
            raise StockQuoteError('나스닥 과거 시세 응답 용량 초과')
        return parse_nasdaq_daily_quote(stock,json.loads(raw),now=now)
    except (HTTPError,URLError,TimeoutError,OSError,ValueError,json.JSONDecodeError) as e:
        if isinstance(e,StockQuoteError):
            raise
        if isinstance(e,HTTPError):
            raise StockQuoteError(f'나스닥 일봉 HTTP {e.code}') from e
        raise StockQuoteError('나스닥 일봉 조회 불가') from e


def parse_naver_us_daily_quote(stock: Stock,payload: object,*,now: datetime | None=None) -> Quote:
    """Naver 해외 종목의 확정된 USD 일봉만 검사. 잘못된 상장거래소는 조회하지 않는다."""
    now=now or datetime.now(timezone.utc)
    if stock.ticker not in _NAVER_NASDAQ_SYMBOLS or stock.market!='미국' or stock.currency!='USD':
        raise StockQuoteError('네이버 해외 일봉 미지원 종목')
    code=stock.ticker+'.O'
    if isinstance(payload,dict):
        for key in ('reutersCode','itemCode'):
            if payload.get(key) not in (None,'',code,stock.ticker):
                raise StockQuoteError('네이버 해외 일봉 종목코드 불일치')
        rows=payload.get('priceInfos')
        if rows is None: rows=payload.get('priceInfoList')
    else:
        rows=payload
    return _us_daily_quote(stock,rows,now=now,source='네이버 해외 확정 종가',
                           date_field='localDate',price_field='closePrice',
                           formats=('%Y%m%d','%Y-%m-%d'))


def fetch_naver_us_daily_quote(stock: Stock,*,opener=urlopen,now: datetime | None=None) -> Quote:
    """나스닥 상장 티커를 사전 허용목록으로 제한한 네이버 해외 일봉 보조 조회."""
    if stock.ticker not in _NAVER_NASDAQ_SYMBOLS or stock.market!='미국' or stock.currency!='USD':
        raise StockQuoteError('네이버 해외 일봉 미지원 종목')
    req=Request(_NAVER_US_DAILY.format(reuters=stock.ticker+'.O'),
                headers={'User-Agent':_YAHOO_USER_AGENT,'Accept':'application/json',
                         'Referer':'https://m.stock.naver.com/'}, method='GET')
    try:
        with opener(req,timeout=FETCH_TIMEOUT) as response:
            raw=response.read(MAX_RESPONSE_BYTES+1)
        if len(raw)>MAX_RESPONSE_BYTES:
            raise StockQuoteError('네이버 해외 일봉 응답 용량 초과')
        return parse_naver_us_daily_quote(stock,json.loads(raw),now=now)
    except (HTTPError,URLError,TimeoutError,OSError,ValueError,json.JSONDecodeError) as e:
        if isinstance(e,StockQuoteError):
            raise
        if isinstance(e,HTTPError):
            raise StockQuoteError(f'네이버 해외 일봉 HTTP {e.code}') from e
        raise StockQuoteError('네이버 해외 일봉 조회 불가') from e


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
    # localTradedAt은 정규장 체결시각이 아니라 장외 응답 갱신시각일 수 있다.
    # 따라서 두 타임스탬프의 선후 관계가 아닌 실제 장외 시간대·날짜를 확인한다.
    hhmm = (at.hour, at.minute)
    if period == 'AFTER_MARKET' and not (15, 40) <= hhmm <= (20, 0):
        return None
    if period in ('BEFORE_MARKET', 'PRE_MARKET') and not (8, 0) <= hhmm <= (8, 50):
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
    session_name = str(data.get('marketSessionType') or '').lower()
    after_quote = _naver_after_market(data, stock, now, trade_time, previous)
    # 네이버 통합 시세가 marketSessionType=afterMarket/preMarket일 때는
    # closePrice 자체가 해당 장외 세션 가격일 수 있다. overPriceInfo 미제공 시
    # 본장 종가로 오표시하지 않고 확인 가능한 세션 시각의 장외가로만 인식한다.
    if after_quote is None and trade_time.weekday() < 5:
        hhmm = (trade_time.hour, trade_time.minute)
        if session_name in ('aftermarket', 'after_market') and (15, 40) <= hhmm <= (20, 0):
            after_quote = AfterMarketQuote(price, pct_value, trade_time, '장후',
                                           market_status, '거래소 미확인')
        elif session_name in ('premarket', 'pre_market', 'beforemarket', 'before_market') and (8, 0) <= hhmm <= (8, 50):
            after_quote = AfterMarketQuote(price, pct_value, trade_time, '장전',
                                           market_status, '거래소 미확인')
    meta = DomesticQuoteMetadata(
        provider=provider,
        market_status=market_status,
        delay_minutes=_naver_delay_minutes(data),
        snapshot_time=snapshot_time,
        after_market=after_quote,
        market_session=session_name)
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
        return replace(parse_rakuten_quote(stock, html, now=now), source='라쿠텐 공개 시세')
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
        return replace(parse_yahoo_japan_quote(stock, raw.decode('utf-8', errors='replace'), now=now), source='Yahoo Japan')
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, ValueError) as error:
        if isinstance(error, StockQuoteError):
            raise
        raise StockQuoteError('Yahoo Japan 시세 연결 실패') from error


def fetch_quote(stock: Stock, *, opener=urlopen, now: datetime | None = None) -> Quote:
    """한국: 네이버 2개 → Yahoo / 일본: Yahoo → Yahoo Japan / 미국: 기존 Yahoo 2개."""
    if stock.market == '한국':
        try:
            quote = fetch_naver_quote(stock, opener=opener, now=now)
            meta = quote.domestic
            # afterMarket 단계의 Naver closePrice는 15:30 KRX 종가가 아닌
            # 시간외 마지막 체결가일 수 있다. 일치하는 시간외 응답을 정규가로 표시 금지.
            if meta is not None and meta.market_session in ('aftermarket', 'after_market',
                                                             'premarket', 'pre_market', 'beforemarket', 'before_market'):
                is_pre = meta.market_session in ('premarket', 'pre_market', 'beforemarket', 'before_market')
                try:
                    regular = fetch_yahoo_quote(stock, opener=opener, now=now)
                    local_time = regular.market_time.astimezone(_timezone(stock.timezone_name))
                    date_ok = ((0 < (quote.market_time.date() - local_time.date()).days <= 4)
                               if is_pre else local_time.date() == quote.market_time.date())
                    if date_ok and (15, 20) <= (local_time.hour, local_time.minute) <= (15, 35):
                        meta = replace(meta, regular_price=regular.price,
                                       regular_percent=regular.percent,
                                       regular_time=local_time, regular_source='Yahoo Finance')
                        _MARKET_LOG.info('KRX_REGULAR_CLOSE_RECOVERED ticker=%s provider=Yahoo',stock.ticker)
                    else:
                        _MARKET_LOG.info('KRX_REGULAR_CLOSE_UNVERIFIED ticker=%s reason=market_time',stock.ticker)
                except StockQuoteError as e:
                    _MARKET_LOG.info('KRX_REGULAR_CLOSE_UNAVAILABLE ticker=%s reason=%s',stock.ticker,e)
                if meta.regular_price is None and not is_pre:
                    # Yahoo 현재가가 장외 세션과 섞인 경우 KRX 당일 일봉의 '종가'를 확인.
                    from .domestic_regular import fetch_daily_regular
                    try:
                        result = fetch_daily_regular(stock, quote, opener=opener,
                                                     now=now or datetime.now(timezone.utc),
                                                     timeout=FETCH_TIMEOUT,
                                                     max_bytes=MAX_RESPONSE_BYTES,
                                                     user_agent=_YAHOO_USER_AGENT)
                        if result:
                            reg_price, reg_pct, reg_time, reg_source = result
                            meta = replace(meta, regular_price=reg_price, regular_percent=reg_pct,
                                           regular_time=reg_time, regular_source=reg_source)
                            _MARKET_LOG.info('KRX_REGULAR_CLOSE_RECOVERED ticker=%s provider=NaverDaily',
                                             stock.ticker)
                    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as e:
                        _MARKET_LOG.info('KRX_REGULAR_CLOSE_DAILY_UNAVAILABLE ticker=%s reason=%s',
                                         stock.ticker, type(e).__name__)
                quote = replace(quote, domestic=meta)
            return quote
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
    if stock.market == '미국':
        errors=[]
        now_us = now or datetime.now(timezone.utc)
        for supplier, lookup in (('Yahoo',fetch_yahoo_quote),
                                 ('Nasdaq info',fetch_nasdaq_quote),
                                 ('Nasdaq daily',fetch_nasdaq_daily_quote),
                                 ('Naver overseas daily',fetch_naver_us_daily_quote)):
            try:
                quote=lookup(stock,opener=opener,now=now)
                from .extended_sessions import fetch_yahoo, session_of, should_fetch
                # 기존 Nasdaq 일봉/보조 복구는 추가 요청 없이 유지한다.
                # 정규장 Yahoo 성공 시에는 마감 후에도 최종 애프터를 확인할 수 있고,
                # 나머지 공급자 복구 시에는 *실제 장외 거래시간*에만 추가 호출한다.
                us_extended_active = bool(session_of(now_us.astimezone(_timezone(stock.timezone_name))))
                if should_fetch(stock, now_us) and (supplier == 'Yahoo' or us_extended_active):
                    from .extended_naver import fetch_naver_extended
                    extra = tuple(quote.extended)
                    us_now_local = now_us.astimezone(_timezone(stock.timezone_name))
                    desired = session_of(us_now_local)
                    if not desired and us_now_local.hour >= 20:
                        desired = '애프터'
                    if desired and not any(p.session == desired for p in extra):
                        try:
                            from_naver = fetch_naver_extended(
                                stock, quote, opener=opener, now=now_us,
                                timeout=min(FETCH_TIMEOUT, 1.8), max_bytes=MAX_RESPONSE_BYTES,
                                user_agent=_YAHOO_USER_AGENT)
                            extra += tuple(p for p in from_naver if p.session not in {v.session for v in extra})
                            if from_naver:
                                _MARKET_LOG.info('US_EXTENDED_NAVER_OK ticker=%s sessions=%s',
                                                 stock.ticker, ','.join(p.session for p in from_naver))
                        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as e:
                            _MARKET_LOG.info('US_EXTENDED_NAVER_FAILED ticker=%s reason=%s',
                                             stock.ticker, str(e)[:160])
                    if desired and not any(p.session == desired for p in extra) and supplier == 'Yahoo':
                        try:
                            from_yahoo = fetch_yahoo(stock, quote, opener=opener, now=now_us,
                                                     timeout=min(FETCH_TIMEOUT, 2.5), max_bytes=MAX_RESPONSE_BYTES * 4,
                                                     user_agent=_YAHOO_USER_AGENT)
                            extra += tuple(p for p in from_yahoo if p.session not in {v.session for v in extra})
                        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as e:
                            _MARKET_LOG.info('US_EXTENDED_YAHOO_FAILED ticker=%s reason=%s',
                                             stock.ticker, type(e).__name__)
                    if desired and not any(p.session == desired for p in extra) and supplier != 'Nasdaq info':
                        try:
                            secondary = fetch_nasdaq_quote(stock, opener=opener, now=now_us).extended
                            extra += tuple(p for p in secondary if p.session not in {v.session for v in extra})
                        except StockQuoteError as e:
                            _MARKET_LOG.info('US_EXTENDED_NASDAQ_FAILED ticker=%s reason=%s', stock.ticker, e)
                    if extra:
                        quote = replace(quote, extended=tuple(
                            next(p for p in extra if p.session == label)
                            for label in ('프리', '애프터') if any(p.session == label for p in extra)))
                    elif desired:
                        _MARKET_LOG.info('US_EXTENDED_NO_TRADE ticker=%s requested=%s',
                                         stock.ticker, desired)
                if errors:
                    # 기존 오류 로그를 유지하면서 어떤 대체 제공처에서 복구됐는지도 식별한다.
                    _MARKET_LOG.info('US_QUOTE_FALLBACK_OK ticker=%s source=%s previous=%s',
                                     stock.ticker,supplier,','.join(errors))
                return quote
            except StockQuoteError as e:
                errors.append(supplier + ':' + str(e))
        _MARKET_LOG.warning('US_QUOTE_FAILED ticker=%s providers=%s',stock.ticker,';'.join(errors))
        raise StockQuoteError('미국 무료 시세 제공처 조회 실패')
    return fetch_yahoo_quote(stock, opener=opener, now=now)


def _formatted_price(value: float, currency: str) -> str:
    if currency == 'USD':
        return f'${value:,.2f}'
    if currency == 'KRW':
        return f'{value:,.0f}원'
    if currency == 'JPY':
        return f'¥{value:,.1f}'
    raise StockQuoteError('지원되지 않는 통화')


def _domestic_status_label(item: Quote) -> str:
    """KRX 메타데이터의 시세 신선도를 판단하며 기존 상세 출력과 통합 요약이 함께 이용한다."""
    meta = item.domestic
    if meta is None:
        return '지연 여부 미확인(대체 시세)'
    status = meta.market_status
    delta = (item.fetched_at - item.market_time).total_seconds()
    freshness = (0 <= delta <= 180)
    server_fresh = (meta.snapshot_time is not None and
                    -30 <= (item.fetched_at - meta.snapshot_time).total_seconds() <= 180)
    if meta.market_session in ('aftermarket', 'after_market','premarket','pre_market'):
        label = ('정규장 종가 별도 확인' if meta.regular_price is not None
                 else '장외 최종체결가 · 정규장 종가 미확인')
    elif meta.market_session in ('premarket', 'pre_market', 'beforemarket', 'before_market'):
        label = '개장 전 정규장 기준가'
    elif status in ('CLOSE', 'CLOSED', 'END'):
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
    return label


def _domestic_status_text(item: Quote) -> str:
    """이전 단일 종목 상세 출력의 형식을 유지한다."""
    meta = item.domestic
    when = item.market_time.strftime('%m/%d %H:%M:%S')
    if meta is None:
        return f'   └ KRX {when} · 지연 여부 미확인(대체 시세)'
    if meta.market_session in ('aftermarket', 'after_market', 'premarket', 'pre_market', 'beforemarket', 'before_market'):
        if meta.regular_price is not None and meta.regular_time is not None:
            return (f'   └ 정규장 기준 {meta.regular_time:%m/%d %H:%M} KST '
                    f'· {meta.regular_source} 확인 · 네이버 장외 응답 {when}')
        return f'   └ 정규장 종가 미확인 · 네이버 장외 응답 {when} · {meta.provider}'
    return f'   └ KRX {when} · {_domestic_status_label(item)} · 네이버 {meta.provider}'


def _domestic_after_text(item: Quote) -> str:
    """시간외 종목별 시세를 KRX 종가에 덮어쓰지 않으며 출처·거래소 불확실성을 표시."""
    meta = item.domestic
    aft = meta.after_market if meta is not None else None
    if aft is None:
        return ''
    when = aft.market_time.strftime('%m/%d %H:%M:%S')
    relative = _domestic_session_percent(item)
    if relative is None:
        change_label = '정규장 기준가 미확인'
    else:
        arrow = '▲' if relative > 0.00001 else ('▽' if relative < -0.00001 else '－')
        change_label = f'{arrow}{abs(relative):.2f}% 정규장 대비'
    status = '거래 중' if aft.status == 'OPEN' else ('마감' if aft.status == 'CLOSE' else '상태 미확인')
    exchange = 'NXT' if aft.exchange == 'NXT' else '시간외(거래소 미확인)'
    session_label = '애프터' if aft.session == '장후' else '프리'
    return (f'   └ {exchange} {aft.session} {_formatted_price(aft.price, item.stock.currency)} '
            f'({change_label}) · {when} · {status} · {session_label}'
            f' · 전일 종가 대비 {aft.percent:+.2f}%')


def _us_extended_text(item: Quote) -> str:
    """프리/애프터를 정규가와 혼동하지 않도록 거래시각·출처와 함께 별도 행 표시."""
    if item.stock.market != '미국' or not item.extended:
        return ''
    lines = []
    for extra in item.extended:
        arrow = '▲' if extra.percent > 0.00001 else ('▽' if extra.percent < -0.00001 else '－')
        lines.append(f'   └ {extra.session} {_formatted_price(extra.price, item.stock.currency)} '
                     f'({arrow}{abs(extra.percent):.2f}%) · '
                     f'{extra.market_time:%m/%d %H:%M} ET · {extra.source} · 지연 여부 미확인')
    return '\n'.join(lines)


def _latest_market_time(item: Quote) -> datetime:
    """정규장뿐 아니라 확인된 한국 시간외/미국 분봉 거래시각을 요약에 반영한다."""
    points = [item.market_time, *(extra.market_time for extra in item.extended)]
    if item.domestic is not None and item.domestic.after_market is not None:
        points.append(item.domestic.after_market.market_time)
    return max(points)


def quote_line(item: Quote, *, source_details: bool = True) -> str:
    """단일 종목 상세 출력은 유지하며 목록에서만 출처 중복을 감춘다."""
    arrow = '▲' if item.percent > 0.00001 else ('▽' if item.percent < -0.00001 else '－')
    domestic_extra = item.stock.market == '한국' and item.domestic is not None and (
        item.domestic.market_session in ('aftermarket', 'after_market', 'premarket', 'pre_market', 'beforemarket', 'before_market')
        and item.domestic.after_market is not None)
    if domestic_extra and item.domestic.regular_price is None:
        body = f'{item.stock.name} : 정규장 종가 미확인'
    else:
        display_price = (item.domestic.regular_price if domestic_extra else None)
        display_pct = (item.domestic.regular_percent if domestic_extra else None)
        display_price = display_price if display_price is not None else item.price
        display_pct = display_pct if display_pct is not None else item.percent
        arrow = '▲' if display_pct > 0.00001 else ('▽' if display_pct < -0.00001 else '－')
        body = f'{item.stock.name} : {_formatted_price(display_price, item.stock.currency)} ({arrow}{abs(display_pct):.2f}%)'
        if domestic_extra:
            body += ' [정규·별도 확인]'
    if item.stock.market == '미국' and item.extended:
        body += ' [정규]'
        extra_us = _us_extended_text(item)
        if extra_us:
            body += '\n' + extra_us
    if not source_details:
        # 시간외 가격은 본장과 다른 가격이므로 기존처럼 해당 종목에 별도 표시한다.
        extra = _domestic_after_text(item) if item.stock.market == '한국' else ''
        return body + ('\n' + extra if extra else '')
    if item.stock.market == '미국' and item.source in ('나스닥 확정 종가','네이버 해외 확정 종가'):
        return body + f"\n   └ 미국 {item.market_time.strftime('%m/%d')} 정규장 종가 · {item.source} · 실시간 아님"
    if item.stock.market == '미국' and item.source == '나스닥 웹':
        # 공개 웹 응답은 별도 실시간 거래소 라이선스/세션을 보증하지 않는다.
        return body + f"\n   └ 미국 {item.market_time.strftime('%m/%d %H:%M')} ET · 나스닥 공개 시세(지연 여부 미확인)"
    if item.stock.market != '한국' or item.domestic is None:
        # 종전 Quote 생성자/테스트 호출에 대해서는 출력 형식을 변경하지 않는다.
        return body
    extra = _domestic_after_text(item)
    return body + '\n' + _domestic_status_text(item) + ('\n' + extra if extra else '')


def market_source_summary(quotes: tuple[Quote | None, ...] | list[Quote | None]) -> tuple[str, ...]:
    """실제로 성공한 시세만 국내/미국/일본으로 묶어 출처·최신 거래시각·지연 정보를 한 번씩 표시한다.

    종목마다 다른 시각/제공자가 섞이면 이를 표시한다. 단일 최신 시각을 전체 종목 시각으로
    주장하지 않으며, 장중 확인 조건이 부족한 가격을 실시간으로 위장하지 않는다.
    """
    result = []
    for region, title in (('한국', '국내'), ('미국', '미국'), ('일본', '일본')):
        region_quotes = [q for q in quotes if q is not None and q.stock.market == region]
        if not region_quotes:
            continue
        providers = []
        statuses = []
        for q in region_quotes:
            if region == '한국':
                provider = ('네이버 ' + q.domestic.provider
                            if q.domestic is not None and q.domestic.provider in ('폴링', '모바일')
                            else (q.domestic.provider if q.domestic is not None else '공급자 미확인'))
                status = _domestic_status_label(q)
            elif region == '미국':
                provider = ('나스닥 공개 시세' if q.source == '나스닥 웹'
                            else q.source if q.source in ('나스닥 확정 종가','네이버 해외 확정 종가')
                            else 'Yahoo Finance')
                if q.extended:
                    provider += '+장외'
                status = ('최근 정규장 확정 종가(실시간 아님)'
                          if q.source in ('나스닥 확정 종가','네이버 해외 확정 종가')
                          else '지연 여부 미확인')
            else:
                provider = q.source or 'Yahoo Finance'
                status = '지연 여부 미확인'
            if region == '미국' and q.extended:
                status += ' · 프리/애프터 별도(지연 여부 미확인)'
            if provider not in providers:
                providers.append(provider)
            if status not in statuses:
                statuses.append(status)
        latest = max(_latest_market_time(q) for q in region_quotes)
        when = latest.strftime('%m/%d %H:%M:%S') if region == '한국' else latest.strftime('%m/%d %H:%M')
        zone = ('KST ' if region == '한국' and any(q.domestic and q.domestic.market_session in ('aftermarket','after_market') for q in region_quotes)
                else 'KRX ' if region == '한국' else 'ET ' if region == '미국' else 'JST ')
        time_difference = ' (종목별 거래시각 상이)' if len({q.market_time for q in region_quotes}) > 1 else ''
        result.append(f'  {title}: {" / ".join(providers)} · {zone}{when} (최신){time_difference} · {" / ".join(statuses)}')
    return ('시세 출처 · 기준시각:', *result) if result else ()


def _domestic_session_percent(item: Quote) -> float | None:
    """장외 거래 당일 정규장(프리는 직전 정규장) 종가 대비. 기준가 미확인 시 None."""
    meta = item.domestic
    aft = meta.after_market if meta else None
    if aft is None:
        return None
    reference = meta.regular_price
    reference_time = meta.regular_time
    if reference is None and meta.market_session not in (
        'aftermarket', 'after_market', 'premarket', 'pre_market',
        'beforemarket', 'before_market'
    ):
        # 구형 Naver 본장 응답 + 별도 overMarketPriceInfo:
        # 실제 KRX 마감시각의 기준가격이므로 이 값만 비교 기준으로 허용한다.
        local = item.market_time.astimezone(_timezone(item.stock.timezone_name))
        if (15, 20) <= (local.hour, local.minute) <= (15, 35):
            reference = item.price
            reference_time = local
    if reference is None or reference <= 0 or reference_time is None:
        return None
    if aft.session == '장후' and reference_time.date() != aft.market_time.date():
        return None
    if aft.session == '장전' and not (0 < (aft.market_time.date() - reference_time.date()).days <= 4):
        return None
    percent = (aft.price / reference - 1.0) * 100.0
    return percent if math.isfinite(percent) and -99.9 < percent < 1000 else None


def _display_session(item: Quote) -> tuple[float, float | None, str]:
    """간략 화면의 대표 세션을 하나만 고른다. 원본 Quote 값은 변경하지 않는다."""
    if item.stock.market == '한국' and item.domestic is not None:
        meta = item.domestic
        aft = meta.after_market
        period = meta.market_session
        expected = ('장후' if period in ('aftermarket', 'after_market')
                    else '장전' if period in ('premarket', 'pre_market', 'beforemarket', 'before_market')
                    else '')
        if aft is not None:
            local = item.fetched_at.astimezone(_timezone(item.stock.timezone_name))
            clock = (local.hour, local.minute)
            on_session_day = local.weekday() < 5 and aft.market_time.date() == local.date()
            market_in_session = (
                (aft.session == '장후' and (15, 40) <= clock <= (23, 59)) or
                (aft.session == '장전' and (8, 0) <= clock < (9, 0))
            )
            if on_session_day and (expected == aft.session or market_in_session):
                label = '애프터' if aft.session == '장후' else '프리'
                return aft.price, _domestic_session_percent(item), label
            # 이전 거래일 통합 응답 closePrice가 여전히 장외 가격인 경우,
            # 그 값을 오늘 정규장 시세인 것처럼 보여주지 않는다.
            if expected and not on_session_day:
                if meta.regular_price is not None:
                    return meta.regular_price, meta.regular_percent, '정규'
                return aft.price, None, '이전 장외'
    if item.stock.market == '미국' and item.extended:
        from .extended_sessions import session_of
        # 공급자의 검증된 장외체결 중 현재 현지 세션을 우선.
        et_now = item.fetched_at.astimezone(_timezone(item.stock.timezone_name))
        desired = session_of(et_now)
        if not desired and et_now.weekday() < 5 and et_now.hour >= 20:
            desired = '애프터'
        # 장중(09:30~16:00 ET) 및 장외 이전에는 프리 기록을 대표가격으로 사용하지 않는다.
        if desired:
            verified = [e for e in item.extended
                        if e.session == desired and e.market_time.date() == et_now.date()]
            if verified:
                chosen = max(verified, key=lambda e: e.market_time)
                return chosen.price, chosen.percent, chosen.session
    return item.price, item.percent, '정규'


def _compact_price(value: float, currency: str, *, extended: bool = False) -> str:
    if currency == 'KRW':
        return f'{value / 10000:.1f}만' if value < 1_000_000 else f'{value / 10000:,.0f}만'
    if currency == 'JPY':
        return f'¥{value:,.0f}'
    # 장외 미국 가격은 소수점까지 표시해 체결가가 변한 것을 확인할 수 있게 한다.
    return f'\u0024{value:,.2f}' if extended or value < 500 else f'\u0024{value:,.0f}'


def compact_quote_line(item: Quote) -> str:
    """메모리7/관심그룹: 종목 하나를 반드시 한 줄로, 선택한 세션 가격만 보여준다."""
    stock = item.stock
    aliases = {'웨스턴디지털': 'WDC', '웬디': 'WDC', 'SK하이닉스': '하이닉스'}
    name = aliases.get(stock.name, stock.name)
    value, change, session = _display_session(item)
    price = _compact_price(value, stock.currency, extended=(session != '정규'))
    suffix = ' P' if session == '프리' else (' A' if session == '애프터' else '')
    if change is None:
        # 정규장 기준가 없이 전일비 하락을 '장후 하락'으로 오표시하지 않는다.
        return f'{name} {price}{suffix} 기준가?'
    arrow = '🔺' if change > 0.00001 else ('▽' if change < -0.00001 else '➖')
    sign = '+' if change > 0.00001 else ('-' if change < -0.00001 else '')
    return f'{name} {price} {arrow}{sign}{abs(change):.2f}%{suffix}'


def compact_source_summary(quotes: tuple[Quote | None, ...] | list[Quote | None]) -> tuple[str, ...]:
    """성공한 종목의 출처/시각만 표시; 혼합 출처 및 확정 종가를 숨기지 않는다."""
    lines = []
    for region in ('한국', '미국', '일본'):
        items = [q for q in quotes if q is not None and q.stock.market == region]
        if not items:
            continue
        providers = []
        for q in items:
            if region == '한국':
                _selected_price, _selected_change, selected_session = _display_session(q)
                source = ('네이버·장외 통합' if selected_session in ('프리', '애프터')
                          else '네이버·KRX' if q.domestic and q.domestic.provider in ('폴링', '모바일')
                          else (q.domestic.provider if q.domestic else '야후'))
            elif region == '미국' and q.extended:
                active_price, _active_percent, active_session = _display_session(q)
                active = next((entry for entry in q.extended
                               if entry.session == active_session and entry.price == active_price), None)
                if active is not None:
                    source = active.source.replace('Yahoo 1분봉', '야후 장외').replace(
                        'Yahoo 메타', '야후 장외')
                else:
                    source = q.source or '야후'
            elif q.source in ('나스닥 확정 종가', '네이버 해외 확정 종가'):
                source = '나스닥 종가' if q.source.startswith('나스닥') else '네이버 종가'
            elif q.source == '나스닥 웹':
                source = '나스닥'
            else:
                source = q.source or '야후'
                source = source.replace('Yahoo Finance', '야후')
            if source not in providers:
                providers.append(source)
        latest = max(_latest_market_time(q) for q in items)
        zone = 'ET' if region == '미국' else ('JST' if region == '일본' else 'KST')
        line = f'📡 {region} {latest:%m/%d} {"·".join(providers)} {latest:%H:%M} {zone}'
        if len({q.market_time for q in items}) > 1:
            line += ' · 시각 상이'
        if any(q.source in ('나스닥 확정 종가', '네이버 해외 확정 종가') for q in items):
            line += ' · 확정 종가'
        if region == '한국' and any(q.domestic and q.domestic.after_market for q in items):
            line += (' · 장외 별도/정규 종가 검증'
                     if all(_domestic_session_percent(q) is not None
                            for q in items if q.domestic and q.domestic.after_market)
                     else ' · 장외 시세/일부 정규 종가 미확인')
        if region == '미국' and any(q.extended for q in items):
            line += ' · 장외 별도·지연 미확인'
        if region == '미국' and any(not q.extended for q in items):
            from .extended_sessions import session_of
            if any(session_of(q.fetched_at.astimezone(_timezone(q.stock.timezone_name)))
                   for q in items if not q.extended):
                line += ' · 일부 장외 시세 미제공'
        lines.append(line)
    return tuple(lines)


def _memory7_brief_clock(quotes: tuple[Quote | None, ...] | list[Quote | None]) -> str:
    """카카오톡 한 화면용 각국 현지 거래 기준시각. 출처 원문은 상세보기에서만 제공."""
    regions = (('한국', 'KR'), ('미국', 'US'), ('일본', 'JP'))
    points = []
    for country, label in regions:
        eligible = [item for item in quotes if item is not None and item.stock.market == country]
        if eligible:
            latest = max(_latest_market_time(item) for item in eligible)
            points.append((label, latest.strftime('%m/%d'), latest.strftime('%H:%M')))
    if not points:
        return ''
    days = {day for _label, day, _clock in points}
    if len(days) == 1:
        # 대부분의 동시 조회는 날짜가 같으므로 날짜를 한 번만 사용한다.
        return f'📡 {points[0][1]} ' + ' · '.join(f'{label}{clock}' for label, _, clock in points)
    # 혼합 거래일의 날짜는 반드시 국가마다 표기한다(하루 차이를 현재가로 오인하지 않음).
    return '📡 ' + ' · '.join(f'{label}{day} {clock}' for label, day, clock in points)


def memory7_report(*, fetcher=fetch_quote, now: datetime | None = None,
                   use_cache: bool = True, detailed: bool = False) -> str:
    """기본 종목당 1행, 상세 메뉴는 정규/프리/애프터 가격·시각·출처·등락기준 표시."""
    global _CACHE
    started = time.monotonic()
    if use_cache and fetcher is fetch_quote and not detailed:
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
    lines = ['🔎 메모리7 시세 상세 보기' if detailed else '💾 메모리7 시세 요약']
    dates: dict[str, str] = {}
    success = 0
    latest_dates = {}
    for item in quotes:
        if item is not None:
            day = _latest_market_time(item).date()
            latest_dates[item.stock.market] = max(day, latest_dates.get(item.stock.market, day))
    for index, (stock, item) in enumerate(zip(WATCHLIST, quotes), start=1):
        if item is None:
            lines.append(f'{index}. {stock.name} : 조회 불가')
        else:
            success += 1
            line = quote_line(item, source_details=True) if detailed else compact_quote_line(item)
            latest_trade = _latest_market_time(item)
            if latest_trade.date() < latest_dates[stock.market]:
                line += (' [거래일 ' + latest_trade.strftime('%m/%d') + ']' if detailed
                         else ' (' + latest_trade.strftime('%m/%d') + ')')
            lines.append(f'{index}. {line}')
            dates[stock.market] = latest_trade.strftime('%m/%d')
    if not success:
        raise StockQuoteError('8개 종목 시세를 가져오지 못했습니다. 시세 제공처의 접속/요청 제한을 확인하세요.')
    # 서로 다른 현지 거래일을 '오늘'이라는 단일 날짜로 오해하지 않도록 분리한다.
    if detailed:
        lines.append('')
        lines.extend(market_source_summary(quotes))
        lines.append('※ 장외 등락 기준: 프리=직전 정규장 종가 대비 / 애프터=당일 정규장 종가 대비')
        lines.append('※ 한국 장외 전일비는 별도 표기되며 정규장 대비 상승률과 다를 수 있습니다.')
    else:
        # 원래 3개 시장의 장문 출처는 상세보기에서 보존하고 기본 화면은 1행 시각 요약만 남긴다.
        lines.append('')
        line = _memory7_brief_clock(quotes)
        if line:
            lines.append(line)
    if success < len(WATCHLIST):
        lines.append((f'※ {len(WATCHLIST)-success}종목 조회 실패'
                      if not detailed else f'※ {len(WATCHLIST)-success}종목 조회 실패. 값은 임의 보충하지 않았습니다.'))
    lines.append('※ 무료·지연 가능·실시간 아님' if detailed else '※ 무료·지연·실시간 아님')
    lines.append('※ 5분 내 1~8: 종목 분석' if detailed else '※ 5분 내 1~8: 분석')
    lines.append('9. ↩ 간략보기' if detailed else '9. 🔎 상세보기')
    result = '\n'.join(lines)
    if use_cache and fetcher is fetch_quote and not detailed:
        with _CACHE_LOCK:
            _CACHE = (time.monotonic(), result)
    return result


def execute_stock_command(command: str, argument: str) -> str:
    """기존 메모리7 조회를 보존하고 '메모리7 상세' 읽기 전용 보기만 추가한다."""
    mode = argument.strip()
    if command == '주식':
        if mode == '메모리7':
            return memory7_report()
        if mode in ('메모리7 상세', '상세'):
            return memory7_report(detailed=True)
    if command == '메모리7':
        if not mode:
            return memory7_report()
        if mode == '상세':
            return memory7_report(detailed=True)
    raise StockQuoteError('사용법: 앙개야 주식 메모리7 / 주식 메모리7 상세')
