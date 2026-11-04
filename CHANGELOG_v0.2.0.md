# AngaeBot Bridge v0.2.0 — 변경 내역

## 유지한 v0.1.3 기능

- 카카오톡 알림 수신/제거, NotificationParser, 허용 채팅방/발신자, 호출어
- 기존 `테스트`, `상태`, `도움말` 로컬 실행 (상태·도움말 안내문은 v0.2.0을 반영)
- 중복 이벤트 감지 SQLite 테이블 및 전체 영구 로그
- RemoteInput 빠른 답장, 응답 요청/실패 상태 기록
- 관리 UI의 알림 권한·설정·긴급 OFF·로컬 테스트·로그·TXT 내보내기·삭제
- 기존 애플리케이션 ID 및 SQLite DB 파일 이름/스키마

## 추가한 기능

- ②-A Termux Python 연결 UI (기본 OFF), 토큰 암호화 저장 및 연결 진단
- Android 127.0.0.1 loopback 인증 통신, 타임아웃 및 오류 응답/로그
- FastAPI 서버: `GET /v1/health`, `POST /v1/commands`
- Python 계산(제한 AST), 서울 시간, 서버 상태
- Python SQLite 요청 중복 방지 및 감사 로그
- Termux 설치·실행·부팅 선택형 스크립트, Python 자동 테스트
- 프로젝트 안전 반영 PowerShell 스크립트 및 운영 문서

## 코드 변경 주의

- AndroidManifest에는 loopback 연결용 INTERNET 권한과 network security config만 추가.
- 앱 Android 내부 로그 DB `angaebot_bridge_v01.db`를 **변경하지 않음**.
- `versionCode=2`, `versionName=0.2.0`. 기존 앱 위에 설치 가능(서명 동일 조건).
- v0.1.3 기준 Java/Kotlin 소스는 최소 변경. v0.2.0 Android APK 실기기 컴파일은 아직 미검증.
