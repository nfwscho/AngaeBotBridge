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
10. NYSE .N 폴링 응답이 빈 경우 basic .N과 bare 티커만 제한적으로 확인하고 JSON 루트 키·항목 개수만 출력한다.
11. 나머지 허용 NYSE 종목의 bare-code 공개 폴링이 실제 종목을 반환하는지 역시 가격/토큰 없이 항목 개수와 종목코드만 기록한다.
12. 일부 NYSE ORCL/ANET/DELL 폴링의 datas=[]인 경우 사용할 수 있는 basic bare-code 응답을 실제 GitHub 네트워크로 확인한다.
13. 네이버 NYSE 조회가 차단된 ORCL/ANET/DELL의 나스닥 웹 공개 secondaryData·marketStatus 구조를 가격·개인정보 없이 확인한다.
14. 기본 CI는 기존 한국 005930·미국 MU 폴링/기본 3개 진단만 실행하고 --full 명시 시에만 종목별 상세 진단을 추가해 불필요한 요청과 CI 지연을 줄인다.
15. 2026-11-06 KRX 장마감 기준가 누락을 해결하기 위해 삼성전자·SK하이닉스의 일봉 endpoint 응답 형태·거래일·필드명만 일시 진단하고 원문 가격은 기록하지 않는다.
16. 2026-11-06 공시된 KRX 종가와 검증값 동일 여부만 불리언으로 확인하고 원본 체결가/가격은 GitHub 로그에 남기지 않는다.
17. 정규장 종가/시간외 최종가 필드 분리를 위해 별도 Naver KRX 종목 상세·일별시세·스냅샷·모바일 기본 API 응답의 최상위 및 중첩 *필드명*만 일시 진단한다.
18. KRX 정규장 15:30 시세를 확인할 수 있는 공개 5분봉/분봉 엔드포인트 응답의 시계열 구조·행 키만 점검하고 실제 가격은 인쇄하지 않는다.
"""
from __future__ import annotations

import json
from urllib.request import Request, urlopen

ENDPOINTS = (
    ('KR_SAMSUNG', 'https://polling.finance.naver.com/api/realtime/domestic/stock/005930'),
    ('US_MU_POLL', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=MU.O'),
    ('US_MU_BASIC', 'https://stock.naver.com/api/securityService/stock/MU.O/basic'),
    ('KR_SAMSUNG_DAY', 'https://api.stock.naver.com/chart/domestic/item/005930?periodType=dayCandle'),
    ('KR_HYNIX_DAY', 'https://api.stock.naver.com/chart/domestic/item/000660?periodType=dayCandle'),
    ('KR_SAMSUNG_DETAIL', 'https://api.stock.naver.com/api/domestic/detail/005930/detail?codeType=KRX'),
    ('KR_HYNIX_DETAIL', 'https://api.stock.naver.com/api/domestic/detail/000660/detail?codeType=KRX'),
    ('KR_SAMSUNG_SISE', 'https://api.stock.naver.com/api/domestic/detail/005930/siseDay?pageSize=20&bizdate=20261106'),
    ('KR_HYNIX_SISE', 'https://api.stock.naver.com/api/domestic/detail/000660/siseDay?pageSize=20&bizdate=20261106'),
    ('KR_SAMSUNG_SNAPSHOT', 'https://api.stock.naver.com/api/stockSecurity/items/v2/domestic/005930/price-snapshot'),
    ('KR_HYNIX_SNAPSHOT', 'https://api.stock.naver.com/api/stockSecurity/items/v2/domestic/000660/price-snapshot'),
    ('KR_SAMSUNG_FRONT', 'https://m.stock.naver.com/front-api/stock/domestic/basic?code=005930&endType=stock'),
    ('KR_HYNIX_FRONT', 'https://m.stock.naver.com/front-api/stock/domestic/basic?code=000660&endType=stock'),
    ('KR_SAMSUNG_MINUTE', 'https://m.stock.naver.com/front-api/chart/domestic/stock/end?code=005930&chartInfoType=item&scriptChartType=candleMinuteFive'),
    ('KR_HYNIX_MINUTE', 'https://m.stock.naver.com/front-api/chart/domestic/stock/end?code=000660&chartInfoType=item&scriptChartType=candleMinuteFive'),
    ('KR_SAMSUNG_MIN2', 'https://api.stock.naver.com/chart/domestic/item/005930?periodType=minuteCandle'),
    ('KR_HYNIX_MIN2', 'https://api.stock.naver.com/chart/domestic/item/000660?periodType=minuteCandle'),
)
# 기존 CI에서는 원래 세 개의 진단 요청만 실행한다. 확대 실측은 --full 명령으로
# 명시적으로 선택한 경우에만 수행해 요청 제한/공급자 부하/CI 지연을 방지한다.
_FULL_ENDPOINTS = (
    ('US_ARM_O', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=ARM.O'),
    ('US_MRVL_O', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=MRVL.O'),
    ('US_QCOM_O', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=QCOM.O'),
    ('US_TXN_O', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=TXN.O'),
    ('US_TSM_N', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=TSM.N'),
    ('US_NOW_N', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=NOW.N'),
    ('US_GLW_N', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=GLW.N'),
    ('US_LITE_O', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=LITE.O'),
    ('US_TSM_N_BASIC', 'https://stock.naver.com/api/securityService/stock/TSM.N/basic'),
    ('US_NOW_N_BASIC', 'https://stock.naver.com/api/securityService/stock/NOW.N/basic'),
    ('US_GLW_N_BASIC', 'https://stock.naver.com/api/securityService/stock/GLW.N/basic'),
    ('US_TSM_NAQ', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=TSM'),
    ('US_NOW_NAQ', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=NOW'),
    ('US_LLY_NAQ', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=LLY'),
    ('US_CRM_NAQ', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=CRM'),
    ('US_ORCL_NAQ', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=ORCL'),
    ('US_IBM_NAQ', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=IBM'),
    ('US_GLW_NAQ', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=GLW'),
    ('US_ANET_NAQ', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=ANET'),
    ('US_VRT_NAQ', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=VRT'),
    ('US_DELL_NAQ', 'https://stock.naver.com/api/polling/worldstock/stock?reutersCodes=DELL'),
    ('US_TSM_BASIC', 'https://stock.naver.com/api/securityService/stock/TSM/basic'),
    ('US_GLW_BASIC', 'https://stock.naver.com/api/securityService/stock/GLW/basic'),
    ('US_ORCL_BASIC', 'https://stock.naver.com/api/securityService/stock/ORCL/basic'),
    ('US_ANET_BASIC', 'https://stock.naver.com/api/securityService/stock/ANET/basic'),
    ('US_DELL_BASIC', 'https://stock.naver.com/api/securityService/stock/DELL/basic'),
)


def main(*, full: bool = False):
    for label, url in (ENDPOINTS + _FULL_ENDPOINTS if full else ENDPOINTS):
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
            root_keys = ','.join(list(payload.keys())[:8]) if isinstance(payload, dict) else ''
            item_count = len(rows) if isinstance(rows, list) else 0
            if label.startswith('KR_') and label.endswith(('_MINUTE','_MIN2')):
                value = payload.get('result', payload.get('data', payload)) if isinstance(payload, dict) else payload
                if isinstance(value, dict):
                    summary = {k: type(v).__name__ for k, v in value.items()}
                    samples = next((v for v in value.values() if isinstance(v, list)), [])
                else:
                    summary = {}
                    samples = value if isinstance(value, list) else []
                sample = samples[-1] if samples else None
                print(f'{label}_STRUCT: payload={type(payload).__name__} '
                      f'value={type(value).__name__} types={summary} '
                      f'rows={len(samples)} sample_fields={list(sample.keys()) if isinstance(sample, dict) else type(sample).__name__}')
            if label.startswith('KR_') and label.endswith(('_DETAIL','_SISE','_SNAPSHOT','_FRONT')):
                # 타사 공개 JSON의 원본 값은 출력하지 않고 필드 이름과
                # 응답 구조만 확인해 별도 KRX 종가 필드를 찾는다.
                top = ','.join(list(payload.keys())[:35]) if isinstance(payload, dict) else ''
                nested = []
                if isinstance(payload, dict):
                    for key, val in list(payload.items())[:15]:
                        if isinstance(val, dict):
                            nested.append(key + ': ' + ','.join(list(val.keys())[:100]))
                        elif isinstance(val, list):
                            sample = next((x for x in val if isinstance(x, dict)), {})
                            nested.append(key + '[dict]: ' + ','.join(list(sample.keys())[:25]))
                print(f'{label}_FIELDS: top={top} nested={nested[:10]}')
            if label.endswith('_DAY') and isinstance(payload, dict):
                # 공개 일봉 구조를 파악하되 주가/잔고/사용자식별자는 출력하지 않는다.
                day_rows = payload.get('priceInfos', payload.get('data', payload.get('result', [])))
                if isinstance(day_rows, dict):
                    day_rows = day_rows.get('priceInfos', [])
                if not isinstance(day_rows, list):
                    day_rows = []
                samples = day_rows[-2:] if day_rows else []
                fields_dates = [(','.join(str(k) for k in row.keys()),
                                str(row.get('localDate') or row.get('tradedAt') or row.get('date') or '')[:30])
                                for row in samples if isinstance(row, dict)]
                expected = {'KR_SAMSUNG_DAY': 188700, 'KR_HYNIX_DAY': 1132000}.get(label)
                last = next((row for row in reversed(day_rows)
                             if isinstance(row, dict) and str(row.get('localDate')) == '20261106'), None)
                observed = None
                if last is not None:
                    try:
                        observed = float(str(last.get('closePrice', '')).replace(',', ''))
                    except (ValueError, TypeError):
                        pass
                exchange = payload.get('stockExchangeType')
                print(f'{label}_SHAPE: total={len(day_rows)} samples={fields_dates} '
                      f'exchange={exchange} known_20261106_krx_close_match={observed == expected}')
            print(f'{label}: HTTP {code} root_keys={root_keys} item_count={item_count} type={type(payload).__name__} identity={identity} '
                  f'session={session} fields={keys} extended_fields={extended_fields}')
        except Exception as exc:
            print(f'{label}: unavailable ({type(exc).__name__})')


    # 기존 네이버 비차단 진단에 더해 미국 거래소 공개 응답의 세션 구조만 확인.
    # 가격이나 사용자 데이터는 출력하지 않는다.
    for ticker in (('ORCL', 'ANET', 'DELL') if full else ()):
        uri = f'https://api.nasdaq.com/api/quote/{ticker}/info?assetclass=stocks'
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/145.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Origin': 'https://www.nasdaq.com',
                'Referer': 'https://www.nasdaq.com/',
            }
            with urlopen(Request(uri, headers=headers), timeout=3.0) as response:
                raw = response.read(180001)
                code = response.status
            if len(raw) > 180000:
                raise ValueError('응답 크기 초과')
            payload = json.loads(raw)
            data = payload.get('data') if isinstance(payload, dict) else None
            primary = data.get('primaryData') if isinstance(data, dict) else None
            secondary = data.get('secondaryData') if isinstance(data, dict) else None
            fields = ','.join(secondary.keys()) if isinstance(secondary, dict) else ''
            print(f'US_{ticker}_NASDAQ: HTTP {code} symbol='
                  f'{data.get("symbol") if isinstance(data, dict) else None} '
                  f'marketStatus={data.get("marketStatus") if isinstance(data, dict) else None} '
                  f'primary={isinstance(primary, dict)} secondary_keys={fields}')
        except Exception as exc:
            print(f'US_{ticker}_NASDAQ: unavailable ({type(exc).__name__})')


if __name__ == '__main__':
    import sys
    main(full='--full' in sys.argv[1:])
