# SilentChair local dev launcher
# Usage:  .\dev.ps1
# Stop:   .\dev.ps1 -Stop

param([switch]$Stop)

$root        = $PSScriptRoot
$backendDir  = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$uvicorn     = Join-Path $backendDir ".venv\Scripts\uvicorn.exe"
$lockFile    = Join-Path $root ".dev-pids.json"

# ── Stop mode ─────────────────────────────────────────────────────────────────
if ($Stop) {
    if (Test-Path $lockFile) {
        $ids = Get-Content $lockFile | ConvertFrom-Json
        foreach ($id in $ids) {
            Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
        }
        Remove-Item $lockFile -Force
        Write-Host "Stopped all dev processes." -ForegroundColor Cyan
    } else {
        Write-Host "No running dev processes found." -ForegroundColor Yellow
    }
    exit 0
}

# ── Preflight ─────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "  SilentChair -- starting local dev" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $uvicorn)) {
    Write-Host "  ERROR: backend\.venv not found." -ForegroundColor Red
    Write-Host "  Run inside backend\:" -ForegroundColor Yellow
    Write-Host "    python -m venv .venv" -ForegroundColor Yellow
    Write-Host "    .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "  node_modules missing -- running npm install..." -ForegroundColor Yellow
    Push-Location $frontendDir
    npm install
    Pop-Location
}

# ── Launch each service in its own PowerShell window ─────────────────────────
$backendCmd  = "Set-Location '$backendDir'; & '$uvicorn' app.main:app --host 0.0.0.0 --port 8000 --reload"
$frontendCmd = "Set-Location '$frontendDir'; npm run dev"

$backend  = Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd  -PassThru
$frontend = Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -PassThru

@($backend.Id, $frontend.Id) | ConvertTo-Json | Set-Content $lockFile

Write-Host "  Services started in separate windows." -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend  ->  http://localhost:3000" -ForegroundColor White
Write-Host "  Backend   ->  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "  To stop all:  .\dev.ps1 -Stop" -ForegroundColor DarkGray
Write-Host ""
