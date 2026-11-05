#requires -version 5.1
<#
AngaeBot Core v0.5.10 Windows to Termux safe deploy — complete existing feature preservation
1. Keeps KakaoTalk notification listener, Android UI, battery suffix, whitelisted rooms/senders, numeric selection unchanged.
2. Preserves Korea Naver realtime, Japan quotes, existing Yahoo/Nasdaq US price checks and source summary.
3. Adds two validated fallback sources for the most recent finished US regular-session closes.
4. Uploads only changed Core sources and regression tests to Galaxy S20+ over the existing SSH/SCP channel.
5. Does not touch Android APK, token/.env, SQLite database, logs, jobs/events, AI sessions or stock groups.
6. Makes source backups and validates syntax and full Python test suite before restarting the Core service.
7. Restores previous source if validation, restart, or authenticated health version check fails.
8. Supports existing core version via 'git pull --ff-only origin main' and does not reset or commit local user files.
9. Preserves runit watchdog, Termux autostart, timezones, permissions, menu handling and all prior operational logs.
10. No background polling, paid key, new app permission, AI vendor/API, notifications or stock trades.
11. Prints clear ASCII success/error messages; does not claim remote Nasdaq/Naver service availability before testing.
#>
[CmdletBinding()]
param([string]$Target='u0_a435@10.1.1.202',[int]$SshPort=8022)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$files=@(
  (Join-Path $root 'core\app\market.py'),
  (Join-Path $root 'core\app\main.py'),
  (Join-Path $root 'core\app\commands.py'),
  (Join-Path $root 'core\scripts\run_core.py'),
  (Join-Path $root 'core\tests\test_ops.py'),
  (Join-Path $root 'core\tests\test_history_api.py'),
  (Join-Path $root 'core\tests\test_watchlist_api.py'),
  (Join-Path $root 'core\tests\test_us_fallback.py'),
  (Join-Path $root 'core\tests\test_us_daily_recovery.py'),
  (Join-Path $root 'core\scripts\apply-v0.5.10.sh')
)
foreach ($file in $files) {
  if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
    throw "Missing source: $file. First run git pull --ff-only origin main."
  }
}
Write-Host "[INFO] Deploy AngaeBot Core v0.5.10 -> ${Target} (SSH ${SshPort})"
& ssh -p $SshPort $Target 'mkdir -p ~/angaebot/update_v0510'
if ($LASTEXITCODE -ne 0) { throw "SSH connection failed: $LASTEXITCODE" }
& scp -P $SshPort @files "${Target}:~/angaebot/update_v0510/"
if ($LASTEXITCODE -ne 0) { throw "SCP file upload failed: $LASTEXITCODE" }
& ssh -p $SshPort $Target 'bash ~/angaebot/update_v0510/apply-v0.5.10.sh'
if ($LASTEXITCODE -ne 0) { throw "Core deploy failed: $LASTEXITCODE. See output and backup path." }
Write-Host '[OK] AngaeBot Python Core v0.5.10 deployment completed. Android APK reinstall NOT required.' -ForegroundColor Green
