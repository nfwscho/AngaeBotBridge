"""
앙개봇 주식 공급자 진단기 — 전체 기능 및 보안
1. 한국 005930 네이버 정규/시간외 응답과 미국 MU 네이버 해외 주식 폴링·기본 경로의 공개 데이터 형태를 한 번씩 점검한다.
2. 프리/애프터 실제 네트워크 조회가 가능한지 운영자가 확인할 수 있도록 HTTP 응답 상태, 티커, 시장세션, 시세 필드명, 거래시간을 기록한다.
3. 네이버 공개 API 외의 URL을 받지 않으며 사용자 식별자, 인증키, .env, 토큰, 개인 DB, 사용자 메시지에 접근하지 않는다.
4. 가격 등 민감하지 않은 공개 시세도 상세값을 로그에 출력하지 않으며 데이터 스키마의 키와 길이만 표시한다.
5. 타임아웃 3초와 응답 180KB로 제한하고 모든 네트워크 오류를 분리해 보고한다.
6. 기존 앙개봇 명령/서비스를 실행·재시작하지 않으며 S20+ DB/로그/.env/Android Bridge를 수정하지 않는다.
7. GitHub Actions에서 비차단 진단으로 실행 가능하며 실제 API 불가 시 정상 CI를 실패로 판정하지 않는다.
8. 추가된 3대 섹터 종목의 Nasdaq .O 및 NYSE .N 조회 지원을 대표 종목 ARM/MRVL/QCOM/TXN/TSM/NOW/GLW/LITE에서 공개 응답 상태와 필드명만 점검한다.
9. 응답 가격·개인정보·사용자 토큰을 기록하지 않으며 기존 한국 삼성전자·미국 MU 양쪽 경로 진단을 삭제하지 않는다.
"""
from __future__ import annotations

import json
from urllib.request import Request, urlopen

ENDPOINTS = (
    ('KR_SAMSUNG', 'https://polling.finance.naver.com/api/realtime/domestic/stock/005930'),
    ('US_MU_POLL', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=MU.O'),
    ('US_MU_BASIC', 'https://stock.naver.com/api/securityService/stock/MU.O/basic'),
    ('US_ARM_O', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=ARM.O'),
    ('US_MRVL_O', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=MRVL.O'),
    ('US_QCOM_O', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=QCOM.O'),
    ('US_TXN_O', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=TXN.O'),
    ('US_TSM_N', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=TSM.N'),
    ('US_NOW_N', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=NOW.N'),
    ('US_GLW_N', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=GLW.N'),
    ('US_LITE_O', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=LITE.O'),
)


def main():
    for label, url in ENDPOINTS:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; AngaeBotBridge/StockDiagnostics)',
                       'Accept': 'application/json',
                       'Referer': 'https://stock.naver.com/'}
            with urlopen(Request(url, headers=headers), timeout=3.0) as response:
                raw = response.read(180001)
                code = response.status
            if len(raw) > 180000:
                raise ValueError('응답 크기 초과')
            payload = json.loads(raw)
            rows = []
            if isinstance(payload, dict):
                rows = payload.get('datas') or payload.get('data') or []
                if isinstance(rows, dict):
                    rows = [rows]
                if not isinstance(rows, list):
                    rows = []
            item = next((p for p in rows if isinstance(p, dict)), None)
            if item is None and isinstance(payload, dict):
                item = payload
            fields = ('reutersCode', 'symbolCode', 'itemCode', 'currencyType',
                      'closePrice', 'marketSessionType', 'marketStatus',
                      'localTradedAt', 'overMarketPriceInfo', 'preMarketPriceInfo',
                      'afterMarketPriceInfo', 'lastTradeTimestamp')
            keys = ','.join(k for k in fields if isinstance(item, dict) and k in item)
            identity = (item.get('reutersCode') or item.get('symbolCode') or
                        item.get('itemCode')) if isinstance(item, dict) else None
            session = item.get('marketSessionType') if isinstance(item, dict) else None
            extended = item.get('overMarketPriceInfo') if isinstance(item, dict) else None
            extended_fields = ','.join(k for k in ('tradingSessionType','overPrice','localTradedAt')
                                       if isinstance(extended, dict) and k in extended)
            print(f'{label}: HTTP {code} type={type(payload).__name__} identity={identity} '
                  f'session={session} fields={keys} extended_fields={extended_fields}')
        except Exception as exc:
            print(f'{label}: unavailable ({type(exc).__name__})')


if __name__ == '__main__':
    main()
