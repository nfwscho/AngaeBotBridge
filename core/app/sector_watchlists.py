"""
앙개봇 3대 미국 산업 섹터 고정 시세 메뉴 — 전체 기능 및 안전 규칙
1. AI 주도주 13개, 반도체 및 기자재 19개, 데이터센터 및 네트워크 5개를 사용자가 제시한 순서로 제공한다.
2. 공식 확인된 현재 상장 미국 종목코드(2026-11-06 기준)를 명시하며 세레브라스 CBRS, 스페이스X SPCX, 서비스나우 NOW, TI TXN을 정확히 연결한다.
3. 기존 주식 시세 엔진 market.fetch_quote 및 watchlists.group_report를 재사용해 정규장과 검증된 프리/애프터 P/A 가격을 조회한다.
4. 사용자 제공 수치·등락률은 예시로만 취급하고 실행 시 항상 공급자로부터 새 시세를 조회하며 불확실한 가격을 만들어내지 않는다.
5. 각 섹터는 최대 10종목씩 페이지로 나눠 휴대폰 카카오톡의 전체보기 접힘과 번호 1~10 분석 충돌을 줄인다.
6. 98은 다음 페이지, 97은 이전 페이지, 99는 해당 페이지의 정규장·장외 상세보기 전환, 0은 직전 실제 화면, 00은 홈이다.
7. 섹터는 읽기 전용 상수이며 기존 사용자별 stock_groups·stock_items CRUD/그룹 최대 10개/그룹당 10종목 제한을 변경하지 않는다.
8. 하위 분석은 페이지마다 표시된 1~10번을 사용하고 코드·순서·원본 사용자 그룹·최근조회·메모리7 시세/로그와 충돌하지 않는다.
9. 섹터명·페이지·보기 모드를 엄격히 검증해 임의 URL, SQL, 명령 실행이나 다른 사용자의 자료 조회를 허용하지 않는다.
10. 지연/무료 공급자, 실패시 조회 불가, 한국·미국·일본 장 구분, 인증·방/발신자·5분 유효시간 및 기존 DB·환경설정·Android 배터리를 보존한다.
11. 단위 테스트에서 fetcher를 주입할 수 있어 인터넷과 실제 단말 없이 동일 시세·출력·페이지 번호를 검증한다.
12. 19종목을 한번에 호출하지 않고 페이지당 최대 10개를 병렬 조회하여 기존 응답 시간 제한과 제공자 호출 부담을 보존한다.
13. 긴 회사명으로 인한 카카오톡 자동 줄바꿈을 최소화하기 위해 사용자가 제시한 MSFT 표기를 그대로 유지한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from math import ceil
from typing import Callable

from .market import Stock, StockQuoteError
from .watchlists import group_report


PAGE_SIZE = 10
_US_TZ = 'America/New_York'


@dataclass(frozen=True)
class Sector:
    key: str
    title: str
    stocks: tuple[Stock, ...]


def _stocks(rows: tuple[tuple[str, str], ...]) -> tuple[Stock, ...]:
    """상장 티커와 사용자 지정 한글 표시명만 담는 불변 읽기 전용 목록."""
    return tuple(Stock(name, ticker, 'USD', '미국', _US_TZ) for name, ticker in rows)


SECTORS: tuple[Sector, ...] = (
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
        ('웬디', 'WDC'),
    ))),
    Sector('dc', '데센 및 네트워크', _stocks((
        ('루멘텀', 'LITE'), ('아리스타', 'ANET'), ('버티브', 'VRT'),
        ('델', 'DELL'), ('코닝', 'GLW'),
    ))),
)

_SECTOR_BY_KEY = {sector.key: sector for sector in SECTORS}
_REQUEST = re.compile(r'^섹터시세 (ai|semi|dc) ([1-9][0-9]?) (간략|상세)$')


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
    """해당 페이지의 1~10종목만 실행 시 조회; 사용자 기존 시세 렌더러 재사용."""
    sector = get_sector(key)
    subset = get_page(key, page)
    pages = page_count(key)
    start = (page - 1) * PAGE_SIZE + 1
    stop = start + len(subset) - 1
    label = f'{sector.title} ({page}/{pages} · {start}~{stop}/{len(sector.stocks)})'
    report = group_report(label, subset, fetcher=fetcher, detailed=detailed)
    lines = report.splitlines()
    # 공통 그룹의 99 상세 버튼을 유지하고 그 앞에 이동 페이지 번호를 배치한다.
    if not lines or not lines[-1].startswith('99. '):
        raise StockQuoteError('시세 그룹 페이지 응답 형식이 변경되었습니다.')
    selector = lines.pop()
    if page > 1:
        lines.append('97. ◀ 이전 10종목')
    if page < pages:
        lines.append(f'98. ▶ 다음 {len(get_page(key,page+1))}종목')
    lines.append(selector)
    return '\n'.join(lines)
