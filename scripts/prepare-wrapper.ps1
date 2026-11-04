# 앙개봇 Android Bridge v0.1.2 - Gradle Wrapper 다운로드 오류 복구 스크립트
# 프로젝트 전체 기능: S20+ 카카오톡 알림 수신(NotificationListenerService), 채팅방 및
# 발신자 허용목록 검증, '앙개야' 호출어 검사, 로컬 명령(테스트/상태/도움말) 실행,
# RemoteInput 빠른 답장 요청, SQLite 중복 방지/수신 및 오류 로그 저장,
# Android 관리 UI(설정/ON-OFF/로그 조회/내보내기/삭제) 기능을 제공한다.
# 이 스크립트는 앱 소스, UI, 설정 및 로그를 변경하지 않고 Gradle Wrapper 실행에
# 필요한 공식 gradle-wrapper.jar만 준비한다.
# 수행 기능:
# 1) 기존 Wrapper JAR의 SHA-256 검증 및 정상이면 재다운로드 생략.
# 2) Gradle 공식 다운로드 서버 시도. 실패하면 공식 Gradle GitHub 태그를 이용.
# 3) 모든 다운로드를 임시 파일로 받아 SHA-256 검증 후에만 최종 경로에 저장.
# 4) 실패한 URL/오류를 콘솔에 남기고 임시 파일 삭제. 검증 실패한 JAR는 사용 금지.
# 5) 모든 소스 실패 시 오류 종료, Android 프로젝트 소스/Gradle 버전 유지.
$ErrorActionPreference = 'Stop'

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$JarPath = Join-Path $ProjectRoot 'gradle\wrapper\gradle-wrapper.jar'
$TempPath = "$JarPath.download"
$ExpectedSha256 = '7d3a4ac4de1c32b59bc6a4eb8ecb8e612ccd0cf1ae1e99f66902da64df296172'
$Urls = @(
    'https://downloads.gradle.org/distributions/gradle-8.14.3-wrapper.jar',
    'https://raw.githubusercontent.com/gradle/gradle/v8.14.3/gradle/wrapper/gradle-wrapper.jar'
)

if (Test-Path -LiteralPath $JarPath) {
    $ExistingHash = (Get-FileHash -LiteralPath $JarPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ExistingHash -eq $ExpectedSha256) {
        Write-Host 'Gradle Wrapper 8.14.3 already present; SHA-256 OK.' -ForegroundColor Green
        exit 0
    }
    throw "Existing gradle-wrapper.jar has an unknown SHA-256 ($ExistingHash). Inspect it before replacing. Expected: $ExpectedSha256"
}

$Errors = New-Object 'System.Collections.Generic.List[string]'
foreach ($Url in $Urls) {
    try {
        if (Test-Path -LiteralPath $TempPath) {
            Remove-Item -LiteralPath $TempPath -Force
        }
        Write-Host "Trying official Gradle Wrapper 8.14.3 source: $Url"
        Invoke-WebRequest -Uri $Url -OutFile $TempPath -UseBasicParsing -ErrorAction Stop
        $ActualSha256 = (Get-FileHash -LiteralPath $TempPath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($ActualSha256 -ne $ExpectedSha256) {
            $Message = "SHA-256 mismatch at $Url : actual=$ActualSha256 expected=$ExpectedSha256"
            Write-Warning $Message
            $Errors.Add($Message)
            continue
        }
        Move-Item -LiteralPath $TempPath -Destination $JarPath -ErrorAction Stop
        Write-Host 'Gradle Wrapper 8.14.3 download complete; SHA-256 verified.' -ForegroundColor Green
        Write-Host "Saved to: $JarPath"
        exit 0
    }
    catch {
        $Message = "Download failed at $Url : $($_.Exception.Message)"
        Write-Warning $Message
        $Errors.Add($Message)
    }
    finally {
        if (Test-Path -LiteralPath $TempPath) {
            Remove-Item -LiteralPath $TempPath -Force -ErrorAction SilentlyContinue
        }
    }
}

$Summary = $Errors -join [Environment]::NewLine
throw "Could not obtain a verified Gradle Wrapper 8.14.3 JAR from either official source. Details:`n$Summary"
