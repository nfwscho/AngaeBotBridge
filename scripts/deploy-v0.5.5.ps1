#requires -version 5.1
<#
AngaeBot v0.5.5 Windows-to-Termux deployment — full existing/new features and protection
1. Adds a scoped 5-minute menu session and recent safe stock commands while preserving existing stock/AI/Kakao commands.
2. Preserves existing Memory7/stock group/US market-cap preset/stock quote functions and request logs.
3. Leaves Android Bridge/KakaoTalk notification listener/RemoteInput/UI/App APK/data untouched.
4. Leaves .env authentication, SQLite databases, Python venv, logs, boot, SSH and watchdog intact.
5. Requires git pull first, verifies all 17 source/test files and installer before deploying.
6. Sends only reviewed files via existing SSH/SCP to Galaxy S20+ Termux localhost-bound Python Core.
7. Remote script makes source backups and performs Python syntax + full regression tests before restart.
8. Remote script automatically restores previous source on failure and verifies /v1/health v0.5.5.
9. Does not run OpenAI/Ollama or add price alerts, scheduled checks, outbound Kakao messages or trades.
10. Deploy Python Core first, then update Android Bridge v0.4.3 to make numeric-only replies work.
11. Does not modify Windows Git status, commit, push, user preferences or local source files.
12. All operational error messages are ASCII to avoid Windows console encoding corruption.
13. Korean lookup still covers Memory7, US top-10 presets, common synonyms, and room/sender scoped aliases.
14. Compatible with v0.5.2 or v0.5.3: includes timezone fallback, stock groups, aliases and safe tzdata check.
15. Preserves explicit SQLite connection cleanup and adds menu session/isolation/dedup tests.
16. Session state is memory-only and expires in 5 minutes; only safe recent stock read commands may replay.
17. No Android APK install or extra permissions are performed by this Core deployment script.
#>
[CmdletBinding()]
param([string]$Target='u0_a435@10.1.1.202',[int]$SshPort=8022)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$files=@(
  (Join-Path $root 'core\app\main.py'),
  (Join-Path $root 'core\app\selection_menu.py'),
  (Join-Path $root 'core\app\commands.py'),
  (Join-Path $root 'core\app\ops.py'),
  (Join-Path $root 'core\app\watchlists.py'),
  (Join-Path $root 'core\app\history.py'),
  (Join-Path $root 'core\scripts\run_core.py'),
  (Join-Path $root 'core\tests\test_ops.py'),
  (Join-Path $root 'core\tests\test_watchlists.py'),
  (Join-Path $root 'core\tests\test_watchlist_api.py'),
  (Join-Path $root 'core\tests\test_history.py'),
  (Join-Path $root 'core\tests\test_history_api.py'),
  (Join-Path $root 'core\tests\test_ai_api.py'),
  (Join-Path $root 'core\tests\test_market_api.py'),
  (Join-Path $root 'core\tests\test_marketcap_preset.py'),
  (Join-Path $root 'core\tests\test_sqlite_cleanup.py'),
  (Join-Path $root 'core\tests\test_selection_menu.py'),
  (Join-Path $root 'core\scripts\apply-v0.5.5.sh')
)
foreach($file in $files){
  if(-not (Test-Path -LiteralPath $file -PathType Leaf)){
    throw "Missing source file: $file. Run git pull --ff-only origin main first."
  }
}
Write-Host "[INFO] Deploy AngaeBot v0.5.5 Python Core -> ${Target} (SSH port ${SshPort})"
& ssh -p $SshPort $Target 'mkdir -p ~/angaebot/update_v055'
if($LASTEXITCODE -ne 0){ throw "SSH setup failed: $LASTEXITCODE" }
& scp -P $SshPort @files "${Target}:~/angaebot/update_v055/"
if($LASTEXITCODE -ne 0){ throw "SCP upload failed: $LASTEXITCODE" }
& ssh -p $SshPort $Target 'bash ~/angaebot/update_v055/apply-v0.5.5.sh'
if($LASTEXITCODE -ne 0){ throw "Termux deployment validation failed: $LASTEXITCODE. Check backup/remote output." }
Write-Host '[OK] AngaeBot Python Core v0.5.5 deployment completed. Install Android Bridge v0.4.3 after this Core update.' -ForegroundColor Green
