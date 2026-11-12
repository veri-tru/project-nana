param(
    [switch]$Setup,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$EngineArgs
)

$ErrorActionPreference = 'Stop'
$enginePython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
Push-Location -LiteralPath $PSScriptRoot
try {
    if ($Setup) {
        if (-not (Test-Path -LiteralPath $enginePython)) {
            & python -c "import sys; assert sys.version_info[:2] == (3, 12), 'Python 3.12 is required'"
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
            & python -m venv .venv
            if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        }
        & $enginePython -m pip install -r tools/dog_engine/verification-lock.txt
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & $enginePython -m pip check
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & $enginePython -m tools.dog_engine doctor
        exit $LASTEXITCODE
    }
    if (-not (Test-Path -LiteralPath $enginePython)) {
        throw 'Project environment missing. Run .\engine.ps1 -Setup first (Python 3.12).'
    }
    if (-not $EngineArgs) { $EngineArgs = @('status') }
    & $enginePython -m tools.dog_engine @EngineArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
