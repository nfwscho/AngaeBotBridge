# 앙개봇 서버·GitHub·소스 운영 정책 (OPERATIONS)

> 운영 기준은 이 파일에만 기록합니다. 과거 서비스 구축 문서의 전문은 아래에 보존합니다.

## 2026-11-07 — 화면 꺼짐 및 인증 불필요 잠금의 이미지 전송 (Android Bridge v0.4.18)

- S20+ 잠금 화면을 일괄 차단하던 기존 로직을 Android 공식 잠금 구분 API로 개선한다. `isDeviceLocked=true`인 PIN·패턴·비밀번호 등의 인증이 필요한 잠금은 절대 자동 우회하지 않는다.
- 화면 꺼짐 또는 '밀어서 해제'/신뢰 상태처럼 사용자 인증이 필요하지 않은 경우 `ImageWakeActivity`(외부 접근 불가)에서 화면을 켜고 `requestDismissKeyguard` 완료 콜백을 확인한다. 그 뒤에만 기존 카카오톡 이미지 공유를 시작한다.
- 잠금 상태/설정/허용 채팅방은 공유 직전 다시 검증한다. 실패 시 `IMAGE_WAKE_AUTH_REQUIRED`, `IMAGE_WAKE_REQUESTED`, `IMAGE_WAKE_DISMISSED`, `IMAGE_WAKE_FAILED`를 기록하고 사진을 전송하지 않는다.
- Android의 배경 Activity 실행 제한으로 깨우기 실패 가능. 실제 S20+에서 꺼진 화면의 카카오톡 사진 말풍선까지 재확인이 필요하다.
- 기존 설정/허용목록/접근성 서비스/UI/배터리/원클릭 배포, Python Core/DB/.env와 RECEIVE/COMMAND/REPLY/IMAGE_UI 로그 보존.
- 전용 S20+를 PIN 없이 운영할 경우 분실 시 개인정보 노출 위험이 있으므로 별도 계정·물리 보안을 검토한다.

## 2026-11-07 — 사진 공유 마지막 보내기 버튼 자동 선택 보완 (Android Bridge v0.4.17)

- 이미지 자동시험에서 실제 PNG 사진 공유는 확인되었으나 최종 보내기 버튼을 사용자가 눌러야 하는 문제가 보고됨. 기존 확인 단계에서 채팅방 이름/미디어 문구/보내기 버튼을 한 화면에 모두 요구한 것이 원인일 가능성 있음.
- 정확한 수신 방 선택 성공 기록이 있고 350ms 이상 지난 공유/미리보기 단계에서, 방 이름이 숨겨져도 사진 미리보기(큰 ImageView) 또는 미디어 표시가 있으면 **단 하나의 명시적 보내기/전송 버튼만** 접근성으로 클릭한다.
- 방 이름이 같은 화면에 남아 있는 UI도 지원. 중복 방 이름·모호한 버튼·이미지 증거 부재·선택 이력 부재·시간 초과·잠금·스위치 OFF 시 전송하지 않는다.
- 카카오톡이 접근성 이벤트를 생략할 경우 후속 화면을 5차례 재확인. `IMAGE_UI_CONFIRM_WAIT`는 화면에 수신 방이 표시되는지·미리보기 유무·전송 버튼 수만 기록하며 대화 내용은 저장하지 않는다.
- **실기기에서 최종 보내기 클릭까지 검증 필요**. S20+ 잠금 화면을 자동 해제하지 않고 Android 백그라운드 Activity 실행을 보장하지 않는다. 기존 Core/DB/.env/로그/Android UI 및 텍스트 알림 응답은 변경하지 않는다.

## 이미지 파일 말풍선 자동전송 실험 — S20+ 실기기 검증 필요 (feature/image-send-20261107)

- 1차 `앙개야 이미지 테스트`: 기존 카카오톡 알림 답장(RemoteInput)에서 이미지 첨부 MIME을 검사. 미지원인 경우 텍스트 경고만 보내며 기존 텍스트 기능을 보존. **S20+에서 이미지 MIME 미지원이 실제 확인됨**.
- 2차 `앙개야 이미지 자동시험`: Android Bridge v0.4.16의 별도 접근성 공유 화면 자동화 실험. 별도 사용자 승인이 필요하며 기본 OFF. 현재는 앱 자체 생성 640×360 PNG만 대상으로 하고 임의 이미지/주식 차트 생성 및 외부 미디어 다운로드는 지원하지 않음.
- 화면 잠금이 해제되어 있어야 함. Android 백그라운드 Activity 실행 제한 및 카카오톡 공유 UI의 OS/버전별 차이 때문에 성공이 보장되지 않음.
- Android 관리 화면 `②-B 이미지 사진 자동전송 실험`에서 스위치 ON → 저장 → `이미지 자동전송 접근성 권한 설정 열기` → `앙개봇 이미지 공유 실험` 활성화. 기존 `②` 자동응답과 허용 방/발신자 설정도 ON/정확 일치해야 함.
- 카카오톡 알림에서 요청된 정확한 방 이름이 공유 UI에 1개만 있고 `채팅방/공유` 화면 단서가 있을 때만 클릭. 다음 화면에도 같은 방 이름/사진 첨부 단서/단일 전송 버튼이 모두 있어야 클릭. 조건 누락 시 최대 15초 후 안전하게 중단. 좌표 클릭, 루트 접근, 화면 캡처/OCR, 무관한 화면 텍스트 저장 금지.
- 기존 SQLite RECEIVE/COMMAND/REPLY_ATTEMPT/REPLY_REQUESTED/REPLY_FAILED 등 모든 로그를 유지하고 `IMAGE_UI_CONNECTED`, `IMAGE_UI_QUEUED`, `IMAGE_UI_START_ACCEPTED`, `IMAGE_UI_START_REJECTED`, `IMAGE_UI_SHARE_OPEN_REQUESTED`, `IMAGE_UI_ROOM_SELECTED`, `IMAGE_UI_SEND_REQUESTED`, `IMAGE_UI_TIMEOUT`, `IMAGE_UI_ABORTED`를 별도 기록.
- `IMAGE_UI_SEND_REQUESTED`는 UI 버튼 클릭 시도 성공만 의미. **실제 카카오톡 이미지 말풍선 도착 여부는 독립적으로 확인해야 하며 사용자에게 전송 성공으로 안내하면 안 됨**.
- 실기기 시험 순서: (1) S20+ 잠금 해제 (2) S25에서 정확히 허용된 1:1 채팅방으로 명령 전송 (3) S20+에서 공유 화면 자동 이동 여부와 이미지 미리보기 확인 (4) S25에서 이미지 말풍선 수신 여부 확인 (5) 실패 시 S20+ 브리지의 `IMAGE_UI_*` 로그를 확인하고 UI 버전 대응. 단체방/오픈채팅방은 별도 현장 검증 필요.
- 새 앱 기능 브랜치 배포: `cd D:\stockproj\AngaeBotBridge` → `.\deploy-angaebot.ps1 -Branch "feature/image-send-20261107" -InstallAndroid`. Core .env/DB/로그·Android Bridge 설치 데이터 보존.
- 루팅/카카오 내부 데이터베이스 접근은 이 실험에 포함하지 않으며, 일상적으로 잠긴 화면에서 24시간 완전무인 사진 게시를 보장하지 못함. 기능 검증 전 main 병합하지 않음.


## 실제 운영과 보안

- 운영 단말: Galaxy S20+ Android Bridge (알림 기반 카카오톡) 및 Termux Python Core (localhost:8765).
- Python Core: Termux runit 서비스와 watchdog, SSH 별칭 `angaebot`, 보존된 DB/환경변수/로그/앱 사용자 데이터.
- 호출어 `상`: 기존 Android 상태 + 인증 Core health에서 확인된 **실제 배포 브랜치/커밋/버전**. 기록이 없으면 미확인.
- 설정 `설 1~6`: 서버 상태·배포 기록·명령 로그·AI 설정·통계·최근오류를 **읽기 전용**으로 조회.
- 사용자 구분: 허용된 카톡 방·발신자 표시 이름은 접근 제한 수단이지 강력한 신원 인증이 아님.
- 인증 토큰·.env·개인정보·카톡 메시지 원문·다른 방의 데이터는 운영 조회에 노출하지 않음.
- 기존 SHA256 알림 중복제거, FastAPI request_id dedup/jobs/events, S20+ 배터리, RemoteInput/로그는 유지.
- 서비스 변경·로그 삭제·종친회 계보/회비 변경 및 GitHub 병합 등은 일반 채팅에서 수행하지 않음.

## 개발/릴리스/배포 규칙

1. 기능 요구사항 → 기능 브랜치 → 코드 최소 수정 → 기존/추가 회귀 테스트 → GitHub 커밋.
2. Python Core/Android Kotlin/PowerShell 5.1·7의 전체 CI 성공을 **해당 커밋 SHA**에 대해 확인.
3. 기능 브랜치의 PR을 검토한 뒤, 사용자 승인받은 `main` 병합은 **앙개봇 메인 채팅**에서만 실행.
4. 병합 후 main CI 성공 확인, S20+ PowerShell 원클릭 배포, 실제 카카오톡 응답 확인.
5. GitHub Actions는 **feature/** 및 **main push** 시 실행하여 동일 브랜치 PR의 중복 워크플로 메일을 줄임.
6. main HEAD와 S20+ `core/.deploy-info.json`의 실제 적용 SHA는 별개로 보고, 일치하지 않아도 오류로 단정하지 않음.
7. 실패 시 원인을 정확히 보고하고 Core rollback 및 이전 운영 환경을 가능한 한 보존.
8. **파일/문서 단일화:** 루트 `CHANGELOG.md` 최신순, `docs/ARCHITECTURE.md`, `docs/OPERATIONS.md`, `docs/UPGRADE.md`, `docs/TEST_PLAN.md` 고정 파일만 수정.
9. Python 파일 최상단에는 모든 기능을 설명하는 상세 주석 유지. 기존 UI/로그/DB/예외 처리/명령어를 임의 삭제하지 않음.

## 테스트 이메일 최소화

GitHub 계정에 로그인 → https://github.com/settings/notifications → System → Actions → Don't notify (또는 웹 알림만 필요하면 On GitHub). 자신의 계정 설정은 본인이 변경합니다. CI 자체를 끄지 않습니다.

## 과거 S20+ 서비스 구축 문서 전문

### 이전 문서: docs/SERVICE_SETUP_v0.2.1.md

# 앙개봇 v0.2.1 — Termux 자동 시작 / 자동 복구 설치 가이드

기준 경로: Windows `D:\stockproj\AngaeBotBridge`, GitHub `nfwscho/AngaeBotBridge`, S20+ Termux `~/angaebot/core`.

## 주의: v0.2.0 Python Core 설치 선행

`core/.env`, `core/.venv/bin/python`, `core/app/main.py`가 있어야 합니다. 인증키를 새로 발급하거나 `.env`, DB, `logs`를 덮어쓰지 않습니다.

Play Store 버전 Termux에서는 Termux:Boot **별도 설치 불필요**입니다. 부팅 기능이 Termux 자체에 포함되어 있습니다. F-Droid의 Termux:Boot를 Play Store Termux에 혼합 설치하지 마세요.

## 1. Windows 저장소에 소스 반영

`GPT_20261105_앙개봇_자동복구패치_v0.2.1.zip`을 받아 압축 해제합니다. 패치에는 `core/scripts/*` 와 문서만 있습니다. 기존 소스의 해당 파일을 백업한 후 교체하고, `core/.env`, `data`, `logs`, `.venv`는 **절대로** 복사하거나 삭제하지 마세요.

## 2. S20+에 파일 복사

S20+의 Termux에서 SSH가 작동하는 경우 Windows PowerShell에서:

```powershell
cd D:\stockproj\AngaeBotBridge
$adb = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb forward tcp:8022 tcp:8022
# 아래 u0_a245는 Termux의 whoami 결과로 바꿔주세요.
scp -P 8022 -r .\core\scripts u0_a245@127.0.0.1:~/angaebot/core/
```

새 스크립트는 기존 `core/scripts`만 갱신하며 `.env`, `data`, `logs`, `.venv`에는 영향을 주지 않습니다. 원격 SSH 접속은 직접 `ssh -p 8022 u0_a245@127.0.0.1`로 가능합니다.

기존 수동 구동 중인 uvicorn 서버가 있다면 해당 Termux 세션에서 `Ctrl+C`로 종료한 다음 서비스를 설치하세요.

## 3. 최초 서비스 등록

```bash
cd ~/angaebot/core
bash scripts/install-autostart.sh
bash scripts/status-autostart.sh
```

서비스가 `run: angaebot-core`, `run: angaebot-watchdog`로 표시되면 실행 중입니다. `HEALTH_OK`도 확인하세요.

## 4. 관리 명령

```bash
cd ~/angaebot/core
bash scripts/status-autostart.sh   # 실행 상태
bash scripts/restart-autostart.sh  # FastAPI 수동 재시작
bash scripts/stop-autostart.sh     # 두 서비스 정지/자동복구 일시 해제
bash scripts/resume-autostart.sh   # 서비스 다시 실행
```

서버 로그: `~/angaebot/core/logs/server.log` (기존 로그 포함, append). 감시 로그: `~/angaebot/core/logs/watchdog.log`. 부팅 파일: `~/.termux/boot/10-angaebot-services`.

## 5. 자동 복구 시험

```bash
sv status "$PREFIX/var/service/angaebot-core"
sv term "$PREFIX/var/service/angaebot-core"   # SIGTERM 종료 요청; runit 재시작 시험
sleep 4
sv status "$PREFIX/var/service/angaebot-core"
bash scripts/status-autostart.sh
```

일시적으로 연결이 끊길 수 있습니다. 내부 Android 앱으로 `앙개야 서버상태`를 보내 정상 응답 여부를 확인하세요.

## 6. 재부팅 후 확인

휴대폰 전체 절전 모드 OFF, Termux 앱 배터리 제한 없음, Wake Lock 실행 상태를 확인하세요. Play Store Termux의 부팅 스크립트가 실제로 실행되는지는 S20+에서 재부팅하여 검증해야 합니다. 사용자 PIN/잠금 해제가 필요할 수 있습니다.

이후 Windows USB-ADB를 다시 연결했다면 `adb forward tcp:8022 tcp:8022`를 재실행해야 합니다. Wi-Fi SSH를 사용한다면 네트워크 IP를 재확인하세요.

## 주의

- 서버를 수동으로 `bash scripts/start-termux.sh` 실행하고 있었다면 `Ctrl+C`로 종료한 뒤 설치하세요. 포트 8765가 이미 사용 중이면 runit 서비스가 실패·재시작 반복할 수 있습니다.
- Termux 자체가 Android에 의해 종료될 경우 runit 및 watchdog도 정지합니다.
- Termux 앱을 강제 중지하면 재부팅 전까지 자동 실행되지 않을 수 있습니다.
- `.env`의 토큰이나 서비스 명령에서 나온 비밀정보는 GitHub에 업로드하지 마세요.
