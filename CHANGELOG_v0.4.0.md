# AngaeBot v0.4.0 — 카카오톡 운영 관리 명령

## 새 기능

- `앙개야 상세상태`: Python Core / watchdog / SSH(run: 상태), 로컬 SSH 8022 접속 여부, Python 프로세스 가동시간.
- `앙개야 통계`: 동일 채팅방·발신자의 **Python Core 명령만** 총계/성공/실패/상위 5개 집계.
- `앙개야 최근오류`: 동일 채팅방·발신자의 최근 실패 명령 5개, 시간·명령·짧은 오류 설명만 표시(입력 인수 원문 제외).
- `앙개야 가동시간`: 현재 FastAPI 프로세스 시작 시각(KST) 및 경과 시간.
- `앙개야 도움말`: 기존 도움말과 전체 명령 보존, 신규 운영 명령 목록 추가.

## 호환 및 보존

- 기존 Android UI, 카카오톡 NotificationListenerService, 방·발신자 허용목록, 호출어, 중복 감지, RemoteInput 빠른답장, Android SQLite/로그의 모든 기능 유지.
- 기존 Python 계산/시간/서버상태/AI상태/질문/요약/대화초기화, FastAPI 인증/health/jobs/events/AI DB 테이블·로그를 변경 없이 유지.
- AI는 기본 OFF. 신규 운영 명령은 AI/인터넷 API 없이 동작. OpenAI API 설치·호출·비용 발생 없음.
- `v0.3.1`의 runit/watchdog/SSH/boot 스크립트 및 로그 회전·중복 실행 방지 기능 유지.
- 운영 조회는 인증된 로컬 Python 명령 API를 통해서만 사용하며 SSH나 FastAPI를 제어하지 않음.
- Python 조회 결과는 요청 전까지 기록된 jobs를 사용하므로 통계에 **현재 조회 명령은 미포함**(요청 완료 후 기존 방식대로 jobs/events 기록).
- Android APK `versionCode 4` / `versionName 0.4.0`, 기존 앱 제거 없이 업데이트 가능.

## 검증

- Python `unittest` 전체 54건 통과(기존 46건 + 신규 운영 명령 8건).
- Kotlin CommandParser 단독 컴파일 확인. 전체 Android APK Gradle 빌드와 S20+ 실기기 동작은 사용자 환경에서 추가 확인 필요.
- Windows `scripts/deploy-v0.4.0.ps1` + Termux `core/scripts/apply-v0.4.0.sh`로 자동 백업·검증·배포 지원.
- 백업 및 설치 안내: `docs/UPGRADE_v0.4.0.md`.
