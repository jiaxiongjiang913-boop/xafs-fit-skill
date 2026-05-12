# xafs-fit-skill -- Self-bootstrapping PowerShell wrapper
# Creates venv, installs deps on first run.

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ScriptArgs
)

$SkillDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $SkillDir ".venv"

if (-not (Test-Path $VenvDir)) {
    Write-Host "[xafs-fit-skill] Bootstrapping..." -ForegroundColor Blue
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        Write-Host "[xafs-fit-skill] ERROR: python not found. Install Python >= 3.9." -ForegroundColor Red
        exit 1
    }
    & python -m venv $VenvDir
    $pipScript = Join-Path $VenvDir "Scripts" "pip.exe"
    & $pipScript install --quiet -r "$SkillDir\requirements.txt"
    Write-Host "[xafs-fit-skill] Bootstrap complete." -ForegroundColor Green
}

$pythonExe = Join-Path $VenvDir "Scripts" "python.exe"
& $pythonExe $ScriptArgs
