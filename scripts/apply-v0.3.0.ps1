# AngaeBot v0.3.0 — Windows 안전 패치 전체 기능 상세 설명
# 1. 기존 Git 프로젝트의 모든 미변경 Kotlin/Python/UI/SQLite/로그/부팅 스크립트를 보존한다.
# 2. Android AI 추가 관련 5개 기존 소스 및 신규 Python AI/테스트/문서만 적용한다.
# 3. 덮어쓸 기존 파일은 프로젝트 밖의 날짜별 독립 백업 폴더에 보관한다.
# 4. 기존 .git, core/.env, core/.venv, data/, logs/, 로컬 APK, Gradle Wrapper를 제외한다.
# 5. 대상 파일이 누락된 경우 오류를 출력하고 필수 프로젝트 경로 검증 후에만 진행한다.
# 6. 원본 ZIP의 AngaeBotBridge 폴더와 Windows D:\stockproj\AngaeBotBridge의 상대 경로를 연결한다.
# 7. 기존 v0.2.1 runit/watchdog 및 v0.2.2 Python 패키지 설치 스크립트는 변경하지 않는다.
# 8. 성공 메시지/백업 경로/반영 파일을 출력하며 git commit/push는 자동으로 수행하지 않는다.
param([string]$TargetRoot = 'D:\stockproj\AngaeBotBridge')
$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not (Test-Path -LiteralPath (Join-Path $TargetRoot 'core\app\main.py') -PathType Leaf)) {
    throw "대상 프로젝트에 core\app\main.py가 없습니다: $TargetRoot"
}
if (-not (Test-Path -LiteralPath (Join-Path $TargetRoot 'app\src\main\java\kr\co\angaebot\bridge\MainActivity.kt') -PathType Leaf)) {
    throw 'Android Bridge 프로젝트가 없습니다.'
}
$files = @(
 'app\build.gradle.kts',
 'app\src\main\java\kr\co\angaebot\bridge\CommandParser.kt',
 'app\src\main\java\kr\co\angaebot\bridge\KakaoNotificationListener.kt',
 'app\src\main\java\kr\co\angaebot\bridge\MainActivity.kt',
 'app\src\main\java\kr\co\angaebot\bridge\PythonBridgeClient.kt',
 'app\src\main\java\kr\co\angaebot\bridge\PythonBridgeConfig.kt',
 'core\app\main.py', 'core\app\commands.py', 'core\app\ai_engine.py',
 'core\scripts\configure-ai.py', 'core\.env.example',
 'core\tests\test_ai.py', 'core\tests\test_ai_api.py', 'core\tests\test_ai_config.py',
 'docs\UPGRADE_v0.3.0.md', 'docs\TEST_PLAN_v0.3.0.md',
 'CHANGELOG_v0.3.0.md', 'scripts\apply-v0.3.0.ps1'
)
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$targetParent = Split-Path -Parent (Resolve-Path $TargetRoot).Path
$backupRoot = Join-Path $targetParent "AngaeBotBridge_backup_v0.3.0_$stamp"
foreach ($relative in $files) {
    $source = Join-Path $sourceRoot $relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "패치 파일이 누락됐습니다: $source" }
}
foreach ($relative in $files) {
    $source = Join-Path $sourceRoot $relative
    $target = Join-Path $TargetRoot $relative
    if (Test-Path -LiteralPath $target -PathType Leaf) {
        $save = Join-Path $backupRoot $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $save) -Force | Out-Null
        Copy-Item -LiteralPath $target -Destination $save -Force
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
    Write-Host "[APPLY] $relative"
}
Write-Host "[OK] AngaeBot v0.3.0 patch applied. Backup: $backupRoot"
Write-Host '기존 .env / SQLite / runit / 로그 / Git 내역은 수정하지 않았습니다.'
Write-Host '다음: git diff --stat; .\gradlew.bat :app:assembleDebug'
