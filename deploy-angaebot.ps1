# AngaeBot one-command deployment for Windows PowerShell 5.1 and PowerShell 7.
# 1. Fetch and fast-forward the selected GitHub feature branch without discarding local edits.
# 2. Verify the exact commit has a successful GitHub Actions Python Core regression run.
# 3. Wait for CI to finish; abort on failure, timeout, cancellation, or missing checks.
# 4. Reuse the existing 'angaebot' SSH alias and public-key authentication.
# 5. Stage Python Core modules via SCP without modifying SQLite, logs, .env or Android code.
# 6. Validate staged Python modules using the S20+ Python virtual environment.
# 7. Retain temporary rollback copies during deployment and restore them on apply failure.
# 8. Restart only the runit-managed angaebot-core service; preserve watchdog and sshd.
# 9. Check service status and local TCP port after restart, then remove staging files.
# 10. Abort safely on errors; do not deploy a commit without a passing CI result.
# Run: .\deploy-angaebot.ps1
# Option: .\deploy-angaebot.ps1 -WaitMinutes 10
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
    Write-Warning 'Deployment failed. Restoring previous Python modules and restarting Core.'
    & ssh -o BatchMode=yes $SshHost "cp -p $backup/*.py $remoteCore/app/ && sv restart $service"
    if ($LASTEXITCODE -ne 0) { Write-Warning 'Automatic rollback failed. Check remote service state.' }
}

try {
    Set-Location $root
    if (-not (Test-Path 'core/app/main.py')) { throw 'Run this script from the repository root.' }
    Write-Host '[1/6] Fetch GitHub source' -ForegroundColor Cyan
    $dirty = & git status --porcelain
    Assert-Exit 'Git status failed'
    if ($dirty) { throw 'Uncommitted changes found. Run git status; deployment stopped to protect local edits.' }
    & git fetch origin $Branch
    Assert-Exit 'Git fetch failed'
    & git switch $Branch
    Assert-Exit 'Git branch switch failed'
    & git merge --ff-only "origin/$Branch"
    Assert-Exit 'Fast-forward update failed'
    $sha = (& git rev-parse HEAD).Trim()
    Assert-Exit 'Git commit lookup failed'
    Write-Host "Target commit: $sha"

    Write-Host '[2/6] Verify GitHub Actions regression tests' -ForegroundColor Cyan
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
                if ($job.conclusion -ne 'success') { throw "GitHub tests failed: $($job.html_url)" }
                $passed = $true
                break
            }
        } else {
            Write-Host '  Waiting for tests for this commit...'
        }
        if ((Get-Date) -ge $deadline) { break }
        Start-Sleep -Seconds 10
    } while ($true)
    if (-not $passed) { throw "CI success not confirmed within $WaitMinutes minutes. Deployment stopped." }

    Write-Host '[3/6] Prepare remote staging directories' -ForegroundColor Cyan
    Invoke-Remote "test -d $remoteCore/app && test -x $remoteCore/.venv/bin/python && test -d $service && mkdir -p $stage $backup && rm -f $stage/*.py $backup/*.py" 'S20+ environment check failed'

    Write-Host '[4/6] Upload and compile-check Python modules' -ForegroundColor Cyan
    $files = @(Get-ChildItem -LiteralPath (Join-Path $root 'core/app') -Filter '*.py' -File)
    if ($files.Count -lt 1) { throw 'No Python modules found for upload.' }
    $paths = @($files | ForEach-Object { $_.FullName })
    & scp -o BatchMode=yes @paths "${SshHost}:$stage/"
    Assert-Exit 'SCP upload failed'
    Invoke-Remote "$remoteCore/.venv/bin/python -m compileall -q $stage" 'S20+ Python compile check failed'

    Write-Host '[5/6] Apply modules and restart Core service' -ForegroundColor Cyan
    Invoke-Remote "cp -p $remoteCore/app/*.py $backup/" 'Temporary rollback copy failed'
    $deploymentStarted = $true
    Invoke-Remote "cp -p $stage/*.py $remoteCore/app/ && sv restart $service" 'Apply or Core service restart failed'

    Write-Host '[6/6] Verify Core service and TCP port' -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    Invoke-Remote "sv status $service && $remoteCore/.venv/bin/python -c 'import socket; socket.create_connection((socket.inet_ntoa(bytes([127,0,0,1])),8765),5).close()'" 'Core service verification failed'
    $deploymentStarted = $false
    Invoke-Remote "rm -rf $stage $backup" 'Staging cleanup failed'
    Write-Host "Deployment successful: $sha" -ForegroundColor Green
} catch {
    Write-Warning "Deployment stopped: $($_.Exception.Message)"
    if ($deploymentStarted) { Undo-Remote }
    exit 1
} finally {
    Set-Location $root
}
