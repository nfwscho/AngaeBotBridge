"""
앙개봇 4개 고정 시세 메뉴(한국·일본·미국 혼합 반도체주 포함) — 전체 기능 및 안전 규칙
1. 반도체주 19개(KR·JP·US), AI 주도주 13개, 반도체 및 기자재 19개, 데센 및 네트워크 5개를 사용자 지정 순서대로 제공한다.
2. 삼성 005930.KS·하이닉스 000660.KS·키오시아 285A.T·미국 상장 EWY/DRAM ETF 및 TSM 등 지정된 티커를 정확히 구분한다.
3. 기존 주식 시세 엔진 market.fetch_quote 및 watchlists.group_report를 재사용해 정규장과 검증된 프리/애프터 P/A 가격을 조회한다.
4. 사용자 제공 수치·등락률은 예시로만 취급하고 실행 시 항상 공급자로부터 새 시세를 조회하며 불확실한 가격을 만들어내지 않는다.
5. 반도체주 19종목, AI 주도주 13종목, 반도체 및 기자재 19종목, 데센 및 네트워크 5종목을 각각 하나의 간략 메시지에 전부 출력한다.
6. 1~19는 화면에 표시된 번호의 정확한 종목 분석, 99는 전체 섹터 상세/간략 전환, 0은 직전 화면, 00은 홈이다.
7. 섹터는 읽기 전용 상수이며 기존 사용자별 stock_groups·stock_items CRUD/그룹 최대 10개/그룹당 10종목 제한을 변경하지 않는다.
8. 1~19 분석은 기존 다른 메뉴의 1~10과 섞이지 않도록 해당 섹터 세션에만 허용하며 기존 사용자 관심그룹·최근조회·메모리7/로그와 충돌하지 않는다.
9. 섹터명·페이지·보기 모드를 엄격히 검증해 임의 URL, SQL, 명령 실행이나 다른 사용자의 자료 조회를 허용하지 않는다.
10. 지연/무료 공급자, 실패시 조회 불가, 한국·미국·일본 장 구분, 인증·방/발신자·5분 유효시간 및 기존 DB·환경설정·Android 배터리를 보존한다.
11. 단위 테스트에서 fetcher를 주입할 수 있어 인터넷과 실제 단말 없이 동일 시세·출력·페이지 번호를 검증한다.
12. 기존 5-worker 동시 조회 한도를 재사용해 19종목을 한 번에 표시하며 개별 실패종목의 조회 불가·기존 시세 제공자 차단을 보존한다.
13. 긴 회사명으로 인한 카카오톡 자동 줄바꿈을 최소화하기 위해 사용자가 제시한 MSFT 표기를 그대로 유지한다.
14. 간략보기는 목록 직후 정확히 두 줄('📡 현지시각', '99. 🔎 상세보기')만 출력하며 Android에서 배터리 🔋/⚡ 잔량을 마지막 상세보기 줄에 합친다.
15. 상세보기는 종가·장외·공급자 시간 등 기존 긴 상세 원문을 그대로 보존하고 별도 페이지로 나누지 않는다.
16. 간략보기의 별도 '※ 지연·비실시간/분석' 안내는 제거하되 상세보기의 모든 원문·지연 경고·실패 건수·기존 번호 메뉴와 로그는 유지한다.
17. 간략 조회 실패 건수는 시각 한 줄에 합쳐 데이터 상태를 숨기지 않으며 시각이 없으면 기준시각 미확인으로 표기한다.
18. 반도체주 고정 목록은 기존 메모리7을 변경하지 않고 한국 2/미국 16/일본 1종목을 정확한 환율·현지시각·통화로 표시한다.
19. 신규 DRAM은 Cboe BZX 상장 Roundhill Memory ETF, EWY는 NYSE Arca 상장 iShares MSCI South Korea ETF로 USD 시세를 조회한다.
20. 제공된 예시 가격/등락률은 하드코딩하지 않고 실시간 조회; 개인 그룹/메모리7/미국시총10의 원본 구성과 순서·DB·로그는 보존한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from math import ceil
from typing import Callable

from .market import Stock, StockQuoteError
from .watchlists import group_report


PAGE_SIZE = 19
_US_TZ = 'America/New_York'


@dataclass(frozen=True)
class Sector:
    key: str
    title: str
    stocks: tuple[Stock, ...]


def _stocks(rows: tuple[tuple[str, str], ...]) -> tuple[Stock, ...]:
    """상장 티커와 사용자 지정 한글 표시명만 담는 불변 읽기 전용 목록."""
    return tuple(Stock(name, ticker, 'USD', '미국', _US_TZ) for name, ticker in rows)


# 과거 메모리7의 불변 WATCHLIST를 수정하지 않고 별도 읽기 전용
# 19종목 반도체주 전체목록만 사용자가 지정한 순서로 구성한다.
_SEMI_CHIPS = (
    Stock('삼성전자', '005930.KS', 'KRW', '한국', 'Asia/Seoul'),
    Stock('하이닉스', '000660.KS', 'KRW', '한국', 'Asia/Seoul'),
    Stock('마이크론', 'MU', 'USD', '미국', _US_TZ),
    Stock('샌디스크', 'SNDK', 'USD', '미국', _US_TZ),
    Stock('키오시아', '285A.T', 'JPY', '일본', 'Asia/Tokyo'),
    Stock('WDC', 'WDC', 'USD', '미국', _US_TZ),
    Stock('씨게이트', 'STX', 'USD', '미국', _US_TZ),
    Stock('SKHY', 'SKHY', 'USD', '미국', _US_TZ),
    Stock('EWY', 'EWY', 'USD', '미국', _US_TZ),
    Stock('DRAM', 'DRAM', 'USD', '미국', _US_TZ),
    Stock('NVDA', 'NVDA', 'USD', '미국', _US_TZ),
    Stock('TSM', 'TSM', 'USD', '미국', _US_TZ),
    Stock('AMD', 'AMD', 'USD', '미국', _US_TZ),
    Stock('INTC', 'INTC', 'USD', '미국', _US_TZ),
    Stock('AVGO', 'AVGO', 'USD', '미국', _US_TZ),
    Stock('MRVL', 'MRVL', 'USD', '미국', _US_TZ),
    Stock('ARM', 'ARM', 'USD', '미국', _US_TZ),
    Stock('QCOM', 'QCOM', 'USD', '미국', _US_TZ),
    Stock('ASML', 'ASML', 'USD', '미국', _US_TZ),
)

SECTORS: tuple[Sector, ...] = (
    Sector('chip', '반도체주 시세', _SEMI_CHIPS),
    Sector('ai', 'AI 주도주', _stocks((
        ('엔비디아', 'NVDA'), ('애플', 'AAPL'), ('MSFT', 'MSFT'),
        ('구글', 'GOOGL'), ('아마존', 'AMZN'), ('메타', 'META'),
        ('테슬라', 'TSLA'), ('팔란티어', 'PLTR'), ('서비스나우', 'NOW'),
        ('세일즈포스', 'CRM'), ('오라클', 'ORCL'), ('IBM', 'IBM'),
        ('스페이스X', 'SPCX'),
    ))),
    Sector('semi', '반도체 및 기자재', _stocks((
        ('ARM', 'ARM'), ('브로드컴', 'AVGO'), ('마벨', 'MRVL'),
        ('퀄컴', 'QCOM'), ('AMD', 'AMD'), ('인텔', 'INTC'),
        ('TSMC', 'TSM'), ('TI', 'TXN'), ('마이크론', 'MU'),
        ('SKHY', 'SKHY'), ('ASML', 'ASML'), ('AMAT', 'AMAT'),
        ('램리서치', 'LRCX'), ('KLA', 'KLAC'), ('세레브라스', 'CBRS'),
        ('SIMO', 'SIMO'), ('샌디스크', 'SNDK'), ('씨게이트', 'STX'),
        ('WDC', 'WDC'),
    ))),
    Sector('dc', '데센 및 네트워크', _stocks((
        ('루멘텀', 'LITE'), ('아리스타', 'ANET'), ('버티브', 'VRT'),
        ('델', 'DELL'), ('코닝', 'GLW'),
    ))),
)

_SECTOR_BY_KEY = {sector.key: sector for sector in SECTORS}
_REQUEST = re.compile(r'^섹터시세 (chip|ai|semi|dc) ([1-9][0-9]?) (간략|상세)$')


def get_sector(key: str) -> Sector:
    """허용된 3개 고정 키만 찾는다. 사용자 그룹 이름과 혼용하지 않는다."""
    result = _SECTOR_BY_KEY.get(key)
    if result is None:
        raise StockQuoteError('등록되지 않은 주식 섹터입니다.')
    return result


def page_count(key: str) -> int:
    return ceil(len(get_sector(key).stocks) / PAGE_SIZE)


def get_page(key: str, page: int) -> tuple[Stock, ...]:
    """페이지 번호는 1부터 시작. 실제 가격 조회 전 배열 범위 검증."""
    sector = get_sector(key)
    if not isinstance(page, int) or isinstance(page, bool) or not 1 <= page <= page_count(key):
        raise StockQuoteError('해당 섹터의 시세 페이지가 없습니다.')
    start = (page - 1) * PAGE_SIZE
    return sector.stocks[start:start + PAGE_SIZE]


def parse_sector_request(argument: str) -> tuple[str, int, bool] | None:
    """내부 메뉴에서 생성된 정확한 요청만 읽기 전용 시세 조회로 처리."""
    if not argument.startswith('섹터시세'):
        return None
    match = _REQUEST.fullmatch(argument)
    if match is None:
        raise StockQuoteError('섹터 시세 사용법: 섹터시세 ai 1 간략')
    key, page_text, mode = match.groups()
    page = int(page_text)
    get_page(key, page)
    return key, page, mode == '상세'


def sector_argument(key: str, page: int, detailed: bool) -> str:
    """정규화한 메뉴 요청을 만들며 알 수 없는 섹터·페이지를 만들지 않는다."""
    get_page(key, page)
    return f"섹터시세 {key} {page} {'상세' if detailed else '간략'}"


def sector_report(key: str, page: int = 1, *, detailed: bool = False,
                  fetcher: Callable[[Stock], object] | None = None) -> str:
    """고정 섹터의 전체 5~19종목을 한 화면에 조회; 기존 공통 시세 렌더러를 재사용."""
    sector = get_sector(key)
    subset = get_page(key, page)
    # 모든 섹터를 1쪽에 표시한다. 원본 그룹 조회 병렬성/가격 검증은 재사용.
    label = sector.title
    report = group_report(label, subset, fetcher=fetcher, detailed=detailed)
    lines = report.splitlines()
    if not lines or not lines[-1].startswith('99. '):
        raise StockQuoteError('시세 그룹 응답 형식이 변경되었습니다.')
    lines[0] = (f'🔎 {sector.title} 상세 ({len(subset)}종목)' if detailed
                else f'📊 {sector.title} ({len(subset)}종목)')
    if detailed:
        # 상세화면은 현재가/정규/프리·애프터/일별 출처 원문을 보존한다.
        lines[-2] = f'※ 5분 내 1~{len(subset)}: 분석'
        return '\n'.join(lines)
    # 간략은 19개의 개별 행을 보존하면서 긴 공통 안내만 압축한다.
    # 공통 renderer의 가격/오류 검증/짧은 시장시계와 99 메뉴는 유지한다.
    rows = lines[1:1 + len(subset)]
    clock = next((line for line in lines[1 + len(subset):] if line.startswith('📡 ')), '')
    failed = [line for line in lines if line.startswith('※ ') and '조회 실패' in line]
    # 본문 아래 정확히 두 줄: '📡 현지시각', '99. 상세보기'.
    # 제공자 조회 실패가 있으면 기존 실패 건수를 삭제하지 않고 시각 줄에 합친다.
    clock = clock or '📡 기준시각 미확인'
    if failed:
        clock += ' · ' + ' · '.join(line.removeprefix('※ ') for line in failed)
    return '\n'.join([lines[0], *rows, clock, lines[-1]])
