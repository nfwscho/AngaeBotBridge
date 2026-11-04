<#
앙개봇 v0.2.0 안전한 소스 반영 스크립트 — 전체 기능
1. 사용자 기존 경로 D:\stockproj\AngaeBotBridge 와 Git 저장소를 유지한다.
2. v0.1.3에서 변경된 Kotlin/Manifest/Gradle 및 새 Python 설정·클라이언트 파일만 반영한다.
3. 기존 앱 DB/로그/설정, .git, local.properties, Gradle Wrapper JAR, APK를 삭제하지 않는다.
4. 기존 파일을 날짜별 폴더로 먼저 백업한 후 새 파일로 덮어쓴다.
5. core/ Python FastAPI, 관련 테스트·문서, 새 XML만 추가·갱신한다.
6. 빌드/커밋/Push는 자동 실행하지 않으며 사용자가 검증 후 진행한다.
#>
param(
    [string]$TargetRoot = 'D:\stockproj\AngaeBotBridge'
)
$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not (Test-Path (Join-Path $TargetRoot '.git'))) { throw "Git 저장소가 아닙니다: $TargetRoot" }
if (-not (Test-Path (Join-Path $TargetRoot 'app\src\main\java\kr\co\angaebot\bridge\MainActivity.kt'))) { throw '기존 앙개봇 MainActivity.kt를 찾을 수 없습니다.' }
$backupRoot = Join-Path (Split-Path $TargetRoot -Parent) ('AngaeBotBridge_backup_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
$modifiedFiles = @(
  'README.md',
  'BUILD_STATUS.md',
  'app\build.gradle.kts',
  'app\src\main\AndroidManifest.xml',
  'app\src\main\java\kr\co\angaebot\bridge\BotConfig.kt',
  'app\src\main\java\kr\co\angaebot\bridge\CommandParser.kt',
  'app\src\main\java\kr\co\angaebot\bridge\KakaoNotificationListener.kt',
  'app\src\main\java\kr\co\angaebot\bridge\LogRepository.kt',
  'app\src\main\java\kr\co\angaebot\bridge\MainActivity.kt',
  'app\src\main\java\kr\co\angaebot\bridge\NotificationParser.kt',
  'app\src\main\java\kr\co\angaebot\bridge\ReplyManager.kt'
)
$newFiles = @(
  'app\src\main\java\kr\co\angaebot\bridge\PythonBridgeConfig.kt',
  'app\src\main\java\kr\co\angaebot\bridge\PythonBridgeClient.kt',
  'app\src\main\res\xml\network_security_config.xml',
  'docs\UPGRADE_v0.2.0.md',
  'docs\TEST_PLAN_v0.2.0.md',
  'CHANGELOG_v0.2.0.md',
  'scripts\apply-v0.2.0.ps1'
)
foreach($relative in $modifiedFiles + $newFiles) {
  $src = Join-Path $sourceRoot $relative
  $dst = Join-Path $TargetRoot $relative
  if (-not (Test-Path $src)) { throw "소스 파일 없음: $src" }
  if (Test-Path $dst) {
    $backup = Join-Path $backupRoot $relative
    New-Item -ItemType Directory -Path (Split-Path $backup -Parent) -Force | Out-Null
    Copy-Item $dst $backup -Force
  }
  New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
  Copy-Item $src $dst -Force
}
# Core is new to v0.2.0; overwrite only tracked source files and avoid replacing .env/data/logs.
Get-ChildItem (Join-Path $sourceRoot 'core') -File -Recurse | Where-Object {
  $_.FullName -notmatch '[\\/](?:\.venv|__pycache__|data|logs)[\\/]' -and
  $_.Name -notmatch '^(?:\.env$|.*\.pyc$|.*\.db(?:-wal|-shm)?$)'
} | ForEach-Object {
  $relative = $_.FullName.Substring($sourceRoot.Length + 1)
  $dst = Join-Path $TargetRoot $relative
  if (Test-Path $dst) {
    $backup = Join-Path $backupRoot $relative
    New-Item -ItemType Directory -Path (Split-Path $backup -Parent) -Force | Out-Null
    Copy-Item $_.FullName $backup -Force
  }
  New-Item -ItemType Directory -Path (Split-Path $dst -Parent) -Force | Out-Null
  Copy-Item $_.FullName $dst -Force
}
Write-Host "v0.2.0 source patch applied to: $TargetRoot" -ForegroundColor Green
Write-Host "Backups (if any): $backupRoot"
Write-Host 'NOTE: Git commit/push and APK build NOT performed. Run git diff and gradlew assembleDebug manually.'
