# ============================================
# Quest Paperclip auto-start (FastAPI / uvicorn)
# ============================================

$AppDir = "C:\Projects\paperclip-app"
$Port = 8001
$HostAddr = "127.0.0.1"
$LogDir = "C:\Projects\logs"
$LogFile = Join-Path $LogDir ("paperclip-{0}.log" -f (Get-Date -Format "yyyy-MM-dd"))

function Write-Log {
    param([string]$Message)
    $line = "{0} - {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }
    Add-Content -Path $LogFile -Value $line
    Write-Host $line
}

Write-Log "===== Paperclip auto-start ====="

if (-not (Test-Path (Join-Path $AppDir "main.py"))) {
    Write-Log "ERROR: main.py not found in $AppDir"
    exit 1
}

$already = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($already) {
    Write-Log "Port $Port is already listening. Leaving existing process running."
    exit 0
}

$python = $null
$venvPython = Join-Path $AppDir ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source }
}

if (-not $python) {
    Write-Log "ERROR: Python not found. Install Python or create $venvPython"
    exit 1
}

Write-Log "Using $python"
Set-Location $AppDir

$args = @(
    "-m", "uvicorn", "main:app",
    "--host", $HostAddr,
    "--port", "$Port"
)

Write-Log "Starting: $python $($args -join ' ')"
Start-Process -FilePath $python -ArgumentList $args -WorkingDirectory $AppDir -WindowStyle Hidden
Start-Sleep -Seconds 2

$up = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($up) {
    Write-Log "Paperclip is listening on http://${HostAddr}:${Port}/"
    exit 0
}

Write-Log "WARNING: process started but port $Port is not listening yet. Check $LogFile"
exit 0
