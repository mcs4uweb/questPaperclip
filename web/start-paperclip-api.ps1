# Start the Quest Paperclip FastAPI process on 8001.
# Note: uvicorn must run from the repo root (parent of this folder),
# where main.py lives — not from web/.

$RepoRoot = Split-Path -Parent $PSScriptRoot
if (-not $RepoRoot) {
    $RepoRoot = "C:\Projects\paperclip-app"
}

Set-Location $RepoRoot
Write-Host "Working directory: $(Get-Location)"
Write-Host "Starting: python -m uvicorn main:app --host 127.0.0.1 --port 8001"

if (-not (Test-Path (Join-Path $RepoRoot "main.py"))) {
    Write-Error "main.py not found in $RepoRoot"
    exit 1
}

python -m uvicorn main:app --host 127.0.0.1 --port 8001
