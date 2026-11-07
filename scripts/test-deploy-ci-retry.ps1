# AngaeBot GitHub Actions API retry safety tests (PowerShell 5.1 and 7).
# 1. Load only the retry classifier function from deploy-angaebot.ps1 without running deployment.
# 2. Verify transient 408/429/500/502/503/504 HTTP responses are retried.
# 3. Verify permanent 400/401/403/404 errors are not hidden or retried.
# 4. Verify network timeout is transient.
# 5. Preserve all existing SSH, S20+, ADB, .env, rollback and logging paths without side effects.
# 6. Never contact GitHub or execute a real deployment during these isolated tests.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$deployScript = Join-Path $projectRoot 'deploy-angaebot.ps1'
if (-not (Test-Path -LiteralPath $deployScript -PathType Leaf)) { throw 'Missing deploy-angaebot.ps1' }

$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    $deployScript, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count -ne 0) { throw 'Deploy script has parse errors' }
$functionNode = $ast.Find({
    param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Test-TransientGithubApiFailure'
}, $true)
if ($null -eq $functionNode) { throw 'Missing GitHub API error classifier' }
. ([scriptblock]::Create($functionNode.Extent.Text))

function Assert-Classified([int]$StatusCode, [bool]$Expected) {
    $ex = New-Object System.Exception('Synthetic HTTP status')
    $response = New-Object psobject -Property @{ StatusCode = $StatusCode }
    $ex | Add-Member -MemberType NoteProperty -Name Response -Value $response
    $record = New-Object System.Management.Automation.ErrorRecord(
        $ex, 'test-http', [System.Management.Automation.ErrorCategory]::ConnectionError, $null)
    $actual = Test-TransientGithubApiFailure $record
    if ($actual -ne $Expected) {
        throw "HTTP status $StatusCode classified as $actual, expected $Expected"
    }
}

foreach ($status in @(408, 429, 500, 502, 503, 504)) { Assert-Classified $status $true }
foreach ($status in @(400, 401, 403, 404)) { Assert-Classified $status $false }
$timeout = New-Object System.Net.WebException(
    'Synthetic timeout', [System.Net.WebExceptionStatus]::Timeout)
$timeoutRecord = New-Object System.Management.Automation.ErrorRecord(
    $timeout, 'test-timeout', [System.Management.Automation.ErrorCategory]::OperationTimeout, $null)
if (-not (Test-TransientGithubApiFailure $timeoutRecord)) {
    throw 'Transient network timeout must be retried'
}
Write-Host 'GitHub CI API retry classification tests PASSED' -ForegroundColor Green
