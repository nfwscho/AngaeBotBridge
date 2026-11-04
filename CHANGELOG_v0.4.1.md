# AngaeBot v0.4.1 — 무료 주식 메모리7 시세 조회

## 기존 기능 보존
- 기존 Android NotificationListener/RemoteInput/정확한 채팅방·발신자 허용/SQLite 로깅/명령 TTL 중복차단 유지.
- v0.4.0 전체 운영 명령·계산·시간·AI 연결(OFF 기본값)·서버상태/인증/DB/부팅 서비스 유지.
- Python 기존 jobs/events와 Android 알림/수신/응답/실패 로그를 변경하거나 삭제하지 않음.
- S20+ FastAPI는 그대로 127.0.0.1:8765에만 바인딩하고 X-AngaeBot-Token으로 인증.

## 추가 기능
- `앙개야 주식 메모리7`, `앙개야 메모리7`: 삼성전자·SK하이닉스·마이크론·SKHY ADR·샌디스크·키오시아·씨게이트·웨스턴디지털 현재 제공 가격/전일종가 대비 등락률 조회.
- 원/달러/엔 표시, 상승▲/하락▽/보합－, 시장별 최근 거래일, 시세 지연 안내.
- 8개 종목 병렬 조회 최대 4개, 3.2초 요청 타임아웃, 30초 메모리 캐시; 각 티커 실패 시 '조회 불가', 모두 실패 시 오류 기록.
- 무료 비공식 Yahoo Finance Chart API 사용. 공급자 접속 제한·요청 차단·시세 지연 가능. 데이터 소스 가용성 및 상업용 재배포 권리는 보장하지 않음.
- OpenAI API/유료 주식 API 없이 동작. API 키 불필요.
- 버전 0.4.1, Android versionCode 5, 새 명령을 포함한 도움말과 Python 연결 허용 명령 추가.
- Windows 단일 배포 스크립트 `scripts/deploy-v0.4.1.ps1` 제공. Termux 소스 백업, 전체 unittest, health 검사 후 적용.

## 확인되지 않은 항목
- 현재 실행 환경은 Yahoo Finance 외부 시세를 직접 가져오지 못하므로 실시간 실제 값은 S20+에서 최초 확인이 필요.
- Google Play Termux 부팅 자동 실행/SSH 부팅 초기화는 별도의 실기기 재부팅으로 검증 필요.
- 예약/스케줄러의 카카오톡 자발적 발신은 알림 RemoteInput만으로 제공되지 않으므로 아직 구현하지 않음.
