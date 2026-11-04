# 앙개봇 Python Core v0.3.1 — 24시간 운영 안정화

기준: Android Bridge v0.3.0, Python Core v0.3.0. Android 소스·UI·카카오톡 수신/답장·모든 SQLite 로그·AI 설정값은 변경하지 않았습니다.

- **중복 실행 방지**: `scripts/run_core.py` 추가. Unix flock을 uvicorn PID가 상속해 runit/수동 프로세스 중복 실행 방지.
- **로그 보관**: 기존 `logs/server.log`는 서버 시작 시 8 MiB 이상이면 `logs/archive/`로 이동 후 새 로그에 이어 기록. watchdog.log는 기록 시 2 MiB 이상이면 archive에 보관. 보관본은 자동 삭제하지 않음.
- **감시기 강화**: v0.2.1의 기존 HEALTH_OK/HEALTH_FAILED/RESTART_REQUESTED 로그 유지, 지수 백오프(최대 300초), .env 토큰 재읽기.
- **부팅 관측**: `scripts/install-stability.sh` 실행 시 기존 boot 스크립트를 백업하고, boot.log에 실제 실행 시간과 SSH/서비스 상태 기록. SSH는 runit이 있으면 runit만 사용해 중복 daemon 경쟁 방지.
- **운영 진단**: `scripts/diagnose-autostart.py` 읽기 전용 상태조회(8022 TCP, health API, runit core/watchdog/sshd, 로그 아카이브, 부팅 실행 기록).
- **버전 표기**: Python Core health 및 `앙개야 서버상태` 응답을 v0.3.1로 표시. Android는 변경 없음(v0.3.0 유지).
- **회귀 테스트**: `core/tests/test_stability.py` 추가, 기존 테스트 계속 실행.

주의: Google Play Termux 앱이 Android 부팅 시 시작되지 않으면 스크립트만으로 해결할 수 없습니다. 완전 무인 부팅은 다음 실제 재부팅에서 확인해야 합니다. 기존 SSH 연결 중에는 별도 `sshd` 중지/재시작을 수행하지 않습니다.
