## 2026-11-07 — MediaSender 직접 공유 실험 v0.4.22

- feature/mediasender-experiment-20261107 브랜치는 main 787cbda654217bff56666e96adf25ab0e5221050 에서 독립 생성.
- MediaSender 공개 소스의 Intent extra 3종을 선택형 시험에 적용 (원본 JS 복사 없음).
- 1:1 알림 숫자형 tag 후보 5분 일회성 진단, 별도 실험 스위치 기본 OFF, `앙개야 이미지 직공유진단` / `앙개야 이미지 직공유시험` 지원.
- 기존 이미지 UI 자동전송·PIN 보호·허용목록·SQLite/DB/.env/주식/날씨/개인 할 일/텍스트 답장/배터리 및 모든 로그 보존.
- 사용자 제공 단말에서 실제 channelId 및 전송 성공은 아직 검증되지 않아 항상 실기기 확인을 요구한다.
- 사용법·위험: docs/MEDIASENDER_EXPERIMENT.md

## 2026-11-07 — 개인 해야 할 일 고유번호·등록일시·항목별 관리 메뉴 보완 (Android v0.4.21 / Python Core v0.7.5)

- 사용자 실기기에서 `개 5 할일 추가 앙개봇 extended lock 해보기`가 지원되지 않아 미등록된 문제를 확인. 이제 `개 5 할일 추가 제목`을 정확한 할일 등록 명령으로 파싱하며 기존 `개 5`/숫자 경로·`할일 추가`를 모두 유지.
- 기존 personal_todos의 `created_at`, `updated_at`, `completed_at`을 읽어 상세의 등록/수정/완료 일시를 KST로 표기. 목록에는 #고유번호와 '등록 MM/DD HH:MM'을 추가. 기존 데이터/테이블/DB 마이그레이션 없이 표시만 보강.
- 개인 5번 할 일 목록에서 1~10번 항목을 선택하면 고유번호·등록일시·기한·내용을 보여주고 1 완료/복원, 2 제목·내용 수정 명령 안내, 3 삭제 확인, 4 목록 복귀 메뉴를 제공.
- 삭제는 해당 항목의 3번 선택 뒤 별도 확인 화면에서 1번까지 눌러야만 실행. 완료/복원/삭제는 SQLite jobs/events 트랜잭션·기존 request_id 중복방지·방/발신자 격리 이후에만 수행.
- 수정은 자유 텍스트가 필요하여 2번 선택 시 `할일 수정 #ID 새 제목 | 내용` 및 기한 명령을 안내. 숫자 조작만으로 임의 제목이나 삭제를 실행하지 않는다. 0 이전/00 홈/5분 만료·메뉴 소스/Android 배터리·로그는 유지.
- 사용자 첫 할 일은 `할일 추가 앙개봇 Extend Unlock 해보기` 또는 `개 5 할일 추가 앙개봇 Extend Unlock 해보기`로 실기기에서 직접 등록. 단말 DB는 GitHub 커밋만으로 변경되지 않으며 모든 방에 자동 등록하지 않는다.
- 기존 주식·날씨·부동산·금융·개인 메모/일정·카카오톡 이미지 자동전송·알림 접근/허용 목록/SSH/.env/DB/모든 기존 로그와 UI를 보존. main 미변경, 기능 브랜치만 업데이트.

## 2026-11-07 — 개인 5번 '해야 할 일' 기능 (Android Bridge v0.4.20 / Core v0.7.4)

- 개인 메뉴(개/앙 9)의 기존 1~4번은 유지하고 5. ✅ 해야 할 일 추가. `개 5`로 미완료 목록을 열어 1~10으로 상세보기. `0` 이전/ `00` 홈, 5분 만료·방/발신자 격리를 유지.
- `할`, `할일`, `앙개야 할일`은 목록. `할일 추가 S20+ Extend Unlock 확인 | PIN 보안을 유지하면서 이미지 자동전송 시험`으로 첫 할 일을 직접 등록. 자동 데이터 생성은 없으므로 다른 채팅방에 개인 점검 항목이 등록되지 않음.
- `할일 추가 [YYYY-MM-DD] 제목 | 상세`, `할일 목록`, `할일 전체`, `할일 완료목록`, `할일 검색 키워드`, `할일 보기 번호`, `할일 완료 번호`, `할일 복원 번호`, `할일 수정 번호 제목 | 상세`, `할일 기한 번호 YYYY-MM-DD/없음`, `할일 삭제 번호 확인` 지원. 목록의 숫자 선택만으로 완료/삭제하지 않음.
- 저장은 SQLite 신규 personal_todos 테이블. 제목 60자·상세 600자·최대 500건, 한 번에 10개 표시. 모든 읽기/수정/삭제에 room/sender 확인, 기존 인증·jobs/events 요청 중복 차단·모듈 식별/로그 그대로 사용.
- 기존 메모·일정·부동산/주식/AI/날씨·카카오톡 자동 이미지 전송·Android 설정/SQLite 기존 테이블/운영 .env·개인 데이터를 변경하거나 삭제하지 않음. 마감일은 정렬·조회만 사용하며 자동 알림은 아직 미구현.
- 기능 브랜치 feature/image-send-20261107에서만 개발·테스트; main 미병합. S20+ 원클릭 기능 브랜치 배포 및 실제 카카오 응답 확인 전까지 실사용 완료 판단하지 않음.

## 2026-11-07 — 인증 불필요 잠금 자동 깨우기 시험 (feature/image-send-20261107)

- Android Bridge v0.4.18(versionCode 22). S20+ 화면이 꺼지거나 인증 없는 밀어서 해제 잠금 상태일 때 공식 Android 잠금 해제 API로 화면을 깨우도록 개선한다.
- PIN·패턴·비밀번호 인증 필요 상태는 우회하지 않으며 `IMAGE_WAKE_*` 로그로 구분한다. 시간 제한/일회용 작업 토큰/허용 채팅방 재검사를 유지한다.
- `ImageWakeActivity.kt`, `ImageLockPolicy.kt` 및 회귀 테스트 추가. 기존 Core/DB/.env/주식/메뉴/Android 알림·접근성/배터리·로그·관리 UI/사진 전송 기능 보존.
- 실기기 검증 전이므로 백그라운드 화면 깨우기와 카카오톡 실제 사진 수신 성공은 아직 확인되지 않았다. main 미병합.

## 2026-11-07 — 사진 전송 마지막 버튼 자동 클릭 보완 (feature/image-send-20261107)

- S20+ 실기기에서 사진 공유 화면까지 자동 진입하고 마지막 보내기 버튼을 사용자가 눌러야 했던 문제 대응.
- Android Bridge v0.4.17(versionCode 21): 최초 수신 채팅방 정확 일치 확인 후 선택 이력을 보존하고 미리보기에서 방 이름이 숨겨져도 사진 및 전송 버튼을 확인해 단일 전송 버튼을 자동 클릭.
- 미리보기 확인 대기 재시도, `IMAGE_UI_CONFIRM_WAIT` 진단 로그, 방/버튼 모호성 차단에 대한 순수 Kotlin 테스트 확장. 기존 이미지 원본·Android 알림 답장·Python Core·DB·.env·배터리·기존 로그 및 UI 보존.
- 새 버전의 카카오톡 실제 전송 및 잠긴 화면 상태의 무인 동작은 실기기에서 별도 확인해야 하며 `main` 변경 없음.

## 2026-11-07 — 카카오톡 실제 이미지 말풍선 자동전송 Android 접근성 실험 (feature/image-send-20261107)

- 알림의 이미지 RemoteInput은 S20+ 카카오톡에서 지원되지 않는 것을 실제 테스트로 확인해 기존 1차 이미지 테스트는 보존하고 별도 `앙개야 이미지 자동시험` 추가.
- Android Bridge v0.4.16(versionCode 20): 선택형 `KakaoImageAccessibilityService`와 카카오톡 전용 접근성 이벤트 설정 추가, 관리 UI에 별도 이미지 자동전송 스위치(기본 OFF)·접근성 설정 버튼 제공.
- 기존 앱 자체 캐시의 640×360 PNG + ACTION_SEND 화면 공유를 사용하고, 대상 방 이름 정확 일치·단일 선택·사진 첨부·단일 보내기 버튼 UI 확인을 모두 통과해야 자동 클릭. 잠금, UI 불명확, 시간초과 등은 전송하지 않고 `IMAGE_UI_*` 로그 기록.
- 기존 Python Core/DB/.env/주식·날씨·부동산·메모·설정·텍스트 빠른답장/배터리 및 Android 기존 UI/명령은 모두 유지. 정확한 수신 방 화면 UI는 OS/카카오톡 버전에 종속적이고 자동전송·수신 성공 여부는 실기기에서 검증 전.
- 사용자 사진·외부 URL·예약/대량 이미지 전송은 아직 구현하지 않으며 루팅·카카오톡 비공개 프로토콜 접근을 사용하지 않는다. main 병합 보류.

## 2026-11-07 — Android 알림 이미지 전송 시험 (feature/image-send-20261107)

- 카카오톡 알림에서 이미지 첨부 `RemoteInput.allowedDataTypes`를 검사하고 지원되는 경우에만 Android 앱 전용 테스트 PNG/JPEG를 읽기 전용 Provider를 통해 전달한다.
- `앙개야 이미지 테스트` 명령은 기존 정확한 채팅방/발신자 허용목록·호출어·중복검사·배터리·로그를 거치며 지원하지 않으면 기존 텍스트 답장으로 이유를 알린다.
- 기존 `ReplyManager.reply()` 텍스트 자동응답 코드는 유지하며 이미지 요청 결과만 `IMAGE_REPLY_*` SQLite 로그를 추가한다. 위험한 접근성 자동조작, 외부 저장소 권한, Python Core/DB/환경변수 변경은 하지 않는다.
- Android Bridge v0.4.15(versionCode 19). Kotlin MIME 정책 회귀 테스트를 추가하고 GitHub Actions Android 빌드/전체 회귀 후 Galaxy S20+의 카카오톡 실제 **사진 말풍선** 수신을 별도로 확인해야 한다.
- 실전송 성공 여부는 아직 확인 전이며 `PendingIntent.send` 성공만으로 전송 완료를 주장하지 않는다. 기능 브랜치 상태로 유지하고 main은 수정하지 않는다.

## 2026-11-06 — Windows .env 파일의 S20+ 배포 자동 동기화

- `deploy-angaebot.ps1` 배포 시 로컬 `core\.env`(없으면 저장소 최상위 `.env`)를 자동 감지하고 SSH/SCP로 S20+에 비공개 전송한다. `-SkipEnvSync`로만 비활성화.
- 기존 S20+ `.env`를 통째로 덮어쓰지 않고 Windows 항목을 변수별로 병합한다. S20+ `ANGAE_TOKEN` 및 S20+ 전용 환경변수·주석은 보존한다.
- 새 환경설정 파서는 BOM·CRLF 호환, 중복/비정상 입력 거부, 0600 권한·원자적 교체·실패 시 기존 `.env`/모듈 복구를 제공한다. 인증키·설정값을 커밋하거나 출력하지 않는다.
- `core/scripts/merge-deployment-env.py` 및 `core/tests/test_deployment_env_merge.py`를 추가하고 기존 전체 회귀 테스트와 PowerShell 5.1/7 정적 문법 검증을 유지한다.
- S20+ 실기기 배포/카카오톡 명령어/국토부 API 연동은 Windows 원클릭 배포 후 확인해야 하며 `main`은 수정하지 않는다.

## 2026-11-06 — 실거래 인증키 비공개 등록 도구 (feature/real-estate-transactions-20261106)

- S20+ `core/.env`에 기존 키·AI 환경설정·주석을 보존하면서 `MOLIT_API_KEY`만 안전하게 추가/갱신하는 `core/scripts/configure-real-estate-key.py` 추가.
- Windows PowerShell `scripts/configure-real-estate-key.ps1`: 기존 `angaebot` SSH 접속, 숨김 입력, SSH 표준입력으로 비밀값 전달, 원자적 `.env` 교체, Core 서비스 재시작. GitHub 코드·CLI 인수·출력에 발급 키 미포함.
- 가짜 키를 이용한 `.env` 내용/권한/줄바꿈/오류 회귀 테스트를 추가하고 PowerShell 5.1/7 양쪽 문법 검사를 CI에 연결.
- 실제 발급 키는 공개 저장소에 절대로 올리지 않으며 이 커밋은 설정 도구만 제공한다. S20+의 실제 인증키 저장과 API 승인 확인은 실기기에서 실행 후 검증해야 한다.

## 2026-11-06 — 국토교통부 아파트 실거래가 조회 (feature/real-estate-transactions-20261106)

- 기존 **부동산 메모 메뉴 1·2번을 유지**하면서 3 매매 실거래, 4 전세 실거래, 5 월세 실거래, 6 지역 설정 안내를 추가. 홈의 기존 1~10 순서·금/개/주/날 단축 메뉴도 변경하지 않음.
- 직접 명령: `부 지역 강남구`(방·발신자별 조회 지역 저장), `부 시세` / `부 매매 강남구` / `부 전세 강남구` / `부 월세 강남구` / `부 매매 강남구 래미안`. 장문 `앙개야 부동산 시세 강남구` 지원. 0 이전·00 홈·5분 번호 선택 재사용.
- 국토교통부 **아파트 매매·전월세 실거래가 공개 API**를 최신 3개 계약 월로 조회하고 취소 계약을 제외, 거래일 순 최대 5건·전용면적·층·거래금액(만원 단위), 출처와 신고 지연 경고를 표시. 현재 매물 호가/감정가가 아님.
- 지역 지원: **서울 25개 자치구** 지명 또는 전국 시군구 법정동 **앞 5자리 숫자 코드**. 다른 지역의 지명 자동 변환은 지원하지 않으며 추측하지 않음.
- 공공데이터포털에서 무료로 발급/승인받은 서비스키를 S20+ 기존 `core/.env`에 `MOLIT_API_KEY=`로 설정해야 실제 호출 가능. 암호키를 GitHub에 올리거나 로그/응답에 노출하지 않음.
- 신규 `core/app/real_estate.py`, 독립 `real_estate_regions` 테이블 및 `core/tests/test_real_estate.py`. 인증·중복 요청·jobs/events 로그·module_source·기존 메모/주식/AI/날씨/Android 배터리·UI 보존. Python Core v0.7.3 / Android Bridge v0.4.14(versionCode 18).
- 개발 브랜치에서 GitHub Actions 회귀 테스트 수행. S20+ 배포/실거래 API 응답 검증 전 `main` 병합하지 않음.

## 2026-11-06 — 날씨 예보 및 사용자별 지역 설정 (feature/weather-forecast-20261106)

- **날/홈 8 날씨**: 기존 오늘(1)·내일(2)·주간(3)·지역 설정(4) 메뉴 번호를 보존하면서 Open-Meteo 실제 예보를 조회.
- **단축어**: `날 1`, `날 2`, `날 3`, `날 4`, `날 오늘`, `날 내일`, `날 주간`, `날 지역 부산`. `앙개야 날씨 오늘`과 `앙개야 날씨 지역 부산`도 지원.
- **예보 내용**: 한국시간 일별 최저/최고 기온·강수확률·날씨 상태, 오늘의 현재 기온·체감온도·습도·풍속.
- **지역**: 별도 `weather_locations` SQLite 테이블에 방·발신자별 좌표를 저장. 미설정 기본 지역은 서울. 국내 지오코딩/입력 검증, GPS 접근 없음.
- **안정성**: 인증·중복 요청·jobs/events 로그·5분 번호 선택·0/00 이동을 유지하며 API 장애/잘못된 지명은 예보 추측 없이 오류 응답. 기존 주식/AI/개인 메모/설정/배터리·Android UI와 기존 DB 테이블을 보존.
- **모듈/버전**: `core/app/weather.py`(응답 하단 담당 경로), Python Core v0.7.2, Android Bridge v0.4.13(versionCode 17). Python/Kotlin 회귀 테스트 추가.
- **배포**: S20+ 테스트는 `deploy-angaebot.ps1 -Branch "feature/weather-forecast-20261106" -InstallAndroid`로 수행하고, 실기기 검증 후 main 병합을 요청. 무료 비상업적 이용 조건은 Open-Meteo 공식 약관 확인.

## 2026-11-06 — 홈 순서 변경 및 부·금·개 단축 명령 (feature/personal-notes-sectors-20261106)

- 홈 메뉴를 **1 주식 → 2 부동산 → 3 금융·투자 → 4 여행 → 5 배드민턴 → 6 요리 → 7 종친 → 8 날씨 → 9 개인 메모·일정 → 10 설정·운영** 순으로 재정렬.
- 새 단축어 **부=부동산, 금=금융·투자, 개=개인 메모·일정**. 기존 투=금융·투자 및 메=개인 별칭은 하위 호환을 위해 유지.
- 설정 8번/Core 도움말 및 Android 로컬 도 도움말을 8줄로 동기화. 설정 7 전체 메뉴 트리는 실제 홈 선택지의 경로를 반영.
- 앙패스 경로 변경: 앙 2 1(부동산 메모) · 앙 3 1(금융 메모) · 앙 9 2(개인 일정) · 앙 10 7(설정 전체 메뉴 트리).
- 설정의 하위 1~8번, 직접 설 1/7/8 호출, 기존 메모/일정 DB·CRUD·주식·AI·로그·5분 선택 및 Android UI/배터리 보존.
- Python Core v0.7.1 및 Android Bridge v0.4.12(versionCode 16). 기존 회귀 테스트 유지, 새 번호·단축어 테스트 갱신.

## 2026-11-06 — 홈 부동산·금융투자·개인메모/일정 (feature/personal-notes-sectors-20261106)

- 홈 기존 1~7 번호 유지, 8 부동산·9 금융·투자·10 개인 메모·일정 추가. 부/투/메 정확한 단축 메뉴 및 앙 8/9/10 앙패스 지원.
- 개인 기록 신규 `core/app/personal_records.py`와 SQLite `personal_records` 테이블/인덱스 추가; 기존 jobs/events/stock_groups/AI/DB 파일·로그 그대로 보존.
- 메모/일정/부동산/투자/금융 명령의 `추가 제목 | 내용`, `목록`, `검색 키워드`, `보기 번호`, `수정 번호 제목 | 내용`, `삭제 번호 확인`; `기록 검색 키워드`는 모든 분야 통합 검색.
- 일정은 `일정 추가 YYYY-MM-DD 제목 | 내용`으로 등록, 다가오는 일정은 한국 날짜 기준 정렬, 5분 숫자 메뉴에서 기록 상세보기 제공.
- 방·발신자별 스코프, 모든 쿼리 바인딩, 검색 문자 이스케이프, 사용자당 500건/제목 60자/본문 600자/한 번에 10건 제한. 삭제는 명시적 확인 필요.
- 정보는 카카오톡과 S20+ SQLite에 평문으로 남을 수 있음. **비밀번호/인증번호/계좌 비밀을 저장하지 말 것**. Galaxy Notes 자동동기화·외부 캘린더 연동·예약 알림은 이번 버전에서 제공하지 않음.
- Android Bridge v0.4.11(versionCode 15), Python Core v0.7.0; 기존 카톡 알림/답장/배터리/담당모듈/주식/AI·설정·전체 테스트 유지.
- GitHub Actions 전체 자동 테스트 및 S20+ 실기기 검증 결과는 별도 확인 후 배포.

## 2026-11-06 — 설정 통합 상태 및 간결 도움말 (feature/menu-settings-20261106)

- **설 1**: Python Core 버전·가동시간·Core/감시/SSH 서비스·실배포 브랜치/커밋을 하나의 읽기 전용 상태로 통합. Android 자체 상태('상')는 그대로 유지.
- **설 8**: 간편 도움말 추가. 기존 1~7번(설 7 전체 메뉴 트리 포함) 번호 유지. `도`·`앙개야 도움말`도 동일하게 축약.
- **카톡 명령 정리**: `테스트`, `ping`, `계산`, `질문` 직접 호출은 무응답으로 비활성화. 레거시 Python 내부 API·테스트와 사용자 과거 DB/로그는 삭제하지 않음. 별도 선택형 자연어·요약 기능은 유지.
- **서버상태/상세상태**: 기존 장문 명령은 호환성 유지, 도움말에서는 중복을 제거하고 `설 1` 통합 화면으로 안내.
- **버전**: Android Bridge v0.4.10 (versionCode 14), Python Core v0.6.2. Android 관리 UI 안내 동기화.
- **회귀 검증**: `core/tests/test_settings_help_status.py` 신규 및 메뉴/Android 파서 테스트 확장. 기존 인증·SQLite·로그·주식·앱 권한·답장 흐름 보존.

## 2026-11-06 — 설정 전체 메뉴 트리 조회 (feature/menu-settings-20261106)

- `설 7` 또는 `앙 7 7`: 설정 메뉴 7번에서 전체 메뉴 트리를 읽기 전용으로 확인.
- 홈·주식·분석·배드민턴·요리·여행·종친·날씨·설정 메뉴의 실제 선택지 정의를 공유하며 번호 경로가 자동 반영됨.
- 관심그룹/최근 조회/시세 선택은 사용자별 동적 메뉴임을 표시하고 개인정보·시세 요청을 수행하지 않음.
- 설정 1~6번, 앙패스/0/00/5분, 인증·SQLite 작업/이벤트 로그·기존 UI·Android APK·DB·AI·주식 명령 보존.
- 새 API 회귀 테스트: `core/tests/test_menu_tree.py`. (GitHub Actions 검증 별도 확인 필요)

# 앙개봇 통합 변경 이력 (CHANGELOG)

> **최신 버전 기록이 위로 쌓이는 단일 파일입니다.** 기존 22개 버전별 CHANGELOG의 내용을 아래에 합쳤습니다.
> 새로운 릴리스는 이 파일의 첫 번째 '최근 릴리스'에만 추가하고, 버전별 별도 파일을 생성하지 않습니다.

## 최근 릴리스

### 2026-11-06 — Android Bridge v0.4.9 / Python Core v0.6.1

- 카카오톡 모든 답장에 기능 모듈명/저장소 소스 경로를 기존 배터리 정보 바로 위에 표시
- `상` 상태에 인증 Core health의 실제 S20+ 배포 브랜치/커밋, Python Core 버전 표시
- 메타데이터 `module_source`, `deployment_branch`, `deployment_sha` 추가 (기존 JSON/SQLite/jobs/events·로그/메뉴 동작 보존)
- 기존 `주 2 2` 앙패스·`설 2` 배포 기록·시세·배터리·AI/설정 그대로
- 루트 CHANGELOG.md 단일화, docs/ARCHITECTURE.md/OPERATIONS.md/TEST_PLAN.md/UPGRADE.md에 전문 통합
- GitHub feature/main push CI 성공 검사 유지, PR 트리거 중복 제거로 테스트 메일/CI 실행 수 감소
- Android versionCode 12→13, Core 0.6.0→0.6.1, 앱 설정/로그/DB 보존

### 2026-11-06 — Android Bridge v0.4.8 / Python Core v0.6.0

- 홈 6번 영어 → 날씨(`날`), 7번 설정·운영(`설`)
- 앙패스: `주 2`, `주 2 2`, `앙 1 2 2`, `설 2` 등 연속 숫자 메뉴 점프
- 설정·운영 상태/배포/로그/설정·통계/최근 오류 읽기 전용
- 배포 성공 시 Core 로컬 `.deploy-info.json`에 SHA/브랜치/시각/APK 설치 여부 기록

### 2026-11-06 — Android Bridge v0.4.7 / Python Core v0.5.10

- 홈/주식·배드민턴·요리·여행·종친·영어 공통 메뉴
- 0 이전/00 홈/5분 TTL/방·발신자 스코프와 한 글자 단축어, 기존 주식/AI/로그 보호
- ADB 자동 탐색, Core+APK 안전한 원클릭 배포

## 과거 릴리스 기록 전문 (최신순)



---

## 기존 변경 이력 원문: CHANGELOG_v0.5.10.md

# AngaeBot Python Core v0.5.10 — 미국 시세 다중 복구

## 변경 내용

- 미국 시세 기존 Yahoo Finance와 Nasdaq 공개 현재가 경로를 그대로 유지.
- 두 공급자가 모두 실패한 경우 Nasdaq `historical` 공개 일별 체결표를 이용해 최근 **확정 정규장 종가 2건**을 가져옴.
- Nasdaq 일별 체결표마저 실패할 경우 네이버 해외 종목 차트 JSON을 독립 백업으로 조회(검증된 Nasdaq 상장 티커에 한정).
- 과거 종가는 **실시간이 아닌 최근 확정 종가**로 구분하고 미국 동부시간의 종가 시각과 실제 출처를 시세표 하단에 한 번만 표시.
- 종목코드/통화/날짜/전일 종가/정규장 종료/응답 크기/시간대 검증; 일부 API 오류는 종목별 조회 불가로 격리.
- 기존 원인 코드 `US_QUOTE_FAILED`를 확대하고 성공 복구는 `US_QUOTE_FALLBACK_OK`로 기록(비밀키/개인정보 제외).
- 국내 KRX/NXT, 일본 키오시아, 메모리7/반도체 그룹/미국시총10, 순서·번호 선택, 주식 분석, 로그인/AI OFF/SQLite DB·로그/배터리 기능 모두 유지.
- Android Bridge v0.4.5 유지, APK 설치 불필요. API 키/유료 가입/주기적 백그라운드 작업 없음.

## 한계

이 두 신규 경로도 비공식 공개 엔드포인트이므로 차단 또는 응답 형식 변경 가능성이 있습니다. 모든 제공처가 실패한 경우 숫자를 만들어내거나 오래된 시세를 실시간처럼 표시하지 않습니다. 변경된 경로는 네트워크 모의 응답과 전체 테스트로 검증했으며 운영 S20+의 실제 응답은 배포 후 확인해야 합니다.

---

## 기존 변경 이력 원문: CHANGELOG_v0.5.9.md

# AngaeBot Python Core v0.5.9 (2026-11-05)

## 변경
- 메모리7 및 모든 사용자 관심그룹 시세 목록에 종목별 가격/등락률/번호만 표시.
- 기존 시세 공급자·최신 거래시각·지연 여부를 시장별로 목록 하단 **한 번만** 요약.
- 미국 Yahoo/나스닥, 국내 네이버 폴링/모바일, 일본 Yahoo Finance/Japan/라쿠텐 등의 제공자 혼합 여부를 표시.
- 동일 시장 종목의 거래시각이 다른 경우 `종목별 거래시각 상이` 명시.
- 국내 별도 시간외/NXT 체결 가격은 종목별 추가 시세로 유지하며 마감 종가에 덮어쓰지 않음.
- 단독 `quote_line()`은 기존 상세 정보 형식을 유지해 다른 호출부 호환 유지.

## 보존
- KRX/미국/일본 무료 시세 조회, 403/429 Yahoo → 나스닥 보조 조회 및 기존 로그.
- 메모리7 8종목/주식 그룹 10종목/기존 사용자별 SQLite 데이터·그룹 저장과 1~10 숫자 선택.
- 5일/1개월/3개월 분석, AI OFF, 카톡 응답, Android 배터리·UI·권한·앱 버전.
- 기존 .env/DB/jobs/events/로그/SSH/runit/watchdog. 추가 서버/유료 API/예약 알림·주문 없음.

## 검증
- 로컬 Python 회귀 테스트 전부 통과 (156건; 타 플랫폼의 ResourceWarning은 별도 관찰됨).
- S20+ 실기기는 사용자가 배포한 뒤 카카오톡에서 최종 확인 필요.

---

## 기존 변경 이력 원문: CHANGELOG_v0.5.8.md

# AngaeBot Python Core v0.5.8 — 미국 시세 공급자 장애 보완 (2026-11-05)

## 적용 배경
- 삼성전자·SK하이닉스·키오시아 시세는 정상인데 미국 마이크론·샌디스크·웨스턴디지털·씨게이트는 일괄 `조회 불가`.
- 이전 미국 경로는 Yahoo Finance Chart API query1/query2 두 곳이 전부였다. 공개/비공식 API 특성상 403·429·네트워크 오류가 발생할 수 있다.
- **Termux에서의 실제 HTTP 오류 코드를 확인하지 못했으므로, 429가 사용자 단말에서 발생했다고 단정하지 않는다.**

## 변경
1. 미국 Yahoo Chart API 요청의 User-Agent를 일반 Windows Chrome 브라우저 형식으로 정리한다.
2. Yahoo HTTP 403/429에서 추가 반복 요청하지 않고 다른 공급자를 시도한다. 일반 장애는 기존 두 번째 Yahoo 호스트를 유지한다.
3. 미국 증시 종목의 Yahoo 조회 실패 시 `api.nasdaq.com/api/quote/{TICKER}/info?assetclass=stocks` 공개 웹 JSON을 단 한 번 보조 조회한다.
4. 나스닥 공개 JSON의 일치 티커·USD·가격·전일 대비 금액·등락률 정합성·거래시각 검증이 모두 통과한 응답만 화면에 표시한다.
5. 보조 공급자의 가격에는 `나스닥 공개 시세(지연 여부 미확인)`과 미국 동부시각을 붙인다. 공식 인증된 실시간 시세라고 표기하지 않는다.
6. 나스닥 역시 접근 제한/데이터 변경/빈 응답일 수 있으므로 모든 공급자가 실패하면 기존 `조회 불가`를 유지한다.
7. 모든 공급자 실패 원인 식별용 `US_QUOTE_FAILED ticker=<ticker> yahoo=<reason> nasdaq=<reason>` 진단 로그를 보강한다. API 토큰과 응답 원문은 기록하지 않는다.

## 반드시 유지하는 것
- 메모리7 고정 종목·순서와 숫자 1~8, 일반 관심그룹 1~10, 최근 명령·5분 제한/방·발신자 격리.
- 국내 네이버 KRX/NXT 구분/시세 신선도·일본 Yahoo Japan/라쿠텐 폴백.
- 기존 Yahoo가 정상일 때의 가격/등락률/출력 서식, 30초 캐시, 모든 국가 통화.
- 5거래일·21거래일·63거래일 역사적 시세 분석, 계산·시간·운영 상태·AI OFF 기능.
- SQLite 운영 데이터(jobs/events/stock_groups/stock_items/ai_sessions/ai_turns), 인증키 `.env`, 로그·백업.
- Android v0.4.5·S20+ 배터리 꼬리표·기존 카카오톡 알림/RemoteInput/UI/허용 목록·watchdog/SSH/Termux 부팅 서비스.
- 가격 알림·예약 발신·주문·상시 웹소켓·OpenAI/유료 API/신규 권한 미추가.

## 검증과 제한
- 로컬 공개 API 네트워크 접근이 불가능한 환경에서 수신 데이터를 모의한 단위 테스트와 전체 회귀 테스트 수행.
- 실제 S20+의 NASDAQ 공개 웹 접근 여부는 배포 후 `주 반도체`/`주 메모리7`로 확인한다.
- 나스닥 공개 웹 JSON은 공식적으로 SLA가 보장되는 시세 API가 아니며 이용 정책/응답 구조/접근 제한이 바뀔 수 있다.
- Yahoo 종가 차트와 별개인 **과거 주식 분석 데이터는 기존의 역사적 공급자 로직을 변경하지 않았다.**

---

## 기존 변경 이력 원문: CHANGELOG_v0.5.7.md

# AngaeBot v0.5.7 — Naver Domestic KRX Realtime Status + NXT Separation

## 변경사항
- 삼성전자/하이닉스 현재가에는 네이버 공개 polling API를 우선 사용하고, 기존 모바일 기본 시세 API → Yahoo Finance 폴백을 보존합니다.
- 폴링 데이터가 장중 3분 이상 오래된 경우 모바일 JSON을 추가로 조회하여 더 최근 체결 시각을 선택합니다.
- 네이버의 거래소 지연 메타데이터(분), KRX 시장상태 및 거래시각, 폴링 응답 생성시각을 표시합니다.
- 정상적으로 지연 0분·장 OPEN·체결시각 3분 이내·서버응답 3분 이내인 경우에만 **'네이버 실시간표시(지연 0분)'**으로 표기합니다. 공인 실시간 틱 공급임을 보증하지 않습니다.
- KRX 장마감 후에는 종가와 시간외 가격을 다른 줄로 보여주며 시간외에서 거래소를 확인하지 못하면 NXT라고 임의 표기하지 않습니다.
- `nxtOverMarketPriceInfo`처럼 NXT가 명시된 경우에만 'NXT'를 붙입니다. 시간외 데이터가 이전 본장 거래보다 오래됐거나 % 정합성이 안 맞으면 제외합니다.
- 기존 메모리7 1~8번, 관심그룹 번호(최대 10), 최근사용 명령, 미국·일본 6종목, 5일/1·3개월 분석, 조회용 무료 공급자, 기존 로그/SQLite/AI OFF/배터리 출력 그대로 유지합니다.
- 네이버 공개 API는 비공식이며 구조 변경·접근 제한·지연 가능성이 있습니다. 이용조건을 준수하고 재배포/상업적 사용은 별도 권리 확인이 필요합니다.
- 백그라운드 조회나 상시 연결을 추가하지 않았습니다. 명령마다 요청하고 기존 30초 메모리 캐시를 유지합니다.

## 버전
- Python Core 0.5.7; Android Bridge 0.4.5 **그대로**.
- Python 148 tests passed including new Naver realtime/closed/after-market/fallback tests; ResourceWarning as error passes.

---

## 기존 변경 이력 원문: CHANGELOG_v0.5.6.md

# 앙개봇 Core v0.5.6 / Android Bridge v0.4.5 — 시세요약 번호 선택

## 기능

- 기존 `주 메모리7`, `앙개야 주식 메모리7`, `앙개야 메모리7`의 8종목 시세표에 **원래 순서대로 1~8 번호**를 붙인다. 현재가/등락률/거래일/시장·제공처 설명을 보존한다.
- `3`을 단독으로 보내면 마이크론(MU), `8`이면 웨스턴디지털(WDC/웬디)의 최근 5거래일 종가 및 1·3개월 수익률·실현변동성 분석으로 이동한다.
- `주 반도체`, `주 미국시총10`과 기존 사용자 그룹 시세표도 저장한 순서대로 번호를 붙이며 **최대 10번**까지 분석을 선택한다.
- `주` → 메인 메뉴에서 `2` → 메모리7 시세표 → `1~8` 분석 같은 3단계 흐름도 지원한다.
- 성공한 시세표를 실제 카카오톡에 빠른답장 요청한 경우에만 Android 번호 선택을 켜며, Python FastAPI 응답 `menu_active`로 동기화한다.
- 메뉴 선택은 종목명/별칭 문자열이 아니라 **기존 허용된 실제 티커**로 분석해 동일 별칭/표시 이름의 혼동을 방지한다.
- 주식 시세 제공처가 실패하면 그 요청으로 새 번호 메뉴를 열지 않는다. 개별 종목이 조회 불가여도 번호의 위치는 보존하며 과거시세 분석은 독립 조회다.
- 새 UI의 선택 유효기간은 기존 **5분**이며 채팅방/발신자 허용목록을 통과한 범위에만 적용된다.
- `10`/`10번`은 10종목 그룹에서 사용 가능하지만 일반 문장 `10개`/`123`/`1만원`은 선택 명령으로 인식하지 않는다.

## 변경되지 않는 기능

- 기존 `주` 메뉴, `주 분 삼성전자`, 별칭/티커, 관심그룹 등록·삭제/조회, 메모리7 데이터, 미국시총10 및 최근 조회 명령을 유지한다.
- 한국/미국/일본 시세 제공처, 30초 캐시, 5거래일·21/63거래일 수익률·변동성 계산을 유지한다.
- `🔋 S20+ 배터리 xx% · 충전 상태` 표시, 카카오톡 알림 수신·RemoteInput, 사용자 허용목록, 중복 차단, Android UI·SQLite 영구 로그를 변경하지 않는다.
- 인증키·기존 DB 테이블·AI OFF·SSH/Watchdog/부팅 설정/포트는 그대로 보존하고 가격 알림/매매/예약발송 기능을 추가하지 않는다.

## 검증

- Python 3.13: 전체 `unittest` **142건 통과** (`ResourceWarning`을 예외로 처리한 상태).
- 순수 Kotlin 명령 파서/숫자 메뉴/배터리 포맷터 **22건 통과** (Android SDK 런타임 없이 컴파일하여 실행).
- Termux 설치 스크립트 `bash -n` 문법 검사 통과.
- Android 전체 Gradle/APK 빌드 및 실제 Galaxy S20+ 카카오톡 자동응답은 사용자의 장치에서 추가 검증 필요.

## 버전

- Python Core: 0.5.6.
- Android Bridge: versionCode 9, versionName 0.4.5.

---

## 기존 변경 이력 원문: CHANGELOG_v0.5.5.md

# AngaeBot Python Core v0.5.5 + Android Bridge v0.4.3

## 신규 기능
- 카카오톡 메시지 `주`로 주식 메뉴 1~6번 표시. 메뉴가 열렸을 때 `1`, `1번`, `1.`처럼 번호만 보내 선택.
- 메뉴 1번: 실제 SQLite `jobs`에서 같은 채팅방·발신자의 최근 성공한 **읽기 전용** 주식 명령을 최대 8개 추출, 중복 제거.
- 메뉴 6번: 삼성전자·하이닉스·마이크론·엔비디아·애플·샌디스크·메모리7 분석 선택.
- 메뉴 2/3/4/5: 메모리7·반도체·미국시총10·관심종목 목록.
- 5분이 지나면 선택을 무효화하며, 메뉴가 열려 있지 않은 숫자는 Android에서 완전히 무시.
- 숫자 선택 뒤 관련 Python 주식 명령을 기존 인증/요청 ID 중복 방지/읽기전용 시세 조회/SQLite jobs/events 기록 흐름에 연결.

## 보안 및 기존 데이터
- 정확한 채팅방/발신자 허용 목록을 통과한 후에만 `MenuSelectionGate`가 숫자를 인식함.
- 최근 명령은 조회 및 분석만 허용하고 **그룹생성·추가·삭제·프리셋·AI·금융 거래·가격 알림·자동 발신을 재실행하지 않음**.
- 기존 Android 알림 수신, SHA-256 dedup, 로컬 UI, `RemoteInput`, .env, 토큰, SQLite DB 스키마, jobs/events 전체, 파일 로그, Watchdog, runit, SSH, AI OFF 유지.
- 기존 `앙개야` 명령/`주 분 종목명`/`주 목록`/`주 메모리7`/`주식 분석`과 5일·21일·63일 수익률/변동성 계산 유지.
- Core v0.5.5와 Bridge v0.4.3이 **둘 다 설치되어야** 숫자만 보내기 기능이 활성화됨.

## 테스트
- Python unittest 전체 134건 통과.
- Kotlin 순수 JVM 파서 및 숫자 메뉴 테스트 16건 통과 (`kotlinc` 테스트 실행기).
- Gradle 전체 APK 빌드 및 실제 S20+ 사용 검증은 Windows에서 수행해야 함.
- Core 배포는 실패 시 원본 백업으로 복원하며 APK는 기존 앱 삭제 없이 동일 서명으로 덮어쓰기.

---

## 기존 변경 이력 원문: CHANGELOG_v0.5.4.md

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

---

## 기존 변경 이력 원문: CHANGELOG_v0.5.3.md

# AngaeBot Python Core v0.5.3 — 한글 종목명·별칭 조회

## 새 기능
- `앙개야 주식 분석 마이크론`, `삼성전자`, `하이닉스`, `엔비디아`, `애플`, `구글` 등 회사명으로 5일·1개월·3개월 분석.
- `앙개야 주식 분석 웨스턴 디지털`처럼 통상적인 회사 이름에 공백이 있어도 인식.
- `앙개야 주식 추가 반도체 엔비디아`, `앙개야 주식 삭제 반도체 엔비디아`처럼 그룹 등록/삭제도 회사명 허용.
- 사용자 자신의 채팅방/발신자에게 등록된 `주식 추가 투자 NVDA 내GPU` 등의 별칭은 `주식 분석 내GPU`로 조회.
- 다른 사용자의 별칭은 보이지 않으며 같은 별칭이 서로 다른 티커에 연결되면 모호성 오류로 임의의 주식을 선택하지 않음.
- 기존 8개 메모리7 종목, 미국시총10 구성, 한국·미국·일본 원래 시세 공급자 및 가격 변동성 계산 보존.

## 기존 동작 보존 및 운영
- 기존 명령·반도체 그룹·메모리7, SQLite jobs/events/stock_groups/stock_items/AI 테이블, 인증키, 로그, Android Bridge, runit/SSH/watchdog 모두 그대로 유지.
- 장마감 기준 역사적 시세는 기존 5일·21일·63일 처리 및 현지 시장 시간대 정확성 유지.
- Termux tzdata 누락은 기존 v0.5.2 핫픽스와 동일하게 재확인하며 없으면 순수 Python wheel을 설치한 뒤 소스 적용.
- 단위·통합 테스트 128건 통과(이전 126건 포함). Bash 구문 검사 통과.
- **가격 알림·주기적 감시·자동 카카오 발송·OpenAI API·주식 거래 기능은 추가하지 않음.**

## 한국어 명령 예시
```
앙개야 주식 분석 마이크론
앙개야 주식 분석 삼성전자
앙개야 주식 분석 하이닉스
앙개야 주식 분석 엔비디아
앙개야 주식 분석 웨스턴 디지털
앙개야 주식 분석 미국시총10
앙개야 주식 추가 반도체 구글
앙개야 주식 삭제 반도체 구글
```

## 2026-11-05 v0.5.3 Termux 배포 버전 검증 핫픽스
- 정상 재시작 후에도 배포 검증에서 v0.5.2를 요구하던 오타를 수정했다.
- 배포 버전 검사는 단일 `EXPECTED_VERSION='0.5.3'` 값을 사용해 성공/오류 경로가 불일치하지 않도록 한다.
- 검증 성공 시 0.5.3을 허용하며, 실패 시 기존 안전 복원·서버 재시작 로직은 변경하지 않는다.
- `ResourceWarning: unclosed database`는 SQLite 테스트 연결의 별도 경고이며 해당 경고를 이번 실패의 직접 원인으로 보지 않는다.
- 기존 UI/카카오톡 자동응답/주식시세/분석/별칭/메모리7/SQLite/로그/토큰/AI OFF/알림 미구현 정책을 유지한다.

---

## 기존 변경 이력 원문: CHANGELOG_v0.5.2.md

# AngaeBot Python Core v0.5.2 — 5거래일 시세·1개월/3개월 변동성

## 기능 보존
- 카카오톡 자동응답(Android NotificationListener / RemoteInput / 기존 UI), 방·발신자 허용 정책을 변경하지 않음.
- 기존 메모리7 8종목 시세 제공자·조회 결과·그룹 CRUD·미국시총10 프리셋·그룹 10종목 상한을 유지.
- 계산/시간/운영 명령/AI 설정(기본 OFF), FastAPI 인증·멱등 키 및 jobs/events/AI/그룹 SQLite 테이블 모두 보존.
- SSH·watchdog·runit·부팅 스크립트·서버 원본 로그 및 archive 로그를 변경·삭제하지 않음.

## 추가된 조회 전용 명령
- `앙개야 주식 분석 MU`: 최근 완료된 5거래일의 일별 종가/전일 대비, 누적 5거래일 수익률, 21/63거래일 수익률 및 실현변동성.
- `앙개야 주식 분석 005930` / `분석 285A.T`: 한국·일본의 거래소 현지 정규장 기준.
- `앙개야 주식 분석 반도체`, `앙개야 주식 분석 미국시총10`: 사용자가 등록한 그룹의 종목별 5거래일 누적수익률·21/63거래일 수익률·실현변동성 비교.
- `앙개야 주식 분석 메모리7`: 기존 고정 8종목에 동일한 그룹 요약을 적용.
- 도움말(`앙개야 주식 도움말`)에 새 명령을 추가하되 기존 전체 도움말/그룹 CRUD 흐름 유지.

## 지표 정의
- 5일: 실제 **최근 5거래일** 장마감 종가. 누적 5일 수익률은 종가/수정종가가 있는 6개 일봉 필요.
- 1개월: 최근 **21거래일**(22개 종가), 3개월: 최근 **63거래일**(64개 종가). 달력 개월 수와는 다름.
- 각 누적수익률 = (기말 수정종가 ÷ 기초 수정종가 − 1) × 100.
- 각 연율화 실현변동성(%) = 최근 기간의 일간 로그수익률 표본 표준편차 × √252 × 100.
- Yahoo 수정종가가 있으면 수익률/변동성 계산에 우선 사용하고, 일별 가격 표시에는 실제 종가 사용. 네이버 데이터는 제공된 종가 기준.
- 미완성 장중 일봉 제외; 시장 휴장일은 건너뜀. 충분한 종가가 없으면 해당 기간 `데이터 부족`.
- 신규 무료 데이터: Yahoo Chart 6mo/1d, 국내 Naver dayCandle; 일본 보조로 Naver 해외 dayCandle 시도. 무료 시세 접속/제공 범위는 보장되지 않음.
- 가격 조회 실패 시 임의 값을 생성하지 않고 실패 종목만 `조회 불가`.

## 배포
- Windows `scripts/deploy-v0.5.2.ps1`, S20+ Termux `core/scripts/apply-v0.5.2.sh`.
- Git Pull 후 PS1 실행, 파일 백업→Python 전체 테스트→FastAPI만 재시작→인증 health 0.5.2 확인.
- Android APK 재설치·OpenAI API·유료 시세 API·자동주문·가격 알림·예약/주기적 감시를 **하지 않음**.
- 실행 환경의 실제 네트워크 조회 성공 여부는 S20+에서 사용자 확인 필요. 오프라인 테스트는 공급자 응답 모의.

## Termux 시간대 데이터 보완 (2026-11-05 핫픽스)
- Python 3.13 Termux에서 `tzdata` 패키지와 IANA 시간대 파일이 누락될 때 `ZoneInfoNotFoundError`로 배포 검증이 실패하는 문제를 보완.
- 한국/일본은 UTC+9를 안전하게 사용하며, 미국은 뉴욕 DST의 정확성이 필요하므로 시간대 정보가 없으면 추정하지 않고 명확히 오류를 반환.
- `apply-v0.5.2.sh`는 운영 소스 적용 전에 필요한 세 시장 시간대를 확인하고, 누락 시에만 tzdata 순수 Python wheel을 기존 `.venv`에 설치 후 재검증.
- 설치나 시간대 검사에 실패하면 기존 Core 서버를 재시작하지 않으며 기존 DB/로그/사용자그룹을 보존.
- 회귀 테스트에서 시간대 DB 누락을 재현하여 한국/일본 대체와 미국 DST 안전 장치를 검증.
- AI API, 가격 알림, 예약, 카카오톡 자동 발신은 추가하지 않음.

---

## 기존 변경 이력 원문: CHANGELOG_v0.5.1.md

# AngaeBot v0.5.1 — US market-cap Top 10 watchlist group preset

## Preserved functionality
- All original KakaoTalk notification listening, sender/room authorization, RemoteInput, app UI, Android SQLite logs remain unchanged.
- Python FastAPI local-only binding `127.0.0.1:8765`, authentication, request-id idempotency, jobs/events logs and AI disabled-by-default are unchanged.
- Memory7's eight original symbols and their Naver/Yahoo/Yahoo Japan/Rakuten quote fallbacks remain unchanged.
- All user-created existing groups and items remain in `stock_groups`/`stock_items`; .env, database, logs and backup files are never deleted.
- Existing manual group CRUD, group lookup, and operations commands continue to work.

## New function
- Maximum stocks per user-managed group changed from 8 to **10** (maximum 10 groups per room/sender unchanged).
- `앙개야 주식 프리셋 미국시총10`: creates `미국시총10` with NVDA, AAPL, MSFT, GOOGL, AMZN, SPCX, AVGO, META, TSLA, LLY in one request.
- `앙개야 주식 미국시총10`: retrieves existing group quotes using the existing public/unofficial quote provider, with no OpenAI or paid API.
- Fixed constituent snapshot **2026-11-04** of U.S.-incorporated public companies; one share class per company (Alphabet represented by GOOGL). The stock list **does not automatically rebalance** as market-cap rankings change.
- An existing group is never overwritten by the preset. Users can still add/remove tickers manually up to 10.
- At most 5 workers for existing group quote lookup to keep 10-stock response within the Android's established stock timeout; failures continue to show `조회 불가` without fabricated values.
- Existing `CORE_START` log marker is now correctly marked v0.5.1 (other logs unchanged).

## Ranking reference
- `https://www.finhacker.cz/en/largest-us-companies-by-market-cap/` (Nov 3, 2026 US companies)
- `https://stockanalysis.com/list/largest-us-companies/` (2026-11-04 nearby ranking)
- Market caps can fluctuate daily; this is a watchlist snapshot, not an up-to-the-minute ranking.

## Verification
- Python unittest suite: 111 tests pass locally (real Galaxy S20+ deployment pending).
- No Android build needed: existing Android Bridge already forwards the `주식` command and supports stock read timeout.
- Use `scripts/deploy-v0.5.1.ps1` after `git pull`. Never run the old `deploy-v0.5.0.ps1` for the new version.

---

## 기존 변경 이력 원문: CHANGELOG_v0.5.0.md

# AngaeBot v0.5.0 — 관심종목 그룹 관리 (OpenAI OFF)

## 기존 기능 완전 보존

- Android Bridge v0.4.1의 카카오톡 수신/자동답장/허용 채팅방·발신자/RemoteInput/SQLite 로그 유지. Android APK 재설치 불필요.
- 기존 `앙개야 주식 메모리7` 및 `앙개야 메모리7`의 **8종목 구성·순서·가격 표시·공급자·캐시/실패 처리 변경 없음**.
- 기존 계산/시간/서버상태/상세상태/통계/최근오류/가동시간/AI상태/질문/요약/대화초기화 및 모든 jobs/events 로그 유지.
- FastAPI 127.0.0.1:8765, 인증 `X-AngaeBot-Token`, 중복요청 ID·400/401/409 응답 구조 유지.
- `.env`, Python venv, DB 데이터/로그, Termux runit, watchdog, SSH 및 부팅 구성 변경 없음.

## 새로운 카카오톡 명령

- `앙개야 주식 목록` : 사용자가 관리하는 그룹 목록과 기본 메모리7 안내
- `앙개야 주식 도움말` : 명령 예시와 사용법
- `앙개야 주식 그룹생성 반도체` : 빈 관심종목 그룹 생성
- `앙개야 주식 추가 반도체 MU 마이크론` : 미국 티커 추가
- `앙개야 주식 추가 반도체 005930 삼성전자` : 한국 종목 추가
- `앙개야 주식 추가 반도체 285A.T 키오시아` : 일본 종목 추가
- `앙개야 주식 반도체` : 새 그룹의 시세·등락률·현지 거래일 조회
- `앙개야 주식 삭제 반도체 MU` : 그룹에서 종목 제외
- `앙개야 주식 그룹삭제 반도체 확인` : 명시적 확인 후 그룹 및 소속 종목만 삭제 (jobs/events 로그는 보존)

## 기술·보안 설계

- 신규 SQLite `stock_groups`와 `stock_items` 테이블만 생성. 기존 DB 테이블 구조는 변경하지 않음.
- `(room, sender)` 스코프별 그룹 분리. 표시된 카카오톡 발신자/방 이름은 강력한 사용자 인증이 아님에 주의.
- 고정 `메모리7`은 변경/삭제 불가. 1개 스코프당 그룹 10개, 그룹당 종목 8개 제한.
- 미국 단순 티커(예 `MU`, `NVDA`), 한국 6자리 코드/`.KS`·`.KQ`, 일본 `.T` 지원. 이름으로 입력은 기본 메모리7의 8종목에 한정.
- 모든 외부 호출은 기존 고정 무료 시세 엔드포인트만 사용. 입력 URL/임의 쉘/주문 기능은 지원하지 않음.
- 시세 조회를 SQLite 쓰기 트랜잭션 밖에서 수행해 명령 중복 기록과 서버 응답 지연을 줄임.
- 신규 명령의 성공/실패도 기존 jobs/events 테이블에 기록되어 운영 통계/최근오류와 연동.
- 시세 공급자가 값을 제공하지 않으면 `조회 불가`; 그룹 전 종목 실패는 오류로 기록.

## 제한 및 향후 과제

- 무료 데이터 소스는 시장/종목에 따라 미제공·차단·지연될 수 있음. 새 코드의 티커 구문 유효성은 실제 상장/상장폐지 검증과 다름.
- 그룹은 카카오톡 **수신 알림에 표시된 room/sender**를 기준으로 저장됨. 알림 이름 변경 시 다른 그룹처럼 보일 수 있음.
- 목표가 알림, 예약 시각의 카카오톡 능동 발송은 이번 버전에 포함되지 않음. 현재 RemoteInput은 수신 알림에 대한 응답 전용.
- OpenAI API는 요청대로 계속 OFF이며 신규 유료 API 연동 없음.



---

## 기존 변경 이력 원문: CHANGELOG_android_v0.4.4.md

# 앙개봇 Android Bridge v0.4.4 — 모든 명령 답장에 S20+ 배터리 상태 표시

- 카카오톡에서 정상 처리된 명령(주식, `주`/`주 분`, 숫자 메뉴, 일반 로컬 명령, Python 처리 실패 등)에 대한 답장의 마지막 줄에 현재 S20+ 배터리 잔량과 충전 상태를 표시한다.
- 예시: `🔋 S20+ 배터리 68% · 충전 중`, 20% 이하이며 충전 중이 아닐 때 `⚠️ 충전 권장` 안내.
- Android `ACTION_BATTERY_CHANGED` sticky 브로드캐스트에서 `BatteryManager.EXTRA_LEVEL`, `EXTRA_SCALE`, `EXTRA_STATUS`를 답장 직전에 직접 조회한다.
- 배터리 정보가 유효하지 않거나 조회에 실패하면 원래 응답을 취소하지 않고 `🔋 S20+ 배터리 확인 불가`를 표시한다.
- 백그라운드 상주 측정/주기적 조회/인터넷 요청/새 Android 권한은 추가하지 않는다.
- 기존 카톡 알림/허용 방·발신자/자동응답 OFF/메뉴 5분 제한/숫자 입력/중복 방지/SQLite 로그/인증/RemoteInput/Python Core v0.5.5/AI OFF/주식 분석과 시세 기능을 그대로 보존한다.
- `REPLY_ATTEMPT` 이벤트에는 실제 전송할 배터리 포함 답장을 저장하며, 기존 `PYTHON_RESULT`의 원래 응답 내용은 보존한다.
- `versionCode=8`, `versionName=0.4.4`; 같은 서명으로 기존 앱에 `adb install -r` 가능. 앱 삭제·데이터 초기화 불필요.
- Kotlin BatteryStatusFormatter 순수 단위 테스트 6개 추가; 실제 Android 배터리 API/카카오톡 답장 작동은 S20+에서 확인 필요.

---

## 기존 변경 이력 원문: CHANGELOG_v0.4.3.md

# 앙개봇 v0.4.3 — 메모리7 키오시아 시세 누락 보완

## 문제 배경
- Galaxy S20+ 카카오톡 실제 확인: v0.4.2에서 삼성전자, SK하이닉스 및 미국 5종목은 정상, 키오시아(285A.T)만 조회 불가.
- Yahoo Japan 시세 페이지는 `リアルタイム株価 11/4` 대신 `リアルタイム株価 15:30`을 표시할 수 있으나, 기존 정규식은 날짜가 그 자리에 있어야만 파싱 가능했음.
- 외부 Yahoo Chart API 및 일본 무료 페이지 접근이 네트워크·HTML 변경에 따라 실패할 수 있음.

## 개선
- 기존 Yahoo Global → Yahoo Japan 순서와 미국 5종목·네이버 국내 2종목 코드/캐시/로그/API 흐름을 그대로 유지.
- Yahoo Japan은 정규장 헤더가 시각만 표시해도 종목 상세의 **명시된 실제 거래일**을 사용하며, 날짜 근거가 없으면 조회 불가.
- Yahoo 2곳이 실패할 때 공개 라쿠텐 증권 일본 본장 285A 가격·등락률·거래일을 추가 확인.
- 다른 종목/PTS 가격, 10일 초과 오래된 시세, 가격·전일 종가·등락률 불일치 데이터를 거부.
- 키오시아가 계속 실패하더라도 다른 7종목 출력은 유지, 가짜 수치로 대체하지 않음.
- `scripts/diagnose-market.py`: 일본 제공처별 성공/HTTP/파싱 오류 구분에 라쿠텐 추가.
- Python Core v0.4.3, Android Bridge 기존 v0.4.1 APK 그대로 사용.
- 원격 안전 배포: `scripts/deploy-v0.4.3.ps1`, `core/scripts/apply-v0.4.3.sh`.

## 데이터 출처 및 한계
- Yahoo Finance Chart/Yahoo Japan, 라쿠텐 증권 일본 동경거래소 공개 시세. 별도 OpenAI/API 키 불필요.
- 무료 HTML 기반 접근은 사이트별 제한·변경으로 실패할 수 있으며 실제 S20+ 네트워크 접근 성공은 아직 미검증.
- 본장과 야간 PTS를 구분하고 시장별 거래일을 표시. 투자·주문용 실시간 보장 없음.
- 개인정보·토큰·DB·Android UI·카카오톡 빠른답장·모든 기존 명령/로그 기능은 변경하지 않음.

---

## 기존 변경 이력 원문: CHANGELOG_android_v0.4.2.md

# AngaeBot Android Bridge v0.4.2 — 한 글자 주식 단축어

## 신규 명령
- `주` → 기존 `앙개야 주식` 명령(주식 도움말)
- `주 분 마이크론` → `앙개야 주식 분석 마이크론`
- `주 분 삼성전자`, `주 분 하이닉스`, `주 분 엔비디아`도 동일
- `주 분`만 입력하면 기존 주식 도움말 출력
- `주 목록`, `주 반도체`, `주 메모리7`, `주 미국시총10` 등 기존 주식 인수 사용 가능

## 호환성과 보안
- 기존 `앙개야` 및 사용자 설정 호출어, 기존 계산·운영·질문·주식 명령 전부 유지
- 정확히 `주` 또는 `주` 뒤 공백/탭/줄바꿈이 있을 때만 단축어 처리. `주가`·`주분`·`주식`·`ㅈㅅ`은 새 호출어가 아님
- 기존 채팅방/발신자 허용, 자동응답 OFF, SHA-256 중복 방지, SQLite 명령/이벤트 로그, RemoteInput, Android UI, 토큰 암호화/AI OFF 유지
- Android 앱 버전 `versionCode = 6`, `versionName = 0.4.2`로 기존 APK를 삭제하지 않고 업데이트
- Termux Python Core v0.5.4, 메모리7·그룹·5일·1개월·3개월 분석은 변경하지 않음
- 주식 가격 알림/예약/자동매매/추가 권한 없음

## 검증
- 기존 8개 Kotlin 파서 테스트 + 4개 단축어 회귀 테스트 유지
- 빌드 시 `gradlew.bat :app:testDebugUnitTest`, `gradlew.bat :app:assembleDebug` 실행
- 기존 앱과 같은 서명으로 `adb install -r` 사용. 앱 삭제/데이터 초기화 금지

## 주의
- 봇 허용 대화방에서 일반 메시지로 `주`라고 입력해도 봇이 반응합니다. 1:1 채팅방에서 먼저 검증하세요.

---

## 기존 변경 이력 원문: CHANGELOG_v0.4.2.md

# 앙개봇 v0.4.2 — 메모리7 국내·일본 시세 조회 보완

## 수정 원인
- v0.4.1의 한국 두 종목(005930.KS/000660.KS), 키오시아(285A.T)가 Yahoo Chart API에서 '조회 불가'로 나왔고, 미국 5종목은 정상 조회되었다.
- 본 버전은 실제 실패의 HTTP 상태를 단말에서 확인한 것은 아니므로 원인을 '야후 응답 또는 메타데이터 검증 실패' 가능성으로 기술한다.

## 추가·개선 기능
- 한국 두 종목: 네이버 금융 모바일 JSON을 우선 조회, 차단 시 네이버 공개 폴링 JSON을 사용하며 모두 실패하면 기존 Yahoo Chart 2호스트를 재시도.
- 키오시아: 기존 Yahoo Chart 2호스트 실패 시 Yahoo Japan 일본 본장 종목 페이지에서 가격·전일 대비 등락률·거래일시를 확인.
- 야간 PTS 데이터는 배제. 다른 종목/통화/이상치/미래나 10일 초과 오래된 시세는 표시하지 않음.
- 기존 미국 MU/SKHY/SNDK/STX/WDC 조회, 메모리7 명령어 2개, 고정 종목 순서, 가격 표시, 거래일 표시, 30초 캐시와 실패 격리 유지.
- 무료 비공식 공개 서비스는 장애·사이트 구조 변경·지연·접속제한이 있을 수 있음. 제공처가 모두 실패하면 추정가격을 만들지 않고 '조회 불가' 표시.
- OpenAI 등 모든 AI API는 계속 OFF. 별도 유료 시세 키를 요구하지 않음.
- Android v0.4.1의 기존 UI/RemoteInput/로그/허용목록/명령 전달은 그대로 이용하므로 APK 재빌드가 필요하지 않음.
- 서버 시작/상태 응답 버전만 0.4.2로 갱신; 기존 SQLite jobs/events, 암호키, 서비스/로그/부팅 환경 유지.
- 신규 국내·일본 보조 공급자 자동 모의 회귀 테스트 10건 추가, 전체 테스트 함께 실행.

## 배포
1. Windows PowerShell: `cd D:\stockproj\AngaeBotBridge; git pull --ff-only origin main`
2. `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\deploy-v0.4.2.ps1`
3. S25+ 카톡: `앙개야 주식 메모리7` / `앙개야 서버상태`.
4. 각 제공처가 실제 단말에서 차단된다면 Termux 운영 로그를 개인정보/인증키 제외 후 확인한다.

## 주의사항
- 공식 실시간 호가가 아닌 비공식/지연 참고 시세이며, 개인적인 모니터링을 위한 용도로만 사용한다.
- 최초의 8종목 시세는 S20+ 연결 환경에서 검증해야 하며, 실제 보조 제공처의 가용성을 보장하지 않는다.
- 읽기 전용 공급자 진단: `cd ~/angaebot/core && .venv/bin/python scripts/diagnose-market.py` (키·DB·로그 불변, S20+ 제공처 접속 실패 종류 확인).

---

## 기존 변경 이력 원문: CHANGELOG_v0.4.1.md

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

---

## 기존 변경 이력 원문: CHANGELOG_v0.4.0.md

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

---

## 기존 변경 이력 원문: CHANGELOG_v0.3.1.md

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

---

## 기존 변경 이력 원문: CHANGELOG_v0.3.0.md

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

---

## 기존 변경 이력 원문: CHANGELOG_v0.2.1.md

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

---

## 기존 변경 이력 원문: CHANGELOG_v0.2.0.md

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

---

## 기존 변경 이력 원문: CHANGELOG_v0.1.3.md

# 앙개봇 Android Bridge — 빌드 오류 수정 v0.1.3

- 일자: 2026-11-04
- 원인: Kotlin `:app:compileDebugKotlin`에서 `MainActivity.kt` 72행의 `fillViewport` 참조가 확인되지 않음.
- 변경: `ScrollView(this).apply { fillViewport = true }` → `ScrollView(this).apply { setFillViewport(true) }`.
- 영향 범위: `MainActivity.kt` 단 한 줄. 기존 UI 배치/명령 처리/자동응답/설정/SQLite 로그 코드 변경 없음.
- Java 환경: JDK 17 확인 완료(사용자 로그). Android SDK 경로: 오류 단계 통과(사용자 로그).
- 검증: 기존 v0.1.2와 Kotlin 소스 diff 검증(단일 라인 변경). Android SDK 없는 환경이므로 APK 컴파일 미수행.
- 설치: 기존 프로젝트에서 `app/src/main/java/kr/co/angaebot/bridge/MainActivity.kt` 한 파일만 덮어쓰거나 아래 한 줄만 수정.
- 프로젝트의 Wrapper JAR, `local.properties`, Git 설정 등 로컬 변경 파일을 교체하지 마세요.
- 권장 커밋: `fix(android): correct ScrollView fillViewport call (v0.1.3)`

빌드:

```powershell
cd D:\stockproj\AngaeBotBridge
.\gradlew.bat :app:assembleDebug
```
## 2026-11-07 — S20+ '1 보내기' 버튼 자동 클릭 인식 보완 (feature/image-send-20261107)

- Android Bridge v0.4.19(versionCode 23): 카카오톡 이미지 공유 화면의 1명 선택 버튼 '1 보내기'에 숫자가 붙어 기존 정확 일치 인식에서 누락되던 문제 보완.
- 신규 ImageSendButtonLabel.kt 및 단위 테스트로 1명 버튼/공백 변형/기존 라벨과 복수 대상 거부를 검증한다.
- 기존 수신 채팅방 단일 검증/이미지 자동 생성·공유/잠금 정책/SQLite IMAGE_UI 로그/메뉴·배터리·Python Core·운영 설정을 모두 보존한다.
- 실제 화면에서 자동 클릭 및 카카오톡 사진 수신은 S20+ 검증 전이며 기능 브랜치만 사용하고 main은 유지한다.

