# 앙개봇 통합 회귀 테스트 계획

> 기존 테스트 계획의 전문을 아래에 보존하고, 현재 필수 검증은 항상 맨 위에 갱신합니다.

## 현재 회귀/배포 승인 기준 (Bridge v0.4.9 / Core v0.6.1)

1. Python Core 전체 unittest와 import/compile, FastAPI 토큰 검증, jobs/events 영구 SQLite 스키마·request_id dedup
2. Android Bridge 명령 파서/숫자 메뉴/한글 호출/관리 UI/배터리/RemoteInput 보존, v0.4.9 debug APK 단위 테스트와 빌드
3. 모든 응답의 모듈 출처: 메뉴(선택 엔진), 시세(market), 분석(history), 그룹(watchlists), 운영(ops), AI(ai_engine), 기본(commands)
4. `상`에 Core health 실제 배포 브랜치/커밋/버전 표시, 로컬 메타 기록이 없으면 미확인
5. `설 2` 배포 SHA, `설 3` 다른 사용자 로그 접근 차단, `앙`, `주`, `날`, `설`, `0`, `00`, 앙패스 `주 2 2`
6. Windows PowerShell 5.1/7 배포 스크립트 구문 및 ADB 자동 탐색, SHA별 Actions CI 성공 후 배포
7. 초기 프로그램 기능·로그·SQLite·UI·.env를 삭제하거나 변경하지 않고 원클릭 안전 배포
8. 자동 검증과 별도로 실제 S20+의 카카오톡 상태·모듈·브랜치·배터리 표시 확인

## 과거 테스트 계획 전문



---

## 이전 테스트 계획 원문: docs/TEST_PLAN.md

# 앙개봇 Bridge v0.1 실기기 검증 계획

## 테스트 환경 기록

- 기기: Galaxy S20+
- Android 버전: ______
- One UI 버전: ______
- 카카오톡 버전: ______
- 테스트 날짜: ______
- Bridge 빌드: 0.1.0 debug

## 기대 결과

| 순번 | 시험 | 기대 로그/동작 | 결과 |
| --- | --- | --- | --- |
| 1 | 최초 앱 실행 | 자동응답 OFF, 허용 목록 0 | 미실시 |
| 2 | 알림 접근 허용 | LISTENER_CONNECTED | 미실시 |
| 3 | OFF 상태에서 명령 메시지 | RECEIVE + REJECT_DISABLED, 답장 없음 | 미실시 |
| 4 | 방/발신자 등록, ON | SETTINGS_SAVED | 미실시 |
| 5 | 1:1 앙개야 테스트 | COMMAND → REPLY_REQUESTED, S25+ 실제 수신 | 미실시 |
| 6 | 일반 대화 | IGNORE_PREFIX, 답장 없음 | 미실시 |
| 7 | 잘못된 호출어 | IGNORE_PREFIX | 미실시 |
| 8 | 동일 알림 재게시 | DUPLICATE, 중복 응답 없음 | 미실시 |
| 9 | 허용하지 않은 방 | REJECT_ROOM | 미실시 |
| 10 | 허용하지 않은 발신자 | REJECT_SENDER | 미실시 |
| 11 | 화면 OFF/잠금 상태 | 가능한 경우 정상 알림 수신/답장 | 미실시 |
| 12 | 답장 액션 없는 알림 | REPLY_UNAVAILABLE | 미실시 |
| 13 | 로그 내보내기 | TXT에 과거 로그 모든 행 포함 | 미실시 |
| 14 | 긴급 OFF | 뒤따르는 명령에 자동응답 없음 | 미실시 |
| 15 | 단체방 메시지 | 방 이름/발신자 정확히 식별되거나 안전 차단 | 미실시 |
| 16 | 재부팅 후 | 권한, 설정, 로그 보존; 서비스 재연결 확인 | 미실시 |

## 주의할 상황

- 카카오톡이 알림 여러 개를 통합할 때 마지막 메시지만 처리하기 때문에 빠른 연속 명령이 누락될 수 있음
- 1:1 동일 메시지를 반복하면 일반 2분/구조화된 메시지 24시간 지문 제한으로 차단될 수 있음
- 단체 알림이 발신자/방 이름을 분명하게 제공하지 않으면 의도적으로 처리하지 않음
- 명령 응답은 RemoteInput PendingIntent의 성공만 관찰하며 서버 확인이나 카카오톡 상대방 배달 상태까지는 검증되지 않음
- 알림 표시 이름은 제3자가 변경할 수 있으므로 실제 계정 고유 식별·보안 승인으로 사용하지 말 것

## 이슈 보고 양식

1. Android 버전 / One UI / 카카오톡 버전
2. 기대 응답 / 실제 응답
3. 해당 시각의 `RECEIVE`, `EXTRACTION_SKIPPED`, `REPLY_*` 로그 (개인정보 제거)
4. 일반 메시지 알림에서 빠른 답장 버튼이 실제 표시되는지 여부

---

## 이전 테스트 계획 원문: docs/TEST_PLAN_v0.5.8.md

# AngaeBot v0.5.8 검증 시나리오

1. Yahoo 성공: 기존 URL/실시간 주장 없음/종전 price 및 quote_line 보존.
2. Yahoo 첫 호스트 일반 오류: 두 번째 호스트를 시도하는 기존 경로 확인.
3. Yahoo HTTP 403/429: 같은 제공자에 반복 요청하지 않고 Nasdaq 공개 웹 한 번만 조회.
4. Nasdaq 성공: 동일 ticker, USD, 정확한 price/previous_close/percent, 10일 이내 ET 시각 확인.
5. Nasdaq 응답 검증 실패: ticker 불일치, USD 외, 음수/0/NaN, HTML 응답, 누락된 거래시각/거래일, 등락률 불일치 거부.
6. 한국/일본 ticker는 Nasdaq으로 보내지 않고 기존 폴백 유지.
7. 모든 공급자 실패: 실제 시세를 추측하지 않고 조회 실패 유지, 토큰·원문 미기록 진단 로그 확인.
8. 메모리7 8종목 순서/번호, 관심그룹 10종목, 숫자 선택/소유권 격리, 과거 분석/AI OFF 보존.
9. 개별 단위 테스트와 전체 Python suite 실행, 개별 파일 문법·Bash 설치기 구문 검사.
10. 운영 원본 백업·실패 롤백·인증 health v0.5.8 확인 후에만 성공 메시지 보고.
11. 사용자 S20+ 카카오톡 실증/실제 미국 시장 데이터 연결성은 사용자 단말 배포 후 확인(이 환경에서는 네트워크 미검증).

---

## 이전 테스트 계획 원문: docs/TEST_PLAN_v0.5.7.md

# AngaeBot v0.5.7 검증 계획

## 자동 테스트
- `ANGAE_TOKEN=... python -W error::ResourceWarning -m unittest discover -s core/tests -q` (core 디렉터리 기준)
- 신규 테스트: polling 우선·시장 OPEN+지연0·체결/응답 신선도(3분)·장마감/개장전·모바일 대체·한국 종목코드 검증
- 기존 테스트: 메모리7 8종목, 그룹 최대 10종목, 숫자 선택 5분, 거래소별 해외 시세/역사적 수익률, 기존 인증/중복, 전체 SQLite 로그
- 테스트는 외부 네이버/Yahoo 호출 없이 주입된 mock opener를 사용합니다.

## Galaxy S20+ 수동 검증
1. `앙개야 서버상태`: Core 0.5.7.
2. 평일 한국장 09:00-15:30에 `주 메모리7`을 보내 삼성전자·하이닉스의 KRX 체결 시각, 상태, 지연 0분 여부 확인.
3. 한국 본장 마감 후에는 장마감 종가 표시, 시간외 JSON 시세가 있으면 별도 표시되는지 확인.
4. 네이버 제공자 장애 시 Yahoo Finance 폴백의 '지연 여부 미확인' 표시 확인.
5. `주 메모리7` → `1` 삼성전자 분석, `3` 마이크론 분석, 그룹 및 최근 명령 번호 선택, 배터리 출력 확인.
6. S20+ 실제 온라인 API 변경/장중 갱신률/데이터 라이선스는 테스트 환경에서 검증되지 않았으며 단말 실사용 검증이 필요합니다.

---

## 이전 테스트 계획 원문: docs/TEST_PLAN_v0.5.6.md

# v0.5.6 시험 계획 및 주요 경계조건

1. 메모리7 **원래 8종목 순서**와 각 줄의 통화·등락률·거래일·공급자 출처를 그대로 유지한 채 앞에 1~8을 붙였는지 확인.
2. 일부 종목 시세 실패: 해당 번호를 제거하거나 당겨오지 않고 `N. 종목 : 조회 불가` 출력; 모든 제공처 실패는 정상 오류 메시지와 실패 이벤트 기록.
3. `주 메모리7` 후 `3`과 `8`이 각각 MU, WDC의 5거래일·1개월·3개월 분석을 호출하는지 확인.
4. `앙개야 메모리7`의 레거시 직접 호출도 `menu_active` 메타데이터를 제공하고 숫자가 실행되는지 확인.
5. `주` → `2` → `1`의 3단계 메뉴가 원래 메인 메뉴를 침범하지 않는지 확인.
6. 사용자 그룹 10종목: 각 줄 `1.`~`10.` 표시와 `10`, `10번`, `10.`의 마지막 종목 티커 매핑 검증.
7. 메뉴가 없는 일반 숫자, 타 사용자·타 채팅방의 번호, 5분 경과, `10개`/`123`/`1만원` 등의 일반 문장은 명령으로 실행하지 않는지 확인.
8. 요청 ID 중복 시 기존 jobs에 결과만 한 번 기록, 결과 반복 캐시, 모든 events 로그 및 종목 그룹·AI 테이블 보존.
9. 인증 실패·Core 시간대 정보 누락·무료 시세 제공처 장애 시 기존 API와 앱 답장·배터리 표시 지속.
10. Python 전체 142건(경고 예외), Kotlin 22건 오프라인 통과. Android Gradle 빌드/실기기 수신·응답은 별도 확인.

---

## 이전 테스트 계획 원문: docs/TEST_PLAN_v0.5.2.md

# AngaeBot Python Core v0.5.2 테스트 계획

- [x] 기존 모든 Python 계산/시간/운영/인증/AI OFF/메모리7/그룹 CRUD/미국시총10 회귀 테스트 유지.
- [x] Yahoo 일봉 티커·통화·종가·수정종가·중복/미완성 장중 데이터 검증.
- [x] Naver 국내 일봉 파싱 및 국내/미국 공급자 요청 우선순위 검증.
- [x] 단일 5거래일 일별 시세·5일 누적수익률·21/63일 수익률/표본 로그변동성 계산 검증.
- [x] 21/63개 일별 수익률 계산을 위한 22/64종가 미달시 `데이터 부족` 표시.
- [x] 그룹 일부 조회 실패 격리·결과 순서·중복 request_id·타인 그룹 격리·오류 DB 로깅 확인.
- [x] 사용자 URL/셸 입력 거부 및 신규 알림 명령 미추가 확인.
- [x] Bash 배포 구문 검사. Android 앱 빌드/재설치 불필요.
- [ ] S20+ Termux 무료 Yahoo/Naver 실제 과거 시세 데이터 테스트.
- [ ] 카카오톡에서 5일·1개월·3개월 출력 길이/수치 및 한국·미국·일본 거래일 실기기 대조.
- [ ] 주말·휴장·기업 분할/배당 이력의 실제 공급자 수정종가 검증.

---

## 이전 테스트 계획 원문: docs/TEST_PLAN_v0.5.1.md

# v0.5.1 US top-ten stock group verification

1. Check previous `앙개야 계산 344*454` = 156,176, `서버상태` = v0.5.1, `주식 메모리7` still lists eight symbols.
2. Use `주식 프리셋 미국시총10` and confirm exactly ten symbols NVDA/AAPL/MSFT/GOOGL/AMZN/SPCX/AVGO/META/TSLA/LLY, and `주식 목록` shows ten.
3. Use `주식 미국시총10`, and confirm price/date source, exchange timezone, no fabricated quote when provider fails, and reply time within Android's stock 23s read timeout.
4. Try duplicate preset and confirm it fails safely and does not overwrite existing ten members.
5. Try adding eleventh stock and confirm explicit maximum-ten rejection.
6. Verify previously created `반도체` group and immutable `메모리7` are intact.
7. Verify API authentication, duplicate request-id semantics, room/sender isolation and logs via unit/integration tests.
8. Verify `.env` token/SQLite data/Android UI/runit SSH-watchdog/previous logs unaffected by deployment.
9. No AI API call, automated trading, or autonomous sending of KakaoTalk messages.
10. Live remote quote responses and Google Play Termux reboot recovery must be verified on user device separately.

---

## 이전 테스트 계획 원문: docs/TEST_PLAN_v0.5.0.md

# AngaeBot v0.5.0 테스트 계획

## 자동 회귀

- 기존 v0.4.3 91건 Python 회귀 테스트 모두 유지.
- 신규 watchlists 단위/API 테스트 15건 추가: 그룹 CRUD, 추가/삭제, 상한, 한국·미국·일본 코드, 서버 인증, 요청 ID 중복 방지, 사용자별 그룹 접근 격리.
- 외부 API 없는 mock 시세 테스트: 상승/하락/실패/현지 거래일/표시 순서/전체 실패 처리.
- 고정 메모리7이 변경되지 않는지, 신규 그룹 명령이 기존 jobs/events/ai SQLite 테이블을 삭제하지 않는지 검사.
- Python py_compile / Bash -n / PowerShell 배포 파일의 소스 존재 검증.

## S20+ 실기기

1. Windows Git Pull → `scripts/deploy-v0.5.0.ps1` → `[OK]`와 Health `v0.5.0`.
2. 기존 `앙개야 계산 344*454` → `156,176`; `앙개야 시간`; `앙개야 서버상태` 확인.
3. `앙개야 주식 메모리7` → 기존 8종목·순서·등락률 조회.
4. `앙개야 주식 목록`에 기본 메모리7 확인.
5. `앙개야 주식 그룹생성 반도체`, `앙개야 주식 추가 반도체 MU 마이크론`, `앙개야 주식 추가 반도체 005930 삼성전자` 정상 응답.
6. `앙개야 주식 반도체`에서 그룹 종목/가격/전일 대비·거래일 표시 확인.
7. `앙개야 주식 삭제 반도체 MU` 성공 후 다시 조회하여 삼성전자만 남는지 확인.
8. `앙개야 주식 그룹삭제 반도체`는 확인 요청 오류, `... 확인`은 삭제됨을 검증.
9. 다른 채팅방과 발신자에서는 이전 그룹을 조회할 수 없는지 확인 (운영 허용목록 범위 내 안전한 테스트).
10. `앙개야 통계`, `앙개야 최근오류`, `앙개야 AI상태`가 이전 기록·OFF 설정을 유지하는지 확인.

## 미검증 영역

- 무료 시세 제공자의 실제 응답 가용성은 S20+ 인터넷 상황 및 대상 종목에 따라 달라짐.
- 재부팅 후 완전 자동복구와 예약 시각의 카카오톡 자발 발신은 별도 개발/검증 대상.

---

## 이전 테스트 계획 원문: docs/TEST_PLAN_v0.4.2.md

# 앙개봇 v0.4.2 실기기 검증

1. Android Bridge는 v0.4.1 그대로 유지한다. v0.4.2는 Python Core 공급자 보완 버전이다.
2. 기존 `계산 344*454` → 156,176, `서버상태` → v0.4.2, `통계`/`최근오류`/`AI상태` 정상 응답 확인.
3. `주식 메모리7`/`메모리7`에서 국내 2종목을 네이버 금융으로, 키오시아를 Yahoo Japan으로 보완 조회하는지 확인.
4. 한국·일본 거래일이 현지 장이 열리지 않은 경우 가장 최근 거래일로 표시되는지 확인.
5. 미국 5종목 정상 표기 및 KRW/USD/JPY, ▲/▽/－ 기호, 8종목 순서 유지 확인.
6. 공급자 오류 시 임의 가격을 표시하지 않고 '조회 불가' 표시 및 기존 계산 명령이 정상 동작하는지 확인.
7. SQLite 원장/로그/인증키/자동 재시작 설정은 변경되지 않았는지 확인.
8. 카카오톡이 수신 알림 RemoteInput으로 회신하므로 긴 외부 호출에서 타임아웃이 없었는지 확인.
9. 국내/일본 비공식 공개 데이터는 실기기 네트워크에서 접근이 제한될 수 있다. 실패하면 제공처 HTTP 응답을 별도 점검한다.
10. 여전히 국내/일본 종목이 조회되지 않으면 S20+ SSH에서 `cd ~/angaebot/core && .venv/bin/python scripts/diagnose-market.py`를 실행하고 인증키 없이 공급자별 결과를 공유한다.

---

## 이전 테스트 계획 원문: docs/TEST_PLAN_v0.4.1.md

# 앙개봇 v0.4.1 무료 시세 및 기존 기능 회귀 테스트

1. Python 기존 v0.4.0 API/AI/운영/watchdog/계산 54건 포함한 전체 `unittest discover` 통과.
2. 새 8개 티커 및 각 시장 통화 포맷·수치·현지 거래일 검증.
3. 상승/하락/보합 등락률, 0 또는 빈 전일종가, 통화/티커 불일치, 응답 이상 및 오래된 시세 거부.
4. 하나 또는 모든 시세 실패 시 허위 시세 없이 '조회 불가'/안내 출력.
5. Python API 인증, jobs/events 저장, request_id 중복 및 충돌, 기존 계산 정상 처리 검증.
6. Kotlin 명령 파서 기존 테스트 및 신규 `주식 메모리7`, `메모리7` 도움말 포함 확인.
7. Android 전체 Gradle 테스트/빌드는 사용자 Windows에서 수행.
8. Termux 배포 백업·전체 Python 테스트 후 health v0.4.1 확인.
9. S25+ 카카오톡에서 새 명령 응답 시간·시장별 거래일·미국 종목 시세 확인.
10. 네트워크 연결 제한 시 기존 계산·시간·운영 명령에 영향 없는지 확인.

---

## 이전 테스트 계획 원문: docs/TEST_PLAN_v0.4.0.md

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

---

## 이전 테스트 계획 원문: docs/TEST_PLAN_v0.3.1.md

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

---

## 이전 테스트 계획 원문: docs/TEST_PLAN_v0.3.0.md

# AngaeBot v0.3.0 테스트 계획

## 자동 테스트
- 기존 v0.2.0 FastAPI 인증·계산·시간·SQLite 요청 중복 방지 및 기존 watchdog 회귀 테스트 유지.
- AI 기본 OFF에서 네트워크 호출하지 않음, 공급자 URL 검증, OpenAI 키 비노출, Ollama 사설망 검증.
- API 질문/요약/AI상태/대화초기화, 방·발신자별 대화 분리, 기존 jobs/events 보존, 실패시 계산 정상.
- AI 최대 질문 길이, 외부 HTTP 오류 매핑, 대화 문맥 반영, 요약 시 문맥 비전송.
- Windows Android Kotlin Gradle 빌드와 Termux 실기기 명령·알림 빠른답장 검증은 사용자 기기에서 확인 필요.

## 실기기 검증
1. Android 앱 v0.3.0 삭제 없이 업데이트; 설정/허용목록/로그 그대로인지 확인.
2. `앙개야 테스트`, `계산 123*456`, `시간`, `서버상태` 기존 기능 정상 확인.
3. AI OFF에서 `AI상태` -> OFF, `질문` -> 연결 설정 안내; 기존 명령 영향 없는지 확인.
4. Python `configure-ai.py` 사용해 OpenAI 또는 실제 Ollama 연결 활성화(별도 과금/네트워크 주의).
5. `AI상태` ON, `질문`, `요약`, `대화초기화` 응답 및 이전 문맥 미사용 확인.
6. 자연어 스위치 OFF에서 미등록 명령은 기존 '지원하지 않는 명령'; ON에서만 AI 질문 연결.
7. 요청 지문 중복 차단, 실패/답장 로그, 알림 로그 내보내기(영문 파일명) 확인.
8. `bash scripts/status-autostart.sh` → HEALTH_OK, `sv status sshd` → run 여부 확인.
9. AI 제공자 연결 장애 시 `계산`/`시간` 정상 작동 및 오류 응답이 키를 노출하지 않는지 확인.

---

## 이전 테스트 계획 원문: docs/TEST_PLAN_v0.2.0.md

# 앙개봇 v0.2.0 안정성·회귀 검증 계획

## 이미 실제 기기에서 확인된 v0.1.3 기준
- S20+ 카카오톡 알림 RECEIVE 및 발신자/채팅방 감지
- COMMAND 파싱, REPLY_ATTEMPT 및 REPLY_REQUESTED 로그
- S25+ 카카오톡에 실제 응답 도착 (사용자 확인)
- Android 앱 APK BUILD SUCCESSFUL 및 ADB install Success (사용자 확인)

## 이 패키지 작성 환경에서 확인한 항목
- Python 서버와 계산기, REST 인증 및 중복 요청 API 테스트 14건 통과
- Python 코드 컴파일 및 Termux 셸 스크립트 구문 검사
- Android 수정은 소스 정적 검사만 수행, **Android SDK 없이 APK 컴파일 불가**

## S20+ / S25+ 실기기에서 완료해야 할 항목
| 번호 | 시나리오 | 기대 결과 |
|---|---|---|
| 01 | v0.2.0 업데이트 설치 | 기존 로그·자동응답 설정·허용 목록 보존 |
| 02 | Python 연결 OFF, `앙개야 테스트` | 기존 로컬 응답 |
| 03 | Python 연결 OFF, `앙개야 상태` | 기존 상태 응답 |
| 04 | Python 연결 OFF, `앙개야 도움말` | 기존 도움말 응답 |
| 05 | Python 연결 ON, 서버 중지, `앙개야 상태` | 로컬 명령 정상 |
| 06 | Python 연결 ON, 서버 실행, 연결 테스트 | `PYTHON_HEALTH_OK` 기록 |
| 07 | `앙개야 계산 123*456` | 56,088 답장, 로그 `PYTHON_RESULT` |
| 08 | `앙개야 시간`, `앙개야 서버상태` | 각각 결과 1회 도착 |
| 09 | `앙개야 계산 1/0` | 거부 응답, `PYTHON_RESULT ok=false` |
| 10 | 같은 알림 재게시/갱신 | Android SQLite 지문 중복 차단 |
| 11 | Python POST 동일 request_id 재전송 | 서버 duplicate=true / 작업 1건만 저장 |
| 12 | Python 인증키가 틀림 | `PYTHON_FAILED` 및 사용자 오류 응답, 토큰 로그 미노출 |
| 13 | 화면 OFF, 30~60분 대기 | 새 메시지 수신/응답 여부 확인 |
| 14 | 3회 연속 메시지 | 각 고유 메시지에 응답, 중복 및 누락 여부 검토 |
| 15 | Termux 강제 중단/재시작 | 로컬 명령 보존, Python 오류 기록 후 복구 |
| 16 | 로그 TXT 내보내기 / 긴급 OFF | 기존 기능 정상 |
| 17 | 앱 재시작 / 휴대폰 재부팅 | 설정 보존, 알림 접근/Termux 재시작 확인 |
| 18 | 다른 채팅방·다른 발신자 | Python 명령 포함하여 자동응답 거부 |

장시간 안정성 및 실제 카톡 배달은 개발 환경에서 확인할 수 없으므로 **통과로 표시하지 않습니다**. 실패시 SQLite 전체 로그 TXT와 `core/logs/server.log`를 비교하되 인증 토큰·개인정보는 제거 후 공유합니다.
