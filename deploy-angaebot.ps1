# AngaeBot one-command deployment for Windows PowerShell 5.1 and PowerShell 7.
# 1. Fetch and fast-forward the selected GitHub feature branch without discarding local edits.
# 2. Verify the exact commit has a successful GitHub Actions Python Core regression run.
# 3. Wait for CI to finish; abort on failure, timeout, cancellation, or missing checks.
# 4. Reuse the existing 'angaebot' SSH alias and public-key authentication.
# 5. Stage Python Core modules via SCP; preserve SQLite, logs and Android settings.
# 23. Auto-detect Windows core/.env (fallback repository-root .env) and upload it privately via SCP.
# 24. Merge Windows variables into the existing S20+ .env; always preserve S20+ ANGAE_TOKEN.
# 25. Keep S20+-only variables/comments, private 0600 permissions, and an automatic .env rollback copy.
# 26. Validate credentials without printing values; fail safely if the source file is invalid.
# 27. -SkipEnvSync explicitly disables synchronization; if no local .env exists, retain remote settings.
# 28. Run .env merge only after successful SHA-matched tests, before restarting Python Core.
# 29. Remove the staged secret-bearing .env after any failure, including a pre-apply error.
# 6. Validate staged Python modules using the S20+ Python virtual environment.
# 7. Retain temporary rollback copies during deployment and restore them on apply failure.
# 8. Restart only the runit-managed angaebot-core service; preserve watchdog and sshd.
# 9. Check service status and local TCP port after restart, then remove staging files.
# 10. Abort safely on errors; do not deploy a commit without a passing CI result.
# 11. -LocalTests mode runs all Python tests in an isolated Linux staging directory on S20+; no GitHub Actions.
# 12. Local mode validates Python syntax on the S20+ Linux interpreter without modifying production DB/.env/logs.
# 13. Isolated tests must pass before any production Python module replacement or service restart.
# 14. -InstallAndroid preflights a uniquely matched Galaxy S20+ via ADB and builds a tested debug APK before Core deployment.
# 15. APK installs with adb install -r -t only after Core is verified; no uninstall or data wipe.
# 16. Android install failure is reported separately from an already successful Python Core update.
# 17. Detect ADB in Android Studio SDK, environment paths, or a verified Google user cache.
# 18. If ADB is missing, the resolver can download a pinned official archive after license consent.
# 19. Invoke ADB by resolved full path without requiring Windows PATH changes.
# 21. After verified deployment, write minimal non-secret SHA/branch/time/Android status to Core-local metadata.
# 22. Metadata is best-effort after successful service/APK verification; never erase existing DB/logs/data.
# 20. If Java is missing from the shell, reuse Android Studio's bundled JBR
#     for the Gradle APK build without changing machine settings.
# 30. Retry transient GitHub Actions API 408/429/5xx and network timeout errors until WaitMinutes expires.
# 31. Never bypass CI, accept a different SHA/branch, or ignore permanent authentication/API errors.
# 32. Keep the previous successful-run validation and all S20+ deployment, rollback, .env and logging behavior.
# Run: .\deploy-angaebot.ps1
# Option: .\deploy-angaebot.ps1 -WaitMinutes 10
param(
    [string]$Branch = 'feature/compact-all-replies-20261105',
    [string]$Repo = 'nfwscho/AngaeBotBridge',
    [string]$SshHost = 'angaebot',
    [int]$WaitMinutes = 8,
    [switch]$LocalTests,
    [switch]$InstallAndroid,
    [switch]$SkipEnvSync
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$service = '/data/data/com.termux/files/usr/var/service/angaebot-core'
$remoteCore = '/data/data/com.termux/files/home/angaebot/core'
$stage = "$remoteCore/.deploy-staging"
$backup = "$remoteCore/.deploy-rollback"
$deploymentStarted = $false
$coreApplied = $false
$androidSerial = ''
$apkFile = ''
$adbExe = ''
$localEnvPath = ''
$envSyncPrepared = $false
$envStageAttempted = $false

# Only HTTP gateway/network failures are retried. Invalid credentials (401/403)
# and API request errors (such as 404) must still abort immediately.
function Test-TransientGithubApiFailure([System.Management.Automation.ErrorRecord]$Failure) {
    $exception = $Failure.Exception
    $httpStatus = $null
    try {
        if ($null -ne $exception.Response -and $null -ne $exception.Response.StatusCode) {
            $httpStatus = [int]$exception.Response.StatusCode
        }
    } catch {
        # Some PowerShell / .NET versions do not expose an HTTP response on timeout.
    }
    if ($null -ne $httpStatus) {
        return ($httpStatus -in @(408, 429, 500, 502, 503, 504))
    }
    if ($exception -is [System.Net.WebException]) {
        return ($exception.Status -in @(
            [System.Net.WebExceptionStatus]::Timeout,
            [System.Net.WebExceptionStatus]::ConnectFailure,
            [System.Net.WebExceptionStatus]::ConnectionClosed,
            [System.Net.WebExceptionStatus]::ReceiveFailure,
            [System.Net.WebExceptionStatus]::SendFailure,
            [System.Net.WebExceptionStatus]::KeepAliveFailure
        ))
    }
    return $false
}

function Assert-Exit([string]$Message) {
    if ($LASTEXITCODE -ne 0) { throw "$Message (exit=$LASTEXITCODE)" }
}
function Invoke-Remote([string]$Command, [string]$Description) {
    & ssh -o BatchMode=yes -o ConnectTimeout=10 $SshHost $Command
    Assert-Exit $Description
}
function Undo-Remote {
    Write-Warning 'Deployment failed. Restoring previous Python modules, private .env and restarting Core.'
    & ssh -o BatchMode=yes $SshHost "if test -f $backup/.env; then cp -p $backup/.env $remoteCore/.env && chmod 600 $remoteCore/.env || exit 1; fi; cp -p $backup/*.py $remoteCore/app/ && sv restart $service"
    if ($LASTEXITCODE -ne 0) { Write-Warning 'Automatic rollback failed. Check remote service and backup files.' }
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

    if (-not $SkipEnvSync) {
        $coreEnv = Join-Path $root 'core\.env'
        $rootEnv = Join-Path $root '.env'
        if (Test-Path -LiteralPath $coreEnv -PathType Leaf) {
            $localEnvPath = $coreEnv
        } elseif (Test-Path -LiteralPath $rootEnv -PathType Leaf) {
            $localEnvPath = $rootEnv
        } else {
            Write-Warning '[Env] No Windows core\.env or repository-root .env found. Existing S20+ .env will be preserved.'
        }
        if ($localEnvPath) {
            $localEnvItem = Get-Item -LiteralPath $localEnvPath -Force
            if (($localEnvItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw '[Env] Local .env is a reparse point / symlink; deployment refused.'
            }
            if ($localEnvItem.Length -gt 65536) {
                throw '[Env] Windows .env exceeds the 64 KiB safety limit; deployment refused.'
            }
            Write-Host "[Env] Windows .env detected: $localEnvPath (content and keys are never printed)" -ForegroundColor Cyan
        }
    } else {
        Write-Host '[Env] Explicit -SkipEnvSync: existing S20+ .env will not be modified.'
    }

    if ($LocalTests) {
        Write-Host '[2/6] Run isolated Linux regression on S20+ (no GitHub Actions)' -ForegroundColor Cyan
        $testStage = "/data/data/com.termux/files/home/angaebot-regression-$sha"
        $testPython = "$remoteCore/.venv/bin/python"
        Invoke-Remote "test -x $testPython && mkdir -p $testStage" 'S20+ Python regression environment unavailable'
        try {
            foreach ($folder in @('app', 'tests', 'scripts')) {
                $source = Join-Path (Join-Path $root 'core') $folder
                if (-not (Test-Path $source)) { throw "Missing regression source folder: $source" }
                & scp -r -o BatchMode=yes $source "${SshHost}:$testStage/"
                Assert-Exit "Unable to stage $folder for isolated tests"
            }
            Invoke-Remote "cd $testStage && PYTHONDONTWRITEBYTECODE=1 $testPython -m compileall -q app && PYTHONDONTWRITEBYTECODE=1 $testPython -m unittest discover -s tests -v" 'Isolated S20+ Linux regression failed; deployment refused'
            Write-Host 'Isolated Linux Python Core regression tests PASSED' -ForegroundColor Green
        } finally {
            & ssh -o BatchMode=yes $SshHost "rm -rf $testStage"
            if ($LASTEXITCODE -ne 0) { Write-Warning 'Isolated regression staging cleanup failed; inspect S20+ temporary folder.' }
        }
    } else {
    Write-Host '[2/6] Verify GitHub Actions regression tests' -ForegroundColor Cyan
    $deadline = (Get-Date).AddMinutes($WaitMinutes)
    $passed = $false
    $headers = @{ 'Accept' = 'application/vnd.github+json'; 'User-Agent' = 'AngaeBot-Deploy' }
    if ($env:GH_TOKEN) { $headers['Authorization'] = "Bearer $env:GH_TOKEN" }
    $apiFailures = 0
    do {
        $api = "https://api.github.com/repos/$Repo/actions/runs?head_sha=$sha&per_page=30"
        try {
            $result = Invoke-RestMethod -Uri $api -Headers $headers -TimeoutSec 20
            $apiFailures = 0
        } catch {
            if (-not (Test-TransientGithubApiFailure $_)) { throw }
            $apiFailures++
            if ((Get-Date) -ge $deadline) {
                throw "GitHub Actions API still unavailable after $WaitMinutes minutes. No CI bypass; deployment stopped."
            }
            $retrySeconds = [int][Math]::Min(20, 5 * [Math]::Pow(2, [Math]::Min($apiFailures - 1, 2)))
            Write-Warning "[CI] Temporary GitHub Actions API gateway/network error (attempt $apiFailures). Retrying in $retrySeconds seconds; target SHA remains $sha."
            Start-Sleep -Seconds $retrySeconds
            continue
        }
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

    }

    if ($InstallAndroid) {
        Write-Host '[Android] Locate S20+ and build tested APK before changing Core' -ForegroundColor Cyan
        $adbResolver = Join-Path $root 'scripts\resolve-adb.ps1'
        if (-not (Test-Path -LiteralPath $adbResolver -PathType Leaf)) {
            throw 'Android ADB resolver script is missing; fetch the newest feature branch.'
        }
        . $adbResolver
        $adbExe = Resolve-AngaeAdb -ProjectRoot $root
        & $adbExe version | Out-Null
        Assert-Exit 'Resolved ADB failed the version check'
        $allDevices = @(& $adbExe devices)
        Assert-Exit 'ADB device listing failed'
        $deviceLines = @($allDevices | Where-Object { $_ -match '^\S+\s+device\s*$' })
        if ($deviceLines.Count -eq 0) {
            $untrusted = @($allDevices | Where-Object { $_ -match '^\S+\s+(unauthorized|offline)' })
            if ($untrusted.Count -gt 0) {
                throw 'Android device unauthorized/offline. Unlock S20+, enable USB debugging, and approve the PC authorization popup.'
            }
            throw 'No authorized Android device found via USB ADB. Connect S20+, enable USB debugging, and approve this PC on the phone.'
        }
        $s20 = @()
        foreach ($line in $deviceLines) {
            $serial = ($line.Trim() -split '\s+')[0]
            $model = (& $adbExe -s $serial shell getprop ro.product.model | Out-String).Trim()
            Assert-Exit 'ADB model lookup failed'
            if ($model -match '^(SM-G985|SM-G986)') { $s20 += $serial }
        }
        if ($s20.Count -ne 1) {
            throw 'Expected exactly one authorized Galaxy S20+ (SM-G985/SM-G986) via ADB.'
        }
        $androidSerial = $s20[0]
        Write-Host "  Android target: $androidSerial (Galaxy S20+)"
        $gradle = Join-Path $root 'gradlew.bat'
        $apkFile = Join-Path $root 'app\build\outputs\apk\debug\app-debug.apk'
        if (-not (Test-Path $gradle)) { throw 'Gradle wrapper missing.' }
        if ([string]::IsNullOrWhiteSpace($env:JAVA_HOME) -and
            -not (Get-Command 'java.exe' -ErrorAction SilentlyContinue)) {
            $jbrCandidates = @()
            if ($env:ProgramFiles) {
                $jbrCandidates += (Join-Path $env:ProgramFiles 'Android\Android Studio\jbr')
            }
            if ($env:LOCALAPPDATA) {
                $jbrCandidates += (Join-Path $env:LOCALAPPDATA 'Programs\Android Studio\jbr')
            }
            foreach ($jbr in $jbrCandidates) {
                if (Test-Path -LiteralPath (Join-Path $jbr 'bin\java.exe') -PathType Leaf) {
                    $env:JAVA_HOME = $jbr
                    Write-Host "  Java resolved from Android Studio: $env:JAVA_HOME" -ForegroundColor Green
                    break
                }
            }
        }
        & $gradle --no-daemon :app:testDebugUnitTest :app:assembleDebug
        Assert-Exit 'Android tests or APK build failed; no deployment was attempted'
        if (-not (Test-Path $apkFile)) { throw 'Debug APK not found; deployment stopped.' }
    }

    Write-Host '[3/6] Prepare remote staging directories' -ForegroundColor Cyan
    Invoke-Remote "test -d $remoteCore/app && test -x $remoteCore/.venv/bin/python && test -d $service && test -f $remoteCore/.env && mkdir -p $stage $backup && chmod 700 $stage $backup && rm -f $stage/*.py $backup/*.py $stage/.env.windows $stage/.env-merge.py $backup/.env" 'S20+ environment check failed'

    Write-Host '[4/6] Upload and compile-check Python modules' -ForegroundColor Cyan
    $files = @(Get-ChildItem -LiteralPath (Join-Path $root 'core/app') -Filter '*.py' -File)
    if ($files.Count -lt 1) { throw 'No Python modules found for upload.' }
    $paths = @($files | ForEach-Object { $_.FullName })
    & scp -o BatchMode=yes @paths "${SshHost}:$stage/"
    Assert-Exit 'SCP upload failed'
    Invoke-Remote "$remoteCore/.venv/bin/python -m compileall -q $stage" 'S20+ Python compile check failed'

    if ($localEnvPath) {
        Write-Host '[Env] Upload Windows .env privately and validate merge helper' -ForegroundColor Cyan
        $envHelper = Join-Path $root 'core\scripts\merge-deployment-env.py'
        if (-not (Test-Path -LiteralPath $envHelper -PathType Leaf)) {
            throw '[Env] Missing merge-deployment-env.py from the selected branch.'
        }
        & scp -q -o BatchMode=yes $envHelper ($SshHost + ':' + $stage + '/.env-merge.py')
        Assert-Exit '[Env] Unable to upload merge helper'
        $envStageAttempted = $true
        & scp -q -o BatchMode=yes $localEnvPath ($SshHost + ':' + $stage + '/.env.windows')
        Assert-Exit '[Env] Unable to stage Windows .env securely'
        Invoke-Remote "chmod 600 $stage/.env.windows $stage/.env-merge.py && $remoteCore/.venv/bin/python -m py_compile $stage/.env-merge.py" '[Env] Remote helper syntax or permissions invalid'
        $envSyncPrepared = $true
    }

    Write-Host '[5/6] Apply modules, merge private .env, and restart Core service' -ForegroundColor Cyan
    Invoke-Remote "cp -p $remoteCore/app/*.py $backup/" 'Temporary rollback copy failed'
    $deploymentStarted = $true
    if ($envSyncPrepared) {
        Invoke-Remote "$remoteCore/.venv/bin/python $stage/.env-merge.py $remoteCore/.env $stage/.env.windows $backup/.env" '[Env] Windows .env merge failed; deployment rolled back'
    }
    Invoke-Remote "cp -p $stage/*.py $remoteCore/app/ && sv restart $service" 'Apply or Core service restart failed'

    Write-Host '[6/6] Verify Core service and TCP port' -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    Invoke-Remote "sv status $service && $remoteCore/.venv/bin/python -c 'import socket; socket.create_connection((socket.inet_ntoa(bytes([127,0,0,1])),8765),5).close()'" 'Core service verification failed'
    $deploymentStarted = $false
    $coreApplied = $true
    Invoke-Remote "rm -rf $stage $backup" 'Staging cleanup failed'
    if ($InstallAndroid) {
        Write-Host '[Android] Upgrade existing S20+ Bridge without clearing app data' -ForegroundColor Cyan
        & $adbExe -s $androidSerial install -r -t $apkFile
        Assert-Exit 'Android APK update failed; Core is already updated'
        $packagePath = (& $adbExe -s $androidSerial shell pm path kr.co.angaebot.bridge | Out-String).Trim()
        Assert-Exit 'Android package verification failed; Core is already updated'
        if ($packagePath -notmatch 'package:') { throw 'Android package not installed after update; Core is already updated.' }
        Write-Host "Android APK verified on $androidSerial" -ForegroundColor Green
    }
    # Record only the success state after Core verification and optional Android installation.
    # This metadata contains no tokens, personal data or secrets.
    $metaTemp = Join-Path ([System.IO.Path]::GetTempPath()) ('angaebot-release-' + [guid]::NewGuid().ToString('N') + '.json')
    try {
        $metadata = @{
            sha = $sha
            branch = $Branch
            deployed_at = (Get-Date).ToString('o')
            android_updated = [bool]$InstallAndroid
        } | ConvertTo-Json -Compress
        [System.IO.File]::WriteAllText($metaTemp, $metadata, (New-Object System.Text.UTF8Encoding($false)))
        & scp -o BatchMode=yes $metaTemp "${SshHost}:$remoteCore/.deploy-info.json.tmp"
        Assert-Exit 'Deployment metadata transfer failed'
        Invoke-Remote "mv -f $remoteCore/.deploy-info.json.tmp $remoteCore/.deploy-info.json" 'Deployment metadata finalize failed'
        Write-Host 'Deployment metadata recorded for the settings menu' -ForegroundColor Green
    } catch {
        Write-Warning "Deployment succeeded, but read-only deployment record was not updated: $($_.Exception.Message)"
    } finally {
        Remove-Item -LiteralPath $metaTemp -Force -ErrorAction SilentlyContinue
    }
    if ($envSyncPrepared) { Write-Host '[Env] Windows .env synchronized; S20+ ANGAE_TOKEN and server-only settings preserved.' -ForegroundColor Green }
    Write-Host "Deployment successful: $sha" -ForegroundColor Green
} catch {
    Write-Warning "Deployment stopped: $($_.Exception.Message)"
    if ($deploymentStarted) { Undo-Remote }
    if ($coreApplied -and $InstallAndroid) {
        Write-Warning 'Core deployment completed, but Android upgrade/verification may be incomplete.'
    }
    exit 1
} finally {
    if ($envStageAttempted) {
        # Never leave the copied private credential in staging after a failed pre-apply step.
        try {
            & ssh -q -o BatchMode=yes -o ConnectTimeout=10 $SshHost "rm -f $stage/.env.windows" | Out-Null
            if ($LASTEXITCODE -ne 0) { Write-Warning '[Env] Verify that S20+ temporary .env was removed.' }
        } catch {
            Write-Warning '[Env] Verify that S20+ temporary .env was removed.'
        }
    }
    Set-Location $root
}
