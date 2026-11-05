#requires -version 5.1
<#
AngaeBot v0.5.9 Windows to Termux installer — complete behavior and safety specification
1. Preserves Android KakaoTalk listener/RemoteInput/UI, allowed rooms and senders, numeric selection and battery suffix.
2. Preserves exact domestic Naver KRX/NXT and Japanese fallback logic, original memory7/watchlists and logs.
3. Updates only Python Core v0.5.9: compact per-market source/time footers while preserving existing provider fallback.
4. Keeps symbol, last-trade timestamp, currency, net change and percent validation, without changes to quote fetching.
5. Groups Korea/US/Japan sources and delay status once after the numbered list and preserves per-stock after-market prices.
6. Leaves SQLite jobs/events/AI/history/group records, all .env tokens, Android APK and settings untouched.
7. Uploads only exact source and test files by SSH/SCP to the existing S20+ Termux service.
8. Remote updater checks files/settings/timezones, backs up old source and runs the full test suite on isolated DB.
9. If validation/restart fails, remote updater restores previous source and preserves running service.
10. Verifies authenticated /v1/health version 0.5.9 after restart, avoiding false success messages.
11. Does not introduce an OpenAI/API key, auto-order, price watch, battery-consuming websocket or scheduling.
12. Preserves old logging including receive, command, success/failure, stock retries and Android reply logs.
#>
[CmdletBinding()]
param([string]$Target='u0_a435@10.1.1.202',[int]$SshPort=8022)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$files=@(
  (Join-Path $root 'core\app\market.py'),
  (Join-Path $root 'core\app\watchlists.py'),
  (Join-Path $root 'core\app\main.py'),
  (Join-Path $root 'core\app\commands.py'),
  (Join-Path $root 'core\scripts\run_core.py'),
  (Join-Path $root 'core\tests\test_market_source_summary.py'),
  (Join-Path $root 'core\tests\test_naver_realtime.py'),
  (Join-Path $root 'core\tests\test_ops.py'),
  (Join-Path $root 'core\tests\test_history_api.py'),
  (Join-Path $root 'core\tests\test_watchlist_api.py'),
  (Join-Path $root 'core\scripts\apply-v0.5.9.sh')
)
foreach($file in $files){
  if(-not (Test-Path -LiteralPath $file -PathType Leaf)) {
    throw "Missing source file: $file. Please git pull --ff-only origin main first."
  }
}
Write-Host "[INFO] Deploy AngaeBot v0.5.9 Python Core -> ${Target} (SSH port ${SshPort})"
& ssh -p $SshPort $Target 'mkdir -p ~/angaebot/update_v059'
if($LASTEXITCODE -ne 0){ throw "SSH setup failed: $LASTEXITCODE" }
& scp -P $SshPort @files "${Target}:~/angaebot/update_v059/"
if($LASTEXITCODE -ne 0){ throw "SCP upload failed: $LASTEXITCODE" }
& ssh -p $SshPort $Target 'bash ~/angaebot/update_v059/apply-v0.5.9.sh'
if($LASTEXITCODE -ne 0){ throw "Termux deployment validation failed: $LASTEXITCODE. Review remote logs/backup." }
Write-Host '[OK] AngaeBot Python Core v0.5.9 deployment completed. Android APK reinstall NOT required.' -ForegroundColor Green
