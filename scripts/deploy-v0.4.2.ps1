#requires -version 5.1
<#
앙개봇 v0.4.2 Windows SSH 배포 도구 — 기존 기능/로그 보존 전체 설명
1. 기존 Android Bridge v0.4.1의 카카오톡 알림 수신·RemoteInput·허용 목록·SQLite 로그를 변경하지 않는다.
2. Python Core 메모리7의 한국/일본 보조 시세 제공자와 기존 미국 조회 기능을 배포한다.
3. Windows Git 최신 소스의 정확히 지정된 Python 8개 파일과 Termux 설치 스크립트만 전송한다.
4. 사용자의 S20+ SSH 주소/포트를 선택할 수 있고 기본값은 기존 10.1.1.202:8022를 사용한다.
5. 전송 전에 모든 파일 존재를 확인하고 SSH/SCP 오류가 발생하면 즉시 명확히 중단한다.
6. 기존 .env, .venv, data DB, logs, SSH/watchdog/runit 서비스 및 Android 앱을 덮어쓰지 않는다.
7. S20+ 내부 적용 스크립트가 백업, Python 전체 회귀 테스트, Core 재시작, health 0.4.2를 검증한다.
8. 전체 업데이트가 실패하면 기존 Python 소스 백업으로 복구하고 오류 코드를 반환한다.
9. 로컬 Git 저장소의 변경·커밋·Push는 하지 않으므로 사용자가 Git Pull만 하고 실행할 수 있다.
10. OpenAI API, 유료 데이터 API, 주식주문 및 APK 재설치 없이 실행한다.
#>
[CmdletBinding()]
param([string]$Target='u0_a435@10.1.1.202',[int]$SshPort=8022)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$files=@(
  (Join-Path $root 'core\app\main.py'),
  (Join-Path $root 'core\app\commands.py'),
  (Join-Path $root 'core\app\ops.py'),
  (Join-Path $root 'core\app\market.py'),
  (Join-Path $root 'core\scripts\run_core.py'),
  (Join-Path $root 'core\tests\test_ops.py'),
  (Join-Path $root 'core\tests\test_market_fallback.py'),
  (Join-Path $root 'core\scripts\diagnose-market.py'),
  (Join-Path $root 'core\scripts\apply-v0.4.2.sh')
)
foreach($f in $files) {
  if(-not (Test-Path -LiteralPath $f -PathType Leaf)){throw "배포 파일 없음: $f. Git Pull을 확인하세요."}
}
Write-Host "[INFO] AngaeBot v0.4.2 Python Core 배포 -> $Target port $SshPort"
& ssh -p $SshPort $Target 'mkdir -p ~/angaebot/update_v042'
if($LASTEXITCODE -ne 0){throw "S20+ SSH 접근 실패: $LASTEXITCODE"}
& scp -P $SshPort @files "${Target}:~/angaebot/update_v042/"
if($LASTEXITCODE -ne 0){throw "S20+ 소스 전송 실패: $LASTEXITCODE"}
& ssh -p $SshPort $Target 'bash ~/angaebot/update_v042/apply-v0.4.2.sh'
if($LASTEXITCODE -ne 0){throw "Termux 배포 검사 실패: $LASTEXITCODE. 백업 및 로그 확인"}
Write-Host '[OK] Python Core v0.4.2 배포 완료. Android APK 재설치 불필요.' -ForegroundColor Green
