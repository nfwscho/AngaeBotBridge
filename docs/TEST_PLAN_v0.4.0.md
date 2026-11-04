# AngaeBot v0.4.0 운영 명령 테스트 계획

## 자동검증

- Python `unittest discover`: 기존 인증·계산·시간·AI OFF·문맥·중복 방지·watchdog·로그 보존 46건과 신규 운영 8건 회귀 테스트.
- 새 API 인증 없으면 401, 셸 명령은 기존처럼 400.
- `통계`: jobs의 성공/실패·TOP5만 집계하고 같은 `(room,sender)`만 반환.
- `최근오류`: 실패 명령 5건 제한, 입력 인수 본문 제외, 다른 채팅방/발신자 기록 격리.
- `상세상태`: 상태 조회만 수행, SSH와 runit 변경/재시작하지 않음.
- `가동시간`: 프로세스 기반 경과시간으로 음수 처리/일·시·분·초 포맷 검증.
- jobs/events/AI DB 테이블 이전 데이터 보존, 동일 요청 ID 중복 저장 없음.
- Kotlin CommandParser 단독 컴파일·기존 알림 파서 테스트 보존.

## 실기기 검증

1. 기존 Android v0.3.0에서 `install -r`로 v0.4.0 업그레이드(데이터 보존).
2. Windows `scripts/deploy-v0.4.0.ps1`로 S20+ Termux에 Python 파일 4개 배포, 자동 백업·전체 테스트·core 재시작.
3. Python 전체 테스트 통과, core restart, `HEALTH_OK version=0.4.0`.
4. 카카오톡 테스트/계산/시간/서버상태/AI상태 기존 기능 유지.
5. 새 상세상태/통계/최근오류/가동시간·도움말 실기기 검증.
6. AI OFF 유지, 토큰/SQLite/로그 변경·삭제 없음 확인.
7. 실제 재부팅 후 자동 실행(후속 단계): 서버/SSH/Android 상태 별도 확인.
