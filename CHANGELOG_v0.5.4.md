# AngaeBot Python Core v0.5.4 — SQLite 연결 종료·배포 안정성

## 수정 사항
- Termux/Python 3.13의 SQLite ResourceWarning: unclosed database 경고의 원인을 확인하고 실제 연결을 닫도록 수정.
- 테스트의 with sqlite3.connect(...) as db는 트랜잭션만 관리하므로 contextlib.closing(sqlite3.connect(...)) as db로 변경.
- 6개 기존 테스트 파일의 모든 해당 SQL 읽기 경로에 closing을 적용하고 기존 테스트/응답/로그 검사를 보존.
- 신규 test_sqlite_cleanup.py: API 인증·계산·중복요청·주식그룹 CRUD·한글 분석·실패 처리 시 SQLite 연결 close 호출 검증.
- 과거 128개 테스트와 신규 1개를 포함해 총 129개, 기존 경고 26건 → 0건을 로컬 Python 3.13에서 확인.
- 기존 v0.5.3 Termux 안전 배포를 확장해 v0.5.4 건강검사/시간대 처리/백업/실패 롤백 유지.

## 변경하지 않은 기능
- 계산·시간·서버 상태·운영 통계·원래 카카오톡 자동응답, UI, 메모리7, 반도체, 미국시총10.
- 한글 종목명/사용자 별칭, 최근 5거래일 종가, 1개월·3개월 수익률 및 연율화 실현변동성.
- SQLite 기존 운영 DB/jobs/events/그룹·로그·인증키·.env·SSH·watchdog·Android APK.
- OpenAI API OFF와 가격 알림·예약 발송·자동매매 기능 미구현.

## 배포
- git pull --ff-only origin main 후 scripts/deploy-v0.5.4.ps1 실행.
- 실제 S20+ 서비스 환경에서 전체 테스트가 완료되어야 설치 완료로 간주.
