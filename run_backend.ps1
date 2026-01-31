$env:PYTHONPATH = Join-Path $PSScriptRoot "src"
$venvPath = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "Activating venv..."
    & $venvPath
} else {
    Write-Host "Warning: .venv not found at $venvPath"
}

Write-Host "Starting Backend Server with PYTHONPATH=$env:PYTHONPATH"
uvicorn api.server:app --reload
