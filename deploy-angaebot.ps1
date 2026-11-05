# 앙개봇 Windows PowerShell 원클릭 배포 스크립트 - 전체 기능 안내
# 1. GitHub 기능 브랜치의 최신 코드를 Windows 로컬 저장소로 fast-forward 동기화합니다.
# 2. GitHub Actions의 해당 커밋 Python Core 전체 회귀 테스트 성공 여부를 확인합니다.
# 3. 테스트가 진행 중이면 제한 시간 내 대기하고, 실패/취소/시간 초과 시 배포를 차단합니다.
# 4. 기존 SSH config의 angaebot 별칭과 SCP 공개키 인증을 재사용하며 Termux 수동 접속은 필요 없습니다.
# 5. Python Core app/*.py 파일만 S20+의 임시 폴더로 전송하며 .env/SQLite/로그/Android 앱은 건드리지 않습니다.
# 6. S20+의 기존 Python 가상환경에서 전송 파일의 문법을 검사한 뒤 적용합니다.
# 7. 기존 실행 파일은 배포 중에만 임시 보관하며 적용/재시작 실패 시 복원합니다.
# 8. runit의 실제 서비스 절대 경로로 angaebot-core만 재시작하며 watchdog/sshd는 유지합니다.
# 9. 재시작 후 runit 실행 상태와 로컬 API의 TCP 연결을 확인하고 성공/실패를 명확히 표시합니다.
# 10. 모든 단계의 명령 오류를 검사하고 검증되지 않은 소스는 S20+에 적용하지 않습니다.
# 실행: .\deploy-angaebot.ps1
# 선택: .\deploy-angaebot.ps1 -WaitMinutes 10
param(
    [string]$Branch = 'feature/compact-all-replies-20261105',
    [string]$Repo = 'nfwscho/AngaeBotBridge',
    [string]$SshHost = 'angaebot',
    [int]$WaitMinutes = 8
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$service = '/data/data/com.termux/files/usr/var/service/angaebot-core'
$remoteCore = '/data/data/com.termux/files/home/angaebot/core'
$stage = "$remoteCore/.deploy-staging"
$backup = "$remoteCore/.deploy-rollback"
$deploymentStarted = $false

function Assert-Exit([string]$Message) {
    if ($LASTEXITCODE -ne 0) { throw "$Message (exit=$LASTEXITCODE)" }
}
function Invoke-Remote([string]$Command, [string]$Description) {
    & ssh -o BatchMode=yes -o ConnectTimeout=10 $SshHost $Command
    Assert-Exit $Description
}
function Undo-Remote {
    Write-Warning '배포 실패: 기존 Python 소스를 복원하고 서비스를 재시작합니다.'
    & ssh -o BatchMode=yes $SshHost "cp -p $backup/*.py $remoteCore/app/ && sv restart $service"
    if ($LASTEXITCODE -ne 0) { Write-Warning '자동 복원 실패: 원격 상태를 직접 확인해야 합니다.' }
}

try {
    Set-Location $root
    if (-not (Test-Path 'core/app/main.py')) { throw '저장소 루트에서 스크립트를 실행해야 합니다.' }
    Write-Host '[1/6] GitHub 최신 소스 확인' -ForegroundColor Cyan
    $dirty = & git status --porcelain
    Assert-Exit 'git 상태 확인 실패'
    if ($dirty) { throw '로컬 수정 파일이 있습니다. 기존 변경을 보호하기 위해 중단합니다. git status를 확인하세요.' }
    & git fetch origin $Branch
    Assert-Exit 'GitHub fetch 실패'
    & git switch $Branch
    Assert-Exit '브랜치 전환 실패'
    & git merge --ff-only "origin/$Branch"
    Assert-Exit 'fast-forward 업데이트 실패'
    $sha = (& git rev-parse HEAD).Trim()
    Assert-Exit '커밋 조회 실패'
    Write-Host "대상 커밋: $sha"

    Write-Host '[2/6] GitHub Actions 전체 테스트 확인' -ForegroundColor Cyan
    $deadline = (Get-Date).AddMinutes($WaitMinutes)
    $passed = $false
    $headers = @{ 'Accept' = 'application/vnd.github+json'; 'User-Agent' = 'AngaeBot-Deploy' }
    if ($env:GH_TOKEN) { $headers['Authorization'] = "Bearer $env:GH_TOKEN" }
    do {
        $api = "https://api.github.com/repos/$Repo/actions/runs?head_sha=$sha&per_page=30"
        $result = Invoke-RestMethod -Uri $api -Headers $headers -TimeoutSec 20
        $run = @($result.workflow_runs | Where-Object {
            $_.head_sha -eq $sha -and $_.name -eq 'AngaeBot Core regression' -and $_.head_branch -eq $Branch
        } | Sort-Object run_number -Descending | Select-Object -First 1)
        if ($run.Count -gt 0) {
            $job = $run[0]
            Write-Host "  $($job.status) / $($job.conclusion) - $($job.html_url)"
            if ($job.status -eq 'completed') {
                if ($job.conclusion -ne 'success') { throw "GitHub 테스트 실패: $($job.html_url)" }
                $passed = $true
                break
            }
        } else {
            Write-Host '  해당 커밋의 테스트 실행을 기다리는 중...'
        }
        if ((Get-Date) -ge $deadline) { break }
        Start-Sleep -Seconds 10
    } while ($true)
    if (-not $passed) { throw "테스트 성공을 확인하지 못했습니다 ($WaitMinutes 분 제한). 배포하지 않습니다." }

    Write-Host '[3/6] SSH 연결 및 원격 임시 폴더 준비' -ForegroundColor Cyan
    Invoke-Remote "test -d $remoteCore/app && test -x $remoteCore/.venv/bin/python && test -d $service && mkdir -p $stage $backup && rm -f $stage/*.py $backup/*.py" 'S20+ 환경 확인 실패'

    Write-Host '[4/6] Python 파일 SCP 전송 및 문법 검증' -ForegroundColor Cyan
    $files = @(Get-ChildItem -LiteralPath (Join-Path $root 'core/app') -Filter '*.py' -File)
    if ($files.Count -lt 1) { throw '전송할 Python 파일이 없습니다.' }
    $paths = @($files | ForEach-Object { $_.FullName })
    & scp -o BatchMode=yes @paths "${SshHost}:$stage/"
    Assert-Exit 'SCP 전송 실패'
    Invoke-Remote "$remoteCore/.venv/bin/python -m compileall -q $stage" 'S20+ Python 문법 검사 실패'

    Write-Host '[5/6] 적용 및 서비스 재시작' -ForegroundColor Cyan
    Invoke-Remote "cp -p $remoteCore/app/*.py $backup/" '기존 실행 파일 임시 보관 실패'
    $deploymentStarted = $true
    Invoke-Remote "cp -p $stage/*.py $remoteCore/app/ && sv restart $service" '배포 또는 서비스 재시작 실패'

    Write-Host '[6/6] 서비스와 API 확인' -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    Invoke-Remote "sv status $service && $remoteCore/.venv/bin/python -c 'import socket; s=socket.create_connection((\"127.0.0.1\",8765),5); s.close()'" '서비스 검증 실패'
    $deploymentStarted = $false
    Invoke-Remote "rm -rf $stage $backup" '임시 폴더 정리 실패'
    Write-Host "배포 성공: $sha" -ForegroundColor Green
} catch {
    Write-Error "배포 중단: $($_.Exception.Message)"
    if ($deploymentStarted) { Undo-Remote }
    exit 1
} finally {
    Set-Location $root
}
