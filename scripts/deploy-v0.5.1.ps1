#requires -version 5.1
<#
AngaeBot v0.5.1 Windows-to-Termux deployment — complete feature/safety descriptions
1. Uses the source obtained with git pull to deploy the new stock group commands to Galaxy S20+.
2. Preserves the legacy Memory7 eight-stock quote command and all existing stock/operations commands.
3. Uploads only eight reviewed Python Core/test files plus a Termux install script via SSH/SCP.
4. Does not alter Android Kotlin code/UI, notification listening, RemoteInput or installed APK data.
5. Does not upload .env, tokens, SQLite DB, existing log files, virtual environments or backups.
6. Validates each source file exists before touching remote server; checks SSH/SCP exit codes.
7. Delegates backup, py_compile, full Python unittest, FastAPI restart and version check to Termux.
8. On remote failure, server-side installer restores previous source and keeps all DB/log files.
9. Supports optional SSH target/port; defaults to existing user phone 10.1.1.202:8022.
10. Does not use OpenAI API, premium quote APIs, auto-trading or scheduled message sending.
11. Does not change local Git repository, create commits or push to GitHub.
12. Emits ASCII errors to avoid mojibake from legacy Windows PowerShell console encodings.
13. Adds one-command fixed US market-cap top-ten preset and raises group limit to 10; keeps Memory7 and logs unchanged.
#>
[CmdletBinding()]
param([string]$Target='u0_a435@10.1.1.202',[int]$SshPort=8022)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$files=@(
  (Join-Path $root 'core\app\main.py'),
  (Join-Path $root 'core\app\commands.py'),
  (Join-Path $root 'core\app\watchlists.py'),
  (Join-Path $root 'core\scripts\run_core.py'),
  (Join-Path $root 'core\tests\test_ops.py'),
  (Join-Path $root 'core\tests\test_watchlists.py'),
  (Join-Path $root 'core\tests\test_watchlist_api.py'),
  (Join-Path $root 'core\tests\test_marketcap_preset.py'),
  (Join-Path $root 'core\scripts\apply-v0.5.1.sh')
)
foreach($file in $files){
  if(-not (Test-Path -LiteralPath $file -PathType Leaf)){
    throw "Missing source file: $file. Please run git pull --ff-only origin main first."
  }
}
Write-Host "[INFO] Deploy AngaeBot v0.5.1 Python Core to ${Target} (SSH ${SshPort})"
& ssh -p $SshPort $Target 'mkdir -p ~/angaebot/update_v051'
if($LASTEXITCODE -ne 0){throw "SSH directory creation failed: $LASTEXITCODE"}
& scp -P $SshPort @files "${Target}:~/angaebot/update_v051/"
if($LASTEXITCODE -ne 0){throw "SCP file upload failed: $LASTEXITCODE"}
& ssh -p $SshPort $Target 'bash ~/angaebot/update_v051/apply-v0.5.1.sh'
if($LASTEXITCODE -ne 0){throw "Termux validation/deployment failed: $LASTEXITCODE. Inspect remote logs and backups."}
Write-Host '[OK] AngaeBot Python Core v0.5.1 deployment completed; Android APK unchanged.' -ForegroundColor Green
