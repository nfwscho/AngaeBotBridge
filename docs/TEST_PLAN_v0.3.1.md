# 앙개봇 v0.3.1 24시간 안정화 테스트

1. Python `unittest discover`: v0.3.0 API/AI/계산/기존 watchdog 회귀 테스트 모두 통과.
2. `test_stability`: 파일 잠금 중복 차단, 서버 로그 보관, watchdog backoff, watchdog 로그 원본 보존, 진단 개인정보 비노출.
3. 기존 카톡 명령 네 개 계산/시간/상태/AI상태 및 Android 테스트를 검증.
4. `diagnose-autostart.py`에서 core/watchdog 실행 중, 8022 OPEN, HEALTH_OK version=0.3.1.
5. `install-stability.sh` 실행 후 현재 SSH 세션이 끊기지 않았는지 확인.
6. 스마트폰 재부팅(사용자가 원할 때) 이후 boot.log의 새로운 BOOT_STARTED/BOOT_FINISHED 시각으로 실제 부팅 트리거 확인.
7. boot.log 실패 시 권한/배터리/앱 백그라운드 실행 정책 점검; 자동 복구 성공 주장 금지.
8. 용량이 8 MiB 이상인 서버 로그는 다음 core 재시작 때 archive로 이동하며, 이전 로그 모두 보존. watchdog는 2 MiB를 넘으면 기록 시 archive로 이동.
9. `.env`, `.env.backup.*`, `data/`, `logs/`는 GitHub에 업로드하지 않는다.
10. `sshd`는 기존 연결을 유지하고 설치 중 중지/재시작하지 않는다.
