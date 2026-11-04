# AngaeBot v0.3.0 변경 이력

**기존 기능 및 로그 보존**: 카카오톡 알림 수신/중복 감지/RemoteInput 답장/기존 Kotlin 관리 UI 및 로그/SQLite DB, Python 계산·시간·서버상태, runit·watchdog, SSH와 부팅 스크립트, `.env` 토큰을 삭제하거나 대체하지 않음.

- Android ②-A Python 섹션에 별도 '자연어 질문 자동 전달'(OFF 기본) 스위치 추가.
- 기존 Python 명령 외에 `질문`, `요약`, `AI상태`, `대화초기화` 라우팅.
- OpenAI와 Ollama의 공통 Chat Completions API 지원. Python 표준 라이브러리만 사용(새 Termux 컴파일 불필요).
- AI OFF 기본, API 키 Termux .env 보관(기존 ANGAE_TOKEN과 Android 암호화 저장 유지).
- SQLite ai_sessions/ai_turns 추가. 채팅방·발신자별 최근 문맥 저장 및 세대식 초기화; 기존 jobs/events 보존.
- AI 질문은 최대 1000자, 응답 최대 1200자, Python 제한 최대 23초/Android 25초.
- 기존 Android 단독 명령 4초 응답 제한 보존, 기존 전체 로그 이벤트 단계 보존.
- Android 로그 TXT 내보내기 파일명은 영문 호환 버전으로 변경(내용/동작 보존).
- 새 테스트/문서/안전 업데이트 스크립트 추가.

**한계**: 외부 AI API/실제 Ollama 모델 가동 및 S20+ APK 실기기 컴파일 검증은 별도 수행 필요. AI 제공자 호출 요금이 발생할 수 있음.
