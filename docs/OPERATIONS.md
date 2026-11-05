# 앙개봇 서버·GitHub·소스 운영 정책 (OPERATIONS)

> 운영 기준은 이 파일에만 기록합니다. 과거 서비스 구축 문서의 전문은 아래에 보존합니다.

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
