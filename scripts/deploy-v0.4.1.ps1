#requires -version 5.1
<#
앙개봇 v0.4.1 Windows PowerShell SSH 배포기 — 전체 기능 상세 설명
1. 기존 GitHub 저장소의 v0.4.1 메모리7 모듈과 FastAPI·운영 코드를 S20+로 복사한다.
2. 기존 ssh/scp 포트 8022 경로를 사용하며 대상은 지정하지 않으면 10.1.1.202이다.
3. 운영 코어 소스 5개, Python 테스트 3개, Termux 적용 스크립트 1개의 파일만 전송한다.
4. 로컬 Git 작업트리, .env 인증키, SQLite, venv, 로그, Android UI/수신/답장은 건드리지 않는다.
5. 각 파일 존재를 확인한 뒤 원격 업데이트 폴더를 만들고 SCP 반환 코드를 검사한다.
6. 백업·문법·전체 테스트·Core 재시작·health 버전 검증은 Termux apply-v0.4.1.sh가 담당한다.
7. SSH/Watchdog/부팅 스크립트는 재시작하거나 덮어쓰지 않는다.
8. 실행 실패 시 원인을 출력하고 수동 파일 복사를 요구하지 않는다.
9. Android APK 빌드/설치는 별도로 실행해야 한다.
10. OpenAI API·유료 시세 API를 사용하거나 가격 숫자를 작성하지 않는다.
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
    (Join-Path $root 'core\tests\test_market.py'),
    (Join-Path $root 'core\tests\test_market_api.py'),
    (Join-Path $root 'core\tests\test_ops.py'),
    (Join-Path $root 'core\scripts\apply-v0.4.1.sh')
)
foreach($f in $files) { if(-not (Test-Path -LiteralPath $f -PathType Leaf)) { throw "배포 파일 누락: $f. git pull을 확인하세요." } }
Write-Host "[INFO] AngaeBot v0.4.1 -> $Target port $SshPort"
& ssh -p $SshPort $Target 'mkdir -p ~/angaebot/update_v041'
if($LASTEXITCODE -ne 0) { throw "원격 임시 폴더 생성 실패: $LASTEXITCODE" }
& scp -P $SshPort @files "${Target}:~/angaebot/update_v041/"
if($LASTEXITCODE -ne 0) { throw "SCP 업로드 실패: $LASTEXITCODE" }
& ssh -p $SshPort $Target 'bash ~/angaebot/update_v041/apply-v0.4.1.sh'
if($LASTEXITCODE -ne 0) { throw "Python Core 배포 실패. 서버 로그 및 백업 확인 필요: $LASTEXITCODE" }
Write-Host '[OK] AngaeBot v0.4.1 Python 배포 완료. Android APK 빌드/업데이트는 별도 진행하세요.' -ForegroundColor Green
