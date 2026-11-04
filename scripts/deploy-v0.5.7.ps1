#requires -version 5.1
<#
AngaeBot v0.5.7 Windows to Termux installer — complete behavior and safety specification
1. Preserves all existing KakaoTalk auto-reply, Android Bridge UI, battery and numeric menu behavior.
2. Upgrades only Python Core Korean Naver realtime-polling-first quote fetching and metadata formatting.
3. Korean KRX last trade and optional NXT/unknown-exchange overmarket quote are shown separately.
4. Preserves all foreign quote feeds, Memory7/watchlists, grouping, history, volatility and all logs.
5. Uses existing SSH/SCP to the user's Galaxy S20+; does not touch or reinstall the Android APK.
6. Uploads exactly the modified sources and tests to a separate update directory without changing live .env/DB.
7. Remote script backs up overwritten source files, runs full Python tests, restarts Core only after passing.
8. Remote script checks authenticated health v0.5.7 and restores all previous source files on failure.
9. Does not change credentials, Termux Python environment, boot, SSH, watchdog or UI settings.
10. No background polling, battery-intensive websocket, AI API use, price alert or stock trade is added.
11. Existing Core jobs/events/logs continue recording through the same original command flow.
12. User must git pull to receive this script; does not commit, reset, rebase or push user's Windows files.
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
  (Join-Path $root 'core\tests\test_naver_realtime.py'),
  (Join-Path $root 'core\tests\test_market_fallback.py'),
  (Join-Path $root 'core\tests\test_history_api.py'),
  (Join-Path $root 'core\tests\test_ops.py'),
  (Join-Path $root 'core\tests\test_watchlist_api.py'),
  (Join-Path $root 'core\scripts\apply-v0.5.7.sh')
)
foreach($file in $files){
  if(-not (Test-Path -LiteralPath $file -PathType Leaf)) {
    throw "Missing source file: $file. Please git pull --ff-only origin main first."
  }
}
Write-Host "[INFO] Deploy AngaeBot v0.5.7 Python Core -> ${Target} (SSH port ${SshPort})"
& ssh -p $SshPort $Target 'mkdir -p ~/angaebot/update_v057'
if($LASTEXITCODE -ne 0){ throw "SSH setup failed: $LASTEXITCODE" }
& scp -P $SshPort @files "${Target}:~/angaebot/update_v057/"
if($LASTEXITCODE -ne 0){ throw "SCP upload failed: $LASTEXITCODE" }
& ssh -p $SshPort $Target 'bash ~/angaebot/update_v057/apply-v0.5.7.sh'
if($LASTEXITCODE -ne 0){ throw "Termux deployment validation failed: $LASTEXITCODE. Review remote logs/backup." }
Write-Host '[OK] AngaeBot Python Core v0.5.7 deployment completed. Android APK reinstall NOT required.' -ForegroundColor Green
