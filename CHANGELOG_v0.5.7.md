# AngaeBot v0.5.7 — Naver Domestic KRX Realtime Status + NXT Separation

## 변경사항
- 삼성전자/하이닉스 현재가에는 네이버 공개 polling API를 우선 사용하고, 기존 모바일 기본 시세 API → Yahoo Finance 폴백을 보존합니다.
- 폴링 데이터가 장중 3분 이상 오래된 경우 모바일 JSON을 추가로 조회하여 더 최근 체결 시각을 선택합니다.
- 네이버의 거래소 지연 메타데이터(분), KRX 시장상태 및 거래시각, 폴링 응답 생성시각을 표시합니다.
- 정상적으로 지연 0분·장 OPEN·체결시각 3분 이내·서버응답 3분 이내인 경우에만 **'네이버 실시간표시(지연 0분)'**으로 표기합니다. 공인 실시간 틱 공급임을 보증하지 않습니다.
- KRX 장마감 후에는 종가와 시간외 가격을 다른 줄로 보여주며 시간외에서 거래소를 확인하지 못하면 NXT라고 임의 표기하지 않습니다.
- `nxtOverMarketPriceInfo`처럼 NXT가 명시된 경우에만 'NXT'를 붙입니다. 시간외 데이터가 이전 본장 거래보다 오래됐거나 % 정합성이 안 맞으면 제외합니다.
- 기존 메모리7 1~8번, 관심그룹 번호(최대 10), 최근사용 명령, 미국·일본 6종목, 5일/1·3개월 분석, 조회용 무료 공급자, 기존 로그/SQLite/AI OFF/배터리 출력 그대로 유지합니다.
- 네이버 공개 API는 비공식이며 구조 변경·접근 제한·지연 가능성이 있습니다. 이용조건을 준수하고 재배포/상업적 사용은 별도 권리 확인이 필요합니다.
- 백그라운드 조회나 상시 연결을 추가하지 않았습니다. 명령마다 요청하고 기존 30초 메모리 캐시를 유지합니다.

## 버전
- Python Core 0.5.7; Android Bridge 0.4.5 **그대로**.
- Python 148 tests passed including new Naver realtime/closed/after-market/fallback tests; ResourceWarning as error passes.
