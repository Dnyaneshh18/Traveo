<#
.SYNOPSIS
    Traveo Windows 1-Click Setup Script
    Downloads the latest full Traveo codebase directly into C:\TRAVEO
#>

$ErrorActionPreference = "Stop"
$TargetDir = "C:\TRAVEO"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   TRAVEO — 1-CLICK WINDOWS SETUP SCRIPT" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path $TargetDir)) {
    Write-Host "[+] Creating target directory: $TargetDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
}

Set-Location $TargetDir

# Check if git is installed
$hasGit = Get-Command git -ErrorAction SilentlyContinue

if ($hasGit) {
    Write-Host "[+] Git detected. Syncing latest repository from GitHub..." -ForegroundColor Green
    if (Test-Path "$TargetDir\.git") {
        git fetch origin main
        git reset --hard origin/main
        git clean -fd
    } else {
        git clone -b main https://github.com/Dnyaneshh18/Traveo.git $TargetDir
    }
} else {
    Write-Host "[+] Git not detected. Downloading complete zip archive..." -ForegroundColor Yellow
    $zipUrl = "https://github.com/Dnyaneshh18/Traveo/archive/refs/heads/main.zip"
    $zipFile = Join-Path $env:TEMP "traveo-latest.zip"
    
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile -UseBasicParsing
    Write-Host "[+] Extracting archive into $TargetDir..." -ForegroundColor Green
    
    $tempExtract = Join-Path $env:TEMP "traveo-extract"
    if (Test-Path $tempExtract) { Remove-Item -Recurse -Force $tempExtract }
    Expand-Archive -Path $zipFile -DestinationPath $tempExtract -Force
    
    $extractedFolder = Join-Path $tempExtract "Traveo-main"
    Copy-Item -Path "$extractedFolder\*" -Destination $TargetDir -Recurse -Force
    
    Remove-Item -Force $zipFile
    Remove-Item -Recurse -Force $tempExtract
}

Write-Host "`n[+] Installing Node.js workspaces dependencies..." -ForegroundColor Green
cmd.exe /c "npm install"

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "SUCCESS! All latest code is updated in C:\TRAVEO" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "`nTo start the application on Windows:" -ForegroundColor Yellow
Write-Host "  Terminal 1 (Backend API):" -ForegroundColor White
Write-Host "    cd C:\TRAVEO\backend"
Write-Host "    python -m venv .venv"
Write-Host "    .venv\Scripts\activate"
Write-Host "    pip install -e ."
Write-Host "    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
Write-Host "`n  Terminal 2 (Passenger Web App):" -ForegroundColor White
Write-Host "    cd C:\TRAVEO"
Write-Host "    npm.cmd run passenger:web"
Write-Host "`n  Terminal 3 (Driver Web App):" -ForegroundColor White
Write-Host "    cd C:\TRAVEO"
Write-Host "    npm.cmd run driver:web"
Write-Host "`n  Terminal 4 (Admin Panel):" -ForegroundColor White
Write-Host "    cd C:\TRAVEO"
Write-Host "    npm.cmd run admin"
