$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$backendCmd = "Set-Location '$projectRoot\backend'; pip install -r requirements.txt; uvicorn app:app --host 127.0.0.1 --port 8000"
$frontendCmd = "Set-Location '$projectRoot\frontend'; npm install; npm run dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "If frontend picks another port, use that URL from terminal output."
