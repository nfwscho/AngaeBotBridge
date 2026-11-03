# 앙개봇 Android Bridge v0.1 - 공식 Gradle Wrapper JAR 수신 및 무결성 검증.
# 공식 배포 서버만 사용, SHA-256 불일치 시 삭제, Android SDK/코드 변조 없음.
$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$JarPath = Join-Path $ProjectRoot 'gradle\wrapper\gradle-wrapper.jar'
$ExpectedSha256 = '7d3a4ac4de1c32b59bc6a4eb8ecb8e612ccd0cf1ae1e99f66902da64df296172'
$Url = 'https://services.gradle.org/distributions/gradle-8.14.3-wrapper.jar'

if (Test-Path $JarPath) {
    $ExistingHash = (Get-FileHash -Algorithm SHA256 -Path $JarPath).Hash.ToLowerInvariant()
    if ($ExistingHash -eq $ExpectedSha256) {
        Write-Host 'Official Gradle Wrapper already present and verified.' -ForegroundColor Green
        exit 0
    }
    throw "Existing wrapper has unexpected SHA-256: $ExistingHash. Delete only after verifying its source."
}

Write-Host "Downloading official Gradle 8.14.3 wrapper: $Url"
try {
    Invoke-WebRequest -Uri $Url -OutFile $JarPath -UseBasicParsing
    $Actual = (Get-FileHash -Algorithm SHA256 -Path $JarPath).Hash.ToLowerInvariant()
    if ($Actual -ne $ExpectedSha256) {
        Remove-Item -Path $JarPath -Force
        throw "Checksum mismatch. Actual=$Actual Expected=$ExpectedSha256"
    }
    Write-Host 'Wrapper checksum verified.' -ForegroundColor Green
} catch {
    if (Test-Path $JarPath) { Remove-Item -Path $JarPath -Force }
    throw
}
