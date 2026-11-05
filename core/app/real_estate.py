"""
앙개봇 부동산 실거래가 모듈 — 전체 기능 및 기존 기능 보존
1. 공공데이터포털 국토교통부 아파트 매매·전월세 신고 실거래가 XML API를 조회한다.
2. '부 매매/시세', '부 전세', '부 월세' 및 아파트명 필터로 최근 계약을 조회한다.
3. 서울 25개 자치구 이름(또는 전국 법정동 앞 5자리 코드)으로 지역을 식별한다.
4. 동일 이름 중복·지원하지 않는 지역은 추정하지 않고 명시적인 입력 안내로 거부한다.
5. 사용자가 '부 지역 강남구'로 지정한 조회 구역을 방·발신자별 독립 SQLite 테이블에 저장한다.
6. 지역을 설정하지 않은 경우 임의의 서울·현재 위치를 추정하지 않고 설정을 요청한다.
7. 최근 3개 계약 월을 조회하고 계약일 역순 최대 5건, 원본 계약 월과 신고 출처를 표시한다.
8. 거래금액·보증금·월세의 단위는 원본 만원 단위 그대로 환산하며 전용면적·층을 표시한다.
9. 매매 취소·해제 거래를 결과에서 제외하고 전세(월세=0), 월세(월세>0)를 구분한다.
10. 매매가를 실시간 호가·평가액으로 부르지 않으며 신고 지연·정정 가능성을 안내한다.
11. API 키 MOLIT_API_KEY는 환경변수로만 받고 API 요청에만 전송, 오류·로그에 노출하지 않는다.
12. 공급자 인증/네트워크/XML 오류, 결과 누락·요청 과다를 구분하며 허위 시세를 생성하지 않는다.
13. 외부 HTTP는 기존 FastAPI DB 쓰기 트랜잭션 밖에서만 실행하고 최신 호출마다 데이터를 조회한다.
14. 요청 월별 최대 3페이지(1천 건/페이지)를 검사하고 불완전한 페이지 조회는 오류 처리한다.
15. 기존 jobs/events/AI/주식/메모·날씨 DB와 로그, Android UI/배터리, 인증·중복 요청/5분 메뉴를 보존한다.
16. 외부로 채팅방·발신자/개인정보·토큰을 보내지 않고 법정동코드·거래년월만 요청한다.
17. 표준 라이브러리만 사용하며 모의 API 응답으로 오프라인 회귀 테스트할 수 있다.
"""
from __future__ import annotations

import os
import re
import sqlite3
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SALE_ENDPOINT = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
RENT_ENDPOINT = "https://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
SEOUL_CODES = {
    "종로구": "11110", "중구": "11140", "용산구": "11170", "성동구": "11200",
    "광진구": "11215", "동대문구": "11230", "중랑구": "11260", "성북구": "11290",
    "강북구": "11305", "도봉구": "11320", "노원구": "11350", "은평구": "11380",
    "서대문구": "11410", "마포구": "11440", "양천구": "11470", "강서구": "11500",
    "구로구": "11530", "금천구": "11545", "영등포구": "11560", "동작구": "11590",
    "관악구": "11620", "서초구": "11650", "강남구": "11680", "송파구": "11710",
    "강동구": "11740",
}
CODE_TO_SEOUL = {v: "서울 " + k for k, v in SEOUL_CODES.items()}
MAX_PAGES = 3
MAX_RESULTS = 5
SEOUL_TZ = timezone(timedelta(hours=9))


class RealEstateError(ValueError):
    """사용자 입력 또는 공식 실거래 데이터 공급 오류."""


@dataclass(frozen=True)
class District:
    name: str
    code: str


@dataclass(frozen=True)
class Deal:
    date: str
    apartment: str
    area: float
    floor: str
    amount: int
    monthly: int = 0


def init_real_estate_schema(db: sqlite3.Connection) -> None:
    """운영 DB를 초기화하지 않고 독립적인 사용자별 조회 지역만 생성."""
    db.execute("""CREATE TABLE IF NOT EXISTS real_estate_regions (
        room TEXT NOT NULL, sender TEXT NOT NULL, name TEXT NOT NULL,
        lawd_code TEXT NOT NULL, updated_at INTEGER NOT NULL,
        PRIMARY KEY (room, sender))""")


def _scope(room: str, sender: str) -> None:
    if not room.strip() or not sender.strip():
        raise RealEstateError("부동산 조회는 채팅방과 발신자가 확인된 경우에만 사용할 수 있습니다.")


def resolve_district(text: str) -> District:
    value = " ".join(text.split())
    if not value or len(value) > 40:
        raise RealEstateError("지역은 서울 자치구 또는 법정동 5자리 코드로 입력하세요. 예: 부 지역 강남구")
    if re.fullmatch(r"[0-9]{5}", value):
        return District(CODE_TO_SEOUL.get(value, f"법정동코드 {value}"), value)
    if value.startswith("서울특별시 "):
        value = value[len("서울특별시 "):]
    elif value.startswith("서울 "):
        value = value[len("서울 "):]
    if value in SEOUL_CODES:
        return District("서울 " + value, SEOUL_CODES[value])
    raise RealEstateError("현재 지명 검색은 서울 25개 구만 지원합니다. 그 외 지역은 법정동코드 앞 5자리를 입력하세요.")


def get_saved_district(db: sqlite3.Connection, room: str, sender: str) -> District | None:
    _scope(room, sender)
    row = db.execute(
        "SELECT name,lawd_code FROM real_estate_regions WHERE room=? AND sender=?",
        (room, sender)
    ).fetchone()
    return District(*row) if row is not None else None


def save_district(db: sqlite3.Connection, room: str, sender: str, district: District) -> None:
    _scope(room, sender)
    db.execute("""INSERT INTO real_estate_regions(room,sender,name,lawd_code,updated_at)
        VALUES(?,?,?,?,strftime('%s','now'))
        ON CONFLICT(room,sender) DO UPDATE SET name=excluded.name,
            lawd_code=excluded.lawd_code, updated_at=excluded.updated_at""",
        (room, sender, district.name, district.code))


def region_help(db: sqlite3.Connection, room: str, sender: str) -> str:
    region = get_saved_district(db, room, sender)
    current = f"{region.name} ({region.code})" if region else "미설정"
    return "\n".join((
        "📍 부동산 실거래가 조회 안내",
        f"현재 조회 지역: {current}",
        "부 지역 강남구  → 지역 저장",
        "부 매매 강남구  → 매매 실거래가",
        "부 전세 강남구  → 전세 실거래가",
        "부 월세 강남구  → 월세 실거래가",
        "부 매매 강남구 래미안  → 단지명 포함 검색",
        "지역 저장 후: 부 시세 / 부 전세 / 부 월세",
        "※ 서울 외 지역: 법정동코드 앞 5자리 사용",
        "※ 최초 이용 시 MOLIT_API_KEY 설정 필요",
    ))


def parse_transaction_query(db: sqlite3.Connection, room: str, sender: str,
                            argument: str) -> tuple[str, District, str]:
    """명령 유형과 명시적 지역(또는 사용자별 저장 지역), 선택적 단지명을 구분."""
    _scope(room, sender)
    parts = " ".join(argument.split()).split(" ")
    action = parts[0] if parts else ""
    if action == "실거래조회":
        parts = parts[1:]
        action = parts.pop(0) if parts else ""
    else:
        parts = parts[1:]
    if action not in {"매매", "시세", "전세", "월세"}:
        raise RealEstateError("조회 방법: 부 매매 강남구 / 부 전세 강남구 / 부 월세 강남구")
    kind = "매매" if action == "시세" else action
    tail = parts
    region = None
    apartment = ""
    if tail:
        if tail[0] in {"서울", "서울특별시"} and len(tail) >= 2:
            candidate = " ".join(tail[:2])
            rest = tail[2:]
        else:
            candidate = tail[0]
            rest = tail[1:]
        try:
            region = resolve_district(candidate)
        except RealEstateError:
            # 지명 오타를 단지명으로 오인하지 않는다. '단지' 접두어는 명확하게 구별한다.
            if tail[0] == "단지":
                apartment = " ".join(tail[1:])
            else:
                raise
        else:
            apartment = " ".join(rest)
    if region is None:
        region = get_saved_district(db, room, sender)
    if region is None:
        raise RealEstateError("조회 지역이 미설정입니다. '부 지역 강남구'로 설정하거나 '부 매매 강남구'로 조회하세요.")
    if apartment and (len(apartment) > 40 or not re.fullmatch(r"[가-힣A-Za-z0-9()\s·._-]+", apartment)):
        raise RealEstateError("단지명은 특수기호 없이 40자 이내로 입력하세요.")
    if tail and tail[0] == "단지" and not apartment:
        raise RealEstateError("검색할 단지명을 입력하세요.")
    return kind, region, apartment


def _fetch_xml(endpoint: str, params: dict[str, str | int]) -> ET.Element:
    if not endpoint.startswith("https://apis.data.go.kr/1613000/"):
        raise RealEstateError("허용되지 않은 실거래가 제공 주소입니다.")
    request = Request(endpoint + "?" + urlencode(params), headers={"User-Agent": "AngaeBotBridge/RealEstate-1.0"})
    try:
        with urlopen(request, timeout=4.5) as response:
            raw = response.read(3_000_001)
        if len(raw) > 3_000_000:
            raise RealEstateError("실거래가 응답 크기가 허용 범위를 초과했습니다.")
        root = ET.fromstring(raw)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, ET.ParseError) as exc:
        if isinstance(exc, RealEstateError):
            raise
        raise RealEstateError("국토교통부 실거래가 API 연결 또는 응답 오류입니다.") from None
    code = (root.findtext(".//resultCode") or "").strip()
    if code not in {"00", "000", "0"}:
        raise RealEstateError("국토교통부 실거래가 API 요청이 거부되었습니다. 공공데이터 API 키/승인 상태를 확인하세요.")
    if root.find(".//body") is None:
        raise RealEstateError("국토교통부 실거래가 API 결과 형식이 올바르지 않습니다.")
    return root


def _xml_text(item: ET.Element, *names: str) -> str:
    for name in names:
        value = item.findtext(name)
        if value is not None and value.strip():
            return value.strip()
    return ""


def _positive_int(text: str, *, allow_zero: bool = False) -> int:
    value = int(text.replace(",", "").strip())
    if value < 0 or (value == 0 and not allow_zero):
        raise ValueError("invalid amount")
    return value


def _deal_from_item(item: ET.Element, kind: str) -> Deal | None:
    if _xml_text(item, "cdealType", "해제여부").upper() in {"O", "Y", "1"}:
        return None
    try:
        year = int(_xml_text(item, "dealYear", "년"))
        month = int(_xml_text(item, "dealMonth", "월"))
        day = int(_xml_text(item, "dealDay", "일"))
        date = datetime(year, month, day).strftime("%Y-%m-%d")
        apartment = _xml_text(item, "aptNm", "아파트")
        area = float(_xml_text(item, "excluUseAr", "전용면적"))
        floor = _xml_text(item, "floor", "층") or "-"
        if not apartment or not (0 < area < 1000):
            return None
        if kind == "매매":
            return Deal(date, apartment, area, floor,
                        _positive_int(_xml_text(item, "dealAmount", "거래금액")))
        monthly = _positive_int(_xml_text(item, "monthlyRent", "월세금액"), allow_zero=True)
        if (kind == "전세" and monthly != 0) or (kind == "월세" and monthly == 0):
            return None
        return Deal(date, apartment, area, floor,
                    _positive_int(_xml_text(item, "deposit", "보증금")), monthly)
    except (ValueError, TypeError, OverflowError):
        return None


def _month_codes(count: int = 3) -> tuple[str, ...]:
    now = datetime.now(SEOUL_TZ)
    start = now.year * 12 + now.month - 1
    return tuple(f"{(start - i) // 12:04d}{(start - i) % 12 + 1:02d}" for i in range(count))


def fetch_month(kind: str, region: District, month: str, service_key: str) -> list[Deal]:
    endpoint = SALE_ENDPOINT if kind == "매매" else RENT_ENDPOINT
    rows: list[Deal] = []
    for page in range(1, MAX_PAGES + 1):
        root = _fetch_xml(endpoint, {
            "serviceKey": service_key, "LAWD_CD": region.code,
            "DEAL_YMD": month, "pageNo": page, "numOfRows": 1000
        })
        total_text = root.findtext(".//totalCount")
        if total_text is None or not total_text.strip().isdigit():
            raise RealEstateError("실거래가 총건수 자료가 누락되었습니다.")
        total = int(total_text)
        items = root.findall(".//items/item")
        if total > 0 and not items:
            raise RealEstateError("실거래가 페이지 자료가 누락되었습니다.")
        for item in items:
            deal = _deal_from_item(item, kind)
            if deal is not None:
                rows.append(deal)
        if total <= page * 1000:
            return rows
    raise RealEstateError("지역·월별 거래 건수가 조회 제한을 초과했습니다. 다른 법정동코드로 좁혀 조회하세요.")


def _money(amount: int) -> str:
    eok, man = divmod(amount, 10000)
    if eok:
        return f"{eok:,}억" + (f" {man:,}만원" if man else "원")
    return f"{man:,}만원"


def transaction_report(kind: str, region: District, apartment: str = "") -> str:
    """공식 신고자료 외에는 보간/추정하지 않는다. 요청마다 신선한 최근 3개월을 조회."""
    key = os.environ.get("MOLIT_API_KEY", "").strip()
    if not key:
        raise RealEstateError("공공데이터 API 키가 없습니다. S20+의 .env에 MOLIT_API_KEY를 설정하세요.")
    if len(key) > 500 or not re.fullmatch(r"[A-Za-z0-9%+/=_-]+", key):
        raise RealEstateError("MOLIT_API_KEY 값이 유효하지 않습니다. 공공데이터포털 발급 키를 확인하세요.")
    months = _month_codes()
    deals: list[Deal] = []
    for month in months:
        deals.extend(fetch_month(kind, region, month, key))
    if apartment:
        deals = [d for d in deals if apartment.casefold() in d.apartment.casefold()]
    deals.sort(key=lambda d: (d.date, d.apartment, d.floor), reverse=True)
    header = f"🏠 아파트 {kind} 실거래가 · {region.name}"
    if apartment:
        header += f"\n🔎 단지명 포함: {apartment}"
    lines = [header, f"📆 계약 기간: {months[-1][:4]}.{months[-1][4:]}~{months[0][:4]}.{months[0][4:]}"]
    if not deals:
        lines.append("📭 이 조건의 신고 실거래 내역이 없습니다.")
    else:
        for index, deal in enumerate(deals[:MAX_RESULTS], 1):
            date = deal.date[5:].replace("-", "/")
            if kind == "매매":
                amount = _money(deal.amount)
            elif kind == "전세":
                amount = "보증금 " + _money(deal.amount)
            else:
                amount = f"보증금 {_money(deal.amount)} / 월 {_money(deal.monthly)}"
            lines.append(
                f"{index}. {deal.apartment} · 전용 {deal.area:g}㎡ · {deal.floor}층"
                f"\n   {date} 계약 · {amount}"
            )
        lines.append(f"📊 조건 일치 {len(deals)}건 중 최근 {min(MAX_RESULTS, len(deals))}건")
    lines.extend((
        "📡 국토교통부 아파트 실거래가 공개자료",
        "※ 신고 지연·정정·취소 가능 · 현재 매물 호가/감정가 아님",
    ))
    return "\n".join(lines)
