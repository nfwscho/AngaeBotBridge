#requires -version 5.1
<#
AngaeBot v0.4.0 Windows PowerShell 배포 프로그램 — 전체 기능 상세 설명
1. 기존 Windows Git 저장소 및 GitHub 소스 파일을 읽고 S20+로 Python 소스 4개와 배포기만 전송한다.
2. 기존 Android UI/Kakao/DB/인증키/로그, runit/SSH/부팅 서비스 설정을 변경하지 않는다.
3. 모든 소스 파일 존재 여부를 먼저 확인하고 필수 파일이 없으면 서버 변경 전 실패한다.
4. 기존 SSH TCP 8022 경로로 디렉터리를 생성하고 SCP 파일 전송 결과를 점검한다.
5. S20+ Termux의 별도 apply-v0.4.0.sh에 소스 백업·테스트·서버 재시작을 위임한다.
6. 실패 시 원격 스크립트가 기존 소스를 복원하도록 구성하고 종료 코드를 반환한다.
7. Android APK 빌드/설치는 별도 단계이며 이 배포기에서는 기존 앱을 제거하지 않는다.
8. OpenAI API·Ollama 호출·API 키 입력·비밀정보 전송 기능이 없다.
9. 성공 시 Git 커밋을 생성하거나 푸시하지 않고 기존 로그와 진행 상태만 출력한다.
10. 사용자 지정 Host/Port를 지원하며 기본 접속은 Galaxy S20+ 로컬 SSH다.
#>
[CmdletBinding()]
param(
    [string]$Target = 'u0_a435@10.1.1.202',
    [int]$SshPort = 8022
)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$files = @(
    (Join-Path $root 'core\app\main.py'),
    (Join-Path $root 'core\app\commands.py'),
    (Join-Path $root 'core\app\ops.py'),
    (Join-Path $root 'core\tests\test_ops.py'),
    (Join-Path $root 'core\scripts\apply-v0.4.0.sh')
)
foreach ($file in $files) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "배포 파일 없음: $file (먼저 git pull origin main 수행)"
    }
}
Write-Host "[INFO] 대상: $Target / SSH: $SshPort"
& ssh -p $SshPort $Target 'mkdir -p ~/angaebot/update_v040'
if ($LASTEXITCODE -ne 0) { throw 'S20+ 업데이트 폴더 생성 실패' }
& scp -P $SshPort @files "${Target}:~/angaebot/update_v040/"
if ($LASTEXITCODE -ne 0) { throw 'S20+ Python 소스 전송 실패' }
& ssh -p $SshPort $Target 'bash ~/angaebot/update_v040/apply-v0.4.0.sh'
if ($LASTEXITCODE -ne 0) { throw "Termux v0.4.0 반영 실패 (SSH exit=$LASTEXITCODE); 로그와 백업 확인 필요" }
Write-Host '[OK] Python Core v0.4.0 배포 완료. Android APK는 별도로 빌드/설치하세요.' -ForegroundColor Green
