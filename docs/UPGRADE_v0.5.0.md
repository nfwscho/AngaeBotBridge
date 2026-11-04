# AngaeBot Python Core v0.5.0 설치/테스트 가이드

## 1. Windows Git 동기화

```powershell
cd D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
```

## 2. 기존 S20+에 Python Core 자동 적용 (Android 재설치 없음)

```powershell
cd D:\stockproj\AngaeBotBridge
powershell -NoProfile -ExecutionPolicy Bypass -File '.\scripts\deploy-v0.5.0.ps1'
```

- 기존 SSH: `u0_a435@10.1.1.202:8022`.
- 업데이트 스크립트는 정확히 7개 Python 소스/테스트와 설치 스크립트 1개만 전송.
- 전송 → 기존 소스 날짜별 백업 → py_compile → 전체 unittest → Core만 runit 재시작 → 인증 Health `0.5.0` 확인.
- 배포/테스트 실패 시 기존 소스를 복원하며 SQLite/로그/인증키/Android/SSH/watchdog은 보존.
- `httpx`는 이전 FastAPI 테스트 환경에 이미 설치돼 있어야 함; 신규 Python 의존성 설치는 필요 없음.
- Windows PowerShell의 `git pull`이 실패하면 소스를 강제 덮어쓰지 말고 변경 파일부터 점검.

## 3. 카카오톡 실제 실행

```text
앙개야 서버상태
앙개야 주식 메모리7
앙개야 주식 목록
앙개야 주식 그룹생성 반도체
앙개야 주식 추가 반도체 MU 마이크론
앙개야 주식 추가 반도체 005930 삼성전자
앙개야 주식 추가 반도체 285A.T 키오시아
앙개야 주식 반도체
앙개야 주식 삭제 반도체 MU
앙개야 주식 목록
```

그룹 삭제는 반드시 `앙개야 주식 그룹삭제 반도체 확인`이라고 입력해야 합니다. 메모리7은 삭제·편집할 수 없습니다.

## 4. 장애 확인

```powershell
ssh -p 8022 u0_a435@10.1.1.202 'cd ~/angaebot/core && bash scripts/status-autostart.sh'
ssh -p 8022 u0_a435@10.1.1.202 'cd ~/angaebot/core && .venv/bin/python scripts/diagnose-autostart.py'
```

Health 버전이 `0.5.0`인지 확인합니다. 그룹 시세 일부가 조회 불가여도 계산·시간·서버상태는 유지되어야 합니다.

## 개인정보 및 시세 참고

- 사용자별 분리는 카카오톡 알림에 표시된 발신자/방 이름을 기준으로 하므로 고신뢰 인증이 아닙니다.
- 신규 그룹 종목은 서버 SQLite에 저장됩니다. `주식 그룹삭제 ... 확인`은 해당 그룹 및 등록 종목만 삭제하고 과거 명령 로그는 보존합니다.
- 네이버 금융·Yahoo 등 무료 시세는 지연되거나 접근이 제한될 수 있으며 실제 매매용 호가가 아닙니다.
- OpenAI API/예약 메시지 발송/주식 주문을 자동 실행하지 않습니다.
