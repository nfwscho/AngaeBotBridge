# AngaeBot ADB resolver regression tests - features and protections.
# 1. Load the production Windows PowerShell 5.1-compatible ADB resolver.
# 2. Verify an explicit external adb.exe path is accepted without PATH changes/download.
# 3. Verify Android SDK platform-tools discovery through ANDROID_HOME.
# 4. Verify that Android SDK root is exposed to Gradle only within this process.
# 5. Prevent any network download or phone/Termux interaction during these tests.
# 6. Restore original environment variables and remove temporary test files.
# 7. Test the existing deployment helper only; preserve Core, Android app, logs,
#    SQLite, user settings, GitHub branching and production deployment semantics.

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'resolve-adb.ps1')

$beforeAdb = [Environment]::GetEnvironmentVariable('ANGAE_ADB_PATH', 'Process')
$beforeHome = [Environment]::GetEnvironmentVariable('ANDROID_HOME', 'Process')
$beforeSdk = [Environment]::GetEnvironmentVariable('ANDROID_SDK_ROOT', 'Process')
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('angaebot-adb-test-' + [guid]::NewGuid().ToString('N'))

try {
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    $directAdb = Join-Path $tempRoot 'adb.exe'
    [System.IO.File]::WriteAllText($directAdb, 'ADB stub: not executed')
    $env:ANGAE_ADB_PATH = $directAdb
    $resolved = Resolve-AngaeAdb -ProjectRoot $root -NoDownload
    if ($resolved -ne $directAdb) {
        throw "Explicit ANGAE_ADB_PATH failed: $resolved"
    }

    # The override is removed for the second probe so SDK detection is exercised.
    Remove-Item Env:\ANGAE_ADB_PATH -ErrorAction SilentlyContinue
    $fakeSdk = Join-Path $tempRoot 'custom-sdk'
    $sdkTools = Join-Path $fakeSdk 'platform-tools'
    New-Item -ItemType Directory -Path $sdkTools -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $fakeSdk 'platforms') -Force | Out-Null
    $sdkAdb = Join-Path $sdkTools 'adb.exe'
    [System.IO.File]::WriteAllText($sdkAdb, 'ADB stub: not executed')
    $env:ANDROID_HOME = $fakeSdk
    $env:ANDROID_SDK_ROOT = ''
    $resolved = Resolve-AngaeAdb -ProjectRoot $root -NoDownload
    if ($resolved -ne $sdkAdb) {
        throw "Custom Android SDK discovery failed: $resolved"
    }
    if ($env:ANDROID_HOME -ne $fakeSdk) {
        throw 'Android SDK environment changed unexpectedly.'
    }

    Write-Host 'ADB resolver isolated discovery tests PASSED' -ForegroundColor Green
} finally {
    [Environment]::SetEnvironmentVariable('ANGAE_ADB_PATH', $beforeAdb, 'Process')
    [Environment]::SetEnvironmentVariable('ANDROID_HOME', $beforeHome, 'Process')
    [Environment]::SetEnvironmentVariable('ANDROID_SDK_ROOT', $beforeSdk, 'Process')
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force
    }
}
