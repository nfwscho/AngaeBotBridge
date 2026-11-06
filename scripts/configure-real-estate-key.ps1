# AngaeBot MOLIT key setup - functions and safety behavior
# 1. Uses the existing Windows SSH alias "angaebot" to reach Galaxy S20+ Termux.
# 2. Checks the existing private core/.env and Python runtime before writing.
# 3. Uploads a key-free Python helper to the private remote Core directory.
# 4. Prompts for the API key using a hidden SecureString input.
# 5. Passes the key over SSH stdin only, never on command lines or in Git files.
# 6. Preserves all unrelated .env settings and existing DB, logs, and Android app data.
# 7. The remote helper performs atomic replacement with 0600 private permissions.
# 8. Restarts only the existing angaebot-core runit service after successful update.
# 9. Removes the temporary key-free helper on exit, including error paths.
# 10. Prints only non-secret success/failure statuses, never the submitted key.
# 11. Optional -SkipRestart permits safe configuration without restarting Core.
# 12. The script itself contains no credentials and is safe to commit to GitHub.
[CmdletBinding()]
param(
    [string]$SshHost = 'angaebot',
    [switch]$SkipRestart
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$remoteCore = '/data/data/com.termux/files/home/angaebot/core'
$remoteHelper = "$remoteCore/.configure-real-estate-key.py"
$service = '/data/data/com.termux/files/usr/var/service/angaebot-core'
$localHelper = Join-Path (Split-Path -Parent $PSScriptRoot) 'core\scripts\configure-real-estate-key.py'
$uploaded = $false

if (-not (Test-Path -LiteralPath $localHelper -PathType Leaf)) {
    throw "The key-free configuration helper is missing: $localHelper"
}

try {
    & ssh -o BatchMode=yes -o ConnectTimeout=10 $SshHost "test -f $remoteCore/.env && test -x $remoteCore/.venv/bin/python && test -d $service"
    if ($LASTEXITCODE -ne 0) {
        throw 'S20+ private Core .env / Python / runit service was not found.'
    }

    $remoteDestination = $SshHost + ':' + $remoteHelper
    & scp -q -o BatchMode=yes -o ConnectTimeout=10 $localHelper $remoteDestination
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not stage the key-free configuration helper on S20+.'
    }
    $uploaded = $true

    $secureKey = Read-Host 'Paste MOLIT API key (hidden input)' -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
    try {
        $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        $secureKey.Dispose()
    }

    if ([string]::IsNullOrWhiteSpace($plainKey)) {
        throw 'Empty API key. Existing S20+ configuration has not been modified.'
    }

    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = (Get-Command ssh -CommandType Application -ErrorAction Stop).Source
    $processInfo.Arguments = '-T -o BatchMode=yes -o ConnectTimeout=10 ' + $SshHost + ' ' + $remoteCore + '/.venv/bin/python ' + $remoteHelper
    $processInfo.UseShellExecute = $false
    $processInfo.CreateNoWindow = $true
    $processInfo.RedirectStandardInput = $true
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true
    $process = [System.Diagnostics.Process]::Start($processInfo)
    if ($null -eq $process) {
        throw 'Could not start the authenticated SSH session.'
    }
    try {
        $process.StandardInput.WriteLine($plainKey)
        $process.StandardInput.Close()
        $plainKey = $null
        $output = $process.StandardOutput.ReadToEnd()
        $errorOutput = $process.StandardError.ReadToEnd()
        if (-not $process.WaitForExit(30000)) {
            $process.Kill()
            throw 'S20+ key configuration timed out.'
        }
        if ($process.ExitCode -ne 0 -or $output -notmatch '^OK: MOLIT_API_KEY configured') {
            throw 'S20+ rejected the key or could not update the private .env. Verify the API key and SSH configuration.'
        }
    } finally {
        $plainKey = $null
        $process.Dispose()
    }
    Write-Host '[OK] API key saved privately on S20+ (key not displayed).' -ForegroundColor Green
    if (-not $SkipRestart) {
        & ssh -o BatchMode=yes -o ConnectTimeout=10 $SshHost "sv restart $service && sv status $service"
        if ($LASTEXITCODE -ne 0) {
            throw 'API key was saved, but the Core service restart failed. Check S20+ service state.'
        }
        Write-Host '[OK] Existing Python Core service restarted.' -ForegroundColor Green
    } else {
        Write-Host '[INFO] Key saved; Core service restart skipped by request.'
    }
} finally {
    if ($uploaded) {
        # No API key was ever stored in this temporary helper file.
        try {
            & ssh -q -o BatchMode=yes -o ConnectTimeout=10 $SshHost "rm -f $remoteHelper" | Out-Null
        } catch {
            Write-Warning 'Check for the temporary key-free helper on S20+.'
        }
    }
}
