#requires -version 5.1
<#
앙개봇 v0.4.3 Windows SSH 배포기 — 기존 프로그램 모든 기능 및 로그 보존 설명
1. Windows GitHub 최신 소스에서 Python Core 3개 파일/진단 도구/회귀 테스트 2개만 Galaxy S20+ Termux로 전송한다.
2. Android APK/Kotlin UI/NotificationListener/RemoteInput/SQLite 앱 로그, 원격 카톡 명령을 변경하지 않는다.
3. 기존 주식 메모리7 8종목 및 7개 정상 종목의 공급자·가격 출력·타임아웃·캐시를 유지한다.
4. 키오시아 Yahoo Japan HTML 날짜 변화 대응 및 일본 증권사 정규장 공개 시세만 보완한다.
5. SSH 대상/포트를 파라미터로 지정 가능하며 기본값은 기존 10.1.1.202:8022다.
6. 파일 존재 및 SSH/SCP 종료 코드를 확인하고 오류가 있으면 전송/설치를 중단한다.
7. Termux 적용 스크립트는 변경 파일 백업, 전체 unittest, 서버 재시작, 인증 Health 버전 확인을 수행한다.
8. .env, .venv, SQLite DB, 로그, SSH/watchdog/부팅 서비스/백업은 건드리거나 삭제하지 않는다.
9. 원격 적용 실패 시 백업 소스를 복원하고 실패 코드와 원인을 표시한다.
10. 유료 API/OpenAI API, 자동매매, Python 패키지 추가 설치 및 Android APK 설치는 하지 않는다.
#>
[CmdletBinding()]
param([string]$Target='u0_a435@10.1.1.202',[int]$SshPort=8022)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$files=@(
    (Join-Path $root 'core\app\market.py'),
    (Join-Path $root 'core\app\main.py'),
    (Join-Path $root 'core\app\commands.py'),
    (Join-Path $root 'core\scripts\diagnose-market.py'),
    (Join-Path $root 'core\tests\test_ops.py'),
    (Join-Path $root 'core\tests\test_market_japan_v043.py'),
    (Join-Path $root 'core\scripts\apply-v0.4.3.sh')
)
foreach($file in $files){
    if(-not (Test-Path -LiteralPath $file -PathType Leaf)){
        throw "Missing deploy file: $file. Run git pull --ff-only origin main"
    }
}
Write-Host "[INFO] Deploy AngaeBot v0.4.3 to $Target (SSH $SshPort)"
& ssh -p $SshPort $Target 'mkdir -p ~/angaebot/update_v043'
if($LASTEXITCODE -ne 0){throw "SSH directory setup failed: $LASTEXITCODE"}
& scp -P $SshPort @files "${Target}:~/angaebot/update_v043/"
if($LASTEXITCODE -ne 0){throw "SCP upload failed: $LASTEXITCODE"}
& ssh -p $SshPort $Target 'bash ~/angaebot/update_v043/apply-v0.4.3.sh'
if($LASTEXITCODE -ne 0){throw "Termux validation/deployment failed: $LASTEXITCODE. Check logs and backup."}
Write-Host '[OK] AngaeBot Python Core v0.4.3 deployment completed' -ForegroundColor Green
Write-Host '[INFO] Android APK rebuild not required'
