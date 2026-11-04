"""
앙개봇 v0.4.3 무료 시세 제공처 읽기 전용 진단 — 전체 기능 상세 설명
1. 한국 삼성전자/하이닉스 네이버 금융 JSON 접근 가능 여부를 확인한다.
2. 일본 키오시아 Yahoo Finance Chart, Yahoo Japan, 라쿠텐 증권 본장 공개 페이지의 접속 여부를 확인한다.
3. 해당 공개 페이지에서 검증된 가격과 최근 거래일만 제한적으로 출력한다.
4. HTTP 403/429, 응답 형식 오류, 시세 지연 등을 종목/공급자별로 구분해 표시한다.
5. .env 토큰, 사용자 메신저 대화, SQLite DB, 기존 서버/Android 로그에 접근하거나 변경하지 않는다.
6. 공개된 고정 URL 이외 임의 주소를 호출하거나 주식 거래/AI API를 실행하지 않는다.
7. 결과를 서버 상태로 착각하지 않도록 단발성 조회이며 비공식 시세임을 표시한다.
8. Python 표준 라이브러리만 사용하고 기존 설치된 FastAPI/패키지를 변경하지 않는다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.market import WATCHLIST, fetch_naver_quote, fetch_yahoo_quote, fetch_yahoo_japan_quote, fetch_rakuten_quote, quote_line


def safe_error(error: Exception) -> str:
    current: BaseException | None = error
    types: list[str] = []
    for _ in range(3):
        if current is None:
            break
        code = getattr(current, 'code', None)
        types.append(f'HTTP {code}' if isinstance(code, int) else type(current).__name__)
        current = current.__cause__
    return ' / '.join(types)


def main() -> None:
    print('AngaeBot v0.4.3 Stock Provider Diagnostics (read only)')
    sources = [
        ('삼성전자 · 네이버', WATCHLIST[0], fetch_naver_quote),
        ('하이닉스 · 네이버', WATCHLIST[1], fetch_naver_quote),
        ('키오시아 · Yahoo Global', WATCHLIST[5], fetch_yahoo_quote),
        ('키오시아 · Yahoo Japan', WATCHLIST[5], fetch_yahoo_japan_quote),
        ('키오시아 · Rakuten Japan', WATCHLIST[5], fetch_rakuten_quote),
    ]
    for name, stock, fetch in sources:
        try:
            quote = fetch(stock)
            print(f'[OK] {name}: {quote_line(quote)} / {quote.market_time.date()}')
        except Exception as error:
            print(f'[FAIL] {name}: {safe_error(error)}')
    print('참고: 비공식/지연 시세. 실제 가격 검증에는 증권사·거래소 데이터를 사용하세요.')


if __name__ == '__main__':
    main()
