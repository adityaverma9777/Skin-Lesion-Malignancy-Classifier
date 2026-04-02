$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend"

if (-not (Test-Path $backendPath)) {
	throw "Backend folder not found at: $backendPath"
}

if (-not (Test-Path $frontendPath)) {
	throw "Frontend folder not found at: $frontendPath"
}

if (Get-Command python -ErrorAction SilentlyContinue) {
	$pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
	$pythonCmd = "py -3"
} else {
	throw "Python was not found. Install Python 3 and try again."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
	throw "npm was not found. Install Node.js (which includes npm) and try again."
}

$backendCmd = "$pythonCmd -m pip install -r requirements.txt; $pythonCmd -m uvicorn app:app --host 127.0.0.1 --port 8000"
$frontendCmd = "npm install; npm run dev"

Start-Process powershell -WorkingDirectory $backendPath -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCmd
Start-Process powershell -WorkingDirectory $frontendPath -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCmd

Write-Host "Project root: $projectRoot"
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "If frontend picks another port, use that URL from terminal output."
