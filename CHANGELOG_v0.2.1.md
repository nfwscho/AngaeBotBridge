# 앙개봇 v0.2.1 — Termux 자동 시작·자동 복구 (2026-11-05)

## 추가된 기능
- `termux-services` / `runit`을 이용한 FastAPI 자동 재시작.
- 30초 간격 인증 health API 확인; 3회 연속 실패하면 재시작 요청.
- Google Play Termux 내장 boot 스크립트(`~/.termux/boot`) 등록.
- SSH 서버 부팅 재개, Wake Lock 설정 시도.
- `status-autostart.sh`, `restart-autostart.sh`, `stop-autostart.sh`, `resume-autostart.sh` 추가.
- 기존 `setup-boot.sh`를 하위 호환 진입점으로 유지.

## 변경사항과 보존 정책
- `core/scripts/start-termux.sh`: 기존 `logs/server.log` 누적을 유지하면서 `exec`로 uvicorn 직접 실행하여 runit 감시 호환성 개선.
- 기존 Python API / 인증키 / DB 스키마 / 전체 Android UI·로그·카카오톡 송수신 **변경 없음**.
- 기존 실행 중 서버가 있다면 서비스 활성화 전 수동 실행을 먼저 중단해야 포트 충돌을 피할 수 있음.
- 자동 복구는 Termux/run it 프로세스가 살아 있을 때만 보장 가능. Android 강제 종료·전원 문제는 대상 아님.
