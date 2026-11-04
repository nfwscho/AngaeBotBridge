#requires -version 5.1
<#
AngaeBot v0.5.2 Windows-to-Termux deployment — full existing/new features and protection
1. Updates only Python Core to add five-session close history and 21/63-session realized volatility.
2. Preserves existing Memory7/stock group/US market-cap preset/stock quote functions and request logs.
3. Leaves Android Bridge/KakaoTalk notification listener/RemoteInput/UI/App APK/data untouched.
4. Leaves .env authentication, SQLite databases, Python venv, logs, boot, SSH and watchdog intact.
5. Requires user to git pull first, checks exact 10 source/test files and deploy installer for existence.
6. Sends only reviewed files via existing SSH/SCP to Galaxy S20+ Termux localhost-bound Python Core.
7. Remote script makes source backups and performs Python syntax + full regression tests before restart.
8. Remote script automatically restores previous source on failure and verifies /v1/health v0.5.2.
9. Does not run OpenAI/Ollama or add price alerts, scheduled checks, outbound Kakao messages or trades.
10. Existing Android Bridge supports the '주식' command; no APK rebuild/install is required.
11. Does not modify Windows Git status, commit, push, user preferences or local source files.
12. All operational error messages are ASCII to avoid Windows console encoding corruption.
#>
[CmdletBinding()]
param([string]$Target='u0_a435@10.1.1.202',[int]$SshPort=8022)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$files=@(
  (Join-Path $root 'core\app\main.py'),
  (Join-Path $root 'core\app\commands.py'),
  (Join-Path $root 'core\app\watchlists.py'),
  (Join-Path $root 'core\app\history.py'),
  (Join-Path $root 'core\scripts\run_core.py'),
  (Join-Path $root 'core\tests\test_ops.py'),
  (Join-Path $root 'core\tests\test_watchlists.py'),
  (Join-Path $root 'core\tests\test_watchlist_api.py'),
  (Join-Path $root 'core\tests\test_history.py'),
  (Join-Path $root 'core\tests\test_history_api.py'),
  (Join-Path $root 'core\scripts\apply-v0.5.2.sh')
)
foreach($file in $files){
  if(-not (Test-Path -LiteralPath $file -PathType Leaf)){
    throw "Missing source file: $file. Run git pull --ff-only origin main first."
  }
}
Write-Host "[INFO] Deploy AngaeBot v0.5.2 Python Core -> ${Target} (SSH port ${SshPort})"
& ssh -p $SshPort $Target 'mkdir -p ~/angaebot/update_v052'
if($LASTEXITCODE -ne 0){ throw "SSH setup failed: $LASTEXITCODE" }
& scp -P $SshPort @files "${Target}:~/angaebot/update_v052/"
if($LASTEXITCODE -ne 0){ throw "SCP upload failed: $LASTEXITCODE" }
& ssh -p $SshPort $Target 'bash ~/angaebot/update_v052/apply-v0.5.2.sh'
if($LASTEXITCODE -ne 0){ throw "Termux deployment validation failed: $LASTEXITCODE. Check backup/remote output." }
Write-Host '[OK] AngaeBot Python Core v0.5.2 deployment completed. Android APK reinstall not required.' -ForegroundColor Green
