# AngaeBot Windows ADB resolver - preserved deployment behaviors and safety guarantees.
# 1. Used only by -InstallAndroid; Python Core-only deployment stays unchanged.
# 2. Prefer explicit ANGAE_ADB_PATH, Android SDK paths, then PATH adb.exe.
# 3. Recognize ANDROID_HOME, ANDROID_SDK_ROOT, standard Android Studio SDK locations,
#    and a previously downloaded AngaeBot-managed local platform-tools copy.
# 4. Never modify system PATH, uninstall software, alter phone app data, or touch Termux.
# 5. If no ADB exists, ask for Android SDK license acceptance before any download.
# 6. Fetch only official Google platform-tools r37.0.1 over HTTPS, pin its SHA-256,
#    reject altered archives, then extract to a local user cache (not the Git repo).
# 7. Keep downloaded files inside the current user's LocalAppData; clean temporary files.
# 8. Give a clear diagnostic if no tool is available, download fails, or license is declined.
# 9. -NoDownload enables isolated automated tests without network/device access.
# 10. Return the full adb.exe path for safe invocation with the PowerShell call operator.
# 11. Preserve existing GitHub CI checks, Android Gradle build, SSH deployment,
#     RemoteInput, logging, SQLite data, permissions and rollback behavior.
# 12. Add Android SDK environment discovery for Gradle only within this process.

function Resolve-AngaeAdb {
    [CmdletBinding()]
    param(
        [string]$ProjectRoot = '',
        [switch]$NoDownload
    )

    $localData = $env:LOCALAPPDATA
    if ([string]::IsNullOrWhiteSpace($localData)) {
        if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
            throw 'LOCALAPPDATA and USERPROFILE are unavailable; cannot locate the Android SDK.'
        }
        $localData = Join-Path $env:USERPROFILE 'AppData\Local'
    }

    $cacheRoot = Join-Path $localData 'AngaeBotBridge\tools\platform-tools-r37.0.1'
    $cachedAdb = Join-Path $cacheRoot 'platform-tools\adb.exe'
    $candidates = New-Object 'System.Collections.Generic.List[string]'
    if (-not [string]::IsNullOrWhiteSpace($env:ANGAE_ADB_PATH)) {
        $candidates.Add($env:ANGAE_ADB_PATH)
    }

    $sdkRoots = @(
        $env:ANDROID_SDK_ROOT,
        $env:ANDROID_HOME,
        (Join-Path $localData 'Android\Sdk'),
        (Join-Path $localData 'Android\sdk')
    )
    if (-not [string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
        $sdkRoots += (Join-Path $env:USERPROFILE 'AppData\Local\Android\Sdk')
    }
    if (-not [string]::IsNullOrWhiteSpace($env:ProgramFiles)) {
        $sdkRoots += (Join-Path $env:ProgramFiles 'Android\Sdk')
    }
    if (-not [string]::IsNullOrWhiteSpace(${env:ProgramFiles(x86)})) {
        $sdkRoots += (Join-Path ${env:ProgramFiles(x86)} 'Android\android-sdk')
    }

    foreach ($sdkRoot in $sdkRoots) {
        if (-not [string]::IsNullOrWhiteSpace($sdkRoot)) {
            $candidates.Add((Join-Path $sdkRoot 'platform-tools\adb.exe'))
        }
    }
    $candidates.Add($cachedAdb)
    $onPath = Get-Command 'adb.exe' -ErrorAction SilentlyContinue
    if ($null -ne $onPath -and $onPath.CommandType -eq 'Application') {
        $candidates.Add($onPath.Source)
    }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $resolved = (Resolve-Path -LiteralPath $candidate).Path
            # Only set the SDK root automatically when the selected path really lives
            # under an Android SDK platform-tools directory. Do not override user config.
            if ([string]::IsNullOrWhiteSpace($env:ANDROID_HOME)) {
                $parent = Split-Path -Path $resolved -Parent
                if ((Split-Path -Path $parent -Leaf) -ieq 'platform-tools') {
                    $sdkParent = Split-Path -Path $parent -Parent
                    if (Test-Path -LiteralPath (Join-Path $sdkParent 'platforms') -PathType Container) {
                        $env:ANDROID_HOME = $sdkParent
                    }
                }
            }
            Write-Host "  ADB resolved: $resolved" -ForegroundColor Green
            return $resolved
        }
    }

    if ($NoDownload) {
        throw 'ADB could not be found in configured Android SDK locations or on PATH.'
    }

    # Official Android SDK Platform-Tools download and fixed SHA-256 for r37.0.1.
    # Obtain only when no existing ADB is available; license approval is required.
    $licenseUrl = 'https://developer.android.com/tools/releases/platform-tools'
    Write-Host "Android SDK Platform-Tools not found. Review Google terms: $licenseUrl" -ForegroundColor Yellow
    $consent = Read-Host 'To download Google Android SDK Platform-Tools, type YES to accept the SDK license'
    if ($consent -cne 'YES') {
        throw 'Android SDK license not accepted. No download or deployment was attempted.'
    }

    $url = 'https://dl.google.com/android/repository/platform-tools_r37.0.1-win.zip'
    $expectedSha = '45f4d63113e895ebde0c90f194099a4676b6ac653bd28d54314a9e022bbc1a99'
    $scratch = Join-Path ([System.IO.Path]::GetTempPath()) ('angaebot-adb-' + [guid]::NewGuid().ToString('N'))
    $zip = Join-Path $scratch 'platform-tools.zip'
    $unpacked = Join-Path $scratch 'extracted'
    try {
        New-Item -ItemType Directory -Path $scratch -Force | Out-Null
        Write-Host '  Downloading verified Google platform-tools ...' -ForegroundColor Cyan
        if ([Net.ServicePointManager]::SecurityProtocol -band [Net.SecurityProtocolType]::Tls12) {
            # TLS 1.2 is already enabled.
        } else {
            [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        }
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing -TimeoutSec 120 -ErrorAction Stop
        $actualSha = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualSha -ne $expectedSha) {
            throw "Google platform-tools checksum mismatch; aborting. Expected $expectedSha; actual $actualSha"
        }
        Expand-Archive -LiteralPath $zip -DestinationPath $unpacked -Force
        $sourceDir = Join-Path $unpacked 'platform-tools'
        if (-not (Test-Path -LiteralPath (Join-Path $sourceDir 'adb.exe') -PathType Leaf)) {
            throw 'Verified archive did not contain platform-tools/adb.exe.'
        }
        New-Item -ItemType Directory -Path $cacheRoot -Force | Out-Null
        $targetDir = Join-Path $cacheRoot 'platform-tools'
        if (-not (Test-Path -LiteralPath (Join-Path $targetDir 'adb.exe') -PathType Leaf)) {
            # The target is AngaeBot's own per-user versioned cache directory.
            if (Test-Path -LiteralPath $targetDir) {
                throw 'Existing incomplete AngaeBot ADB cache; inspect before replacing files.'
            }
            Move-Item -LiteralPath $sourceDir -Destination $targetDir
        }
        if (-not (Test-Path -LiteralPath $cachedAdb -PathType Leaf)) {
            throw 'Android Platform-Tools extraction failed.'
        }
        Write-Host "  Verified ADB installed in user cache: $cachedAdb" -ForegroundColor Green
        return $cachedAdb
    } finally {
        if (Test-Path -LiteralPath $scratch) {
            Remove-Item -LiteralPath $scratch -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}
