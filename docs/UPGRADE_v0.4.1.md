# 앙개봇 v0.4.1 메모리7 주식 시세 설치 가이드

## 적용 범위
- 기존 Android v0.4.0 + Termux Python Core v0.4.0 기반의 추가 업데이트.
- OpenAI API는 OFF인 상태를 그대로 보존. 무료 비공식 Yahoo Finance 시세만 별도 요청.
- 기존 .env, DB, 모든 로그, Android 앱 데이터와 허용목록, SSH·Watchdog·부팅 스크립트 유지.

## 1. Windows Git Pull
```powershell
cd D:\stockproj\AngaeBotBridge
git status
git pull --ff-only origin main
git log -1 --oneline
```

## 2. Python Core 자동 업그레이드
```powershell
cd D:\stockproj\AngaeBotBridge
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\deploy-v0.4.1.ps1"
```
- 전송한 소스만 백업·갱신, 전체 Python 테스트 성공 후 runit core만 재시작.
- SSH 연결이 끊어지면 `ssh -p 8022 u0_a435@10.1.1.202`로 복귀한 뒤 `bash ~/angaebot/core/scripts/status-autostart.sh`를 확인.
- 테스트에 실패하면 배포 스크립트가 이전 소스를 복구하며 기존 DB/로그/인증키는 보존.

## 3. Windows Android 빌드/설치 (USB S20+)
```powershell
cd D:\stockproj\AngaeBotBridge
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug
$adb="$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
& $adb devices -l
& $adb install -r ".\app\build\outputs\apk\debug\app-debug.apk"
```
- Android 기존 앱을 삭제하지 마세요. `install -r`로 설정과 앱 DB 유지.

## 4. 카카오톡 테스트
- `앙개야 서버상태` → Python v0.4.1
- `앙개야 계산 344*454` → 156,176
- `앙개야 통계` / `앙개야 최근오류` / `앙개야 가동시간` → 기존 기능 유지
- `앙개야 주식 메모리7` → 8개 종목 시세와 등락률 및 현지 거래일 표시
- `앙개야 메모리7` → 같은 결과
- `앙개야 주식 마이크론` → 사용법 안내(아직 임의 종목 조회 미지원)

## 시세 제공 정책
- Yahoo Finance 비공식 chart API이며 지연/장중 변동/접속 제한/중단 가능.
- **KRW(한국), USD(미국), JPY(일본) 각 시장 최근 정규 거래일** 기준으로 표시. 미국 장은 한국 시각으로 전날 거래일일 수 있음.
- 시세 실패 시 값은 임의 계산하거나 과거 값을 '오늘' 값으로 보이지 않음.
- 종목: 005930.KS / 000660.KS / MU / SKHY / SNDK / 285A.T / STX / WDC.
- 유료 OpenAI API와 무관하며 .env 설정을 변경할 필요가 없음.
