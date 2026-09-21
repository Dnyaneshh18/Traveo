import os
import base64
import json

ROOT = "/home/user/Traveo"
IGNORED_DIRS = {
    ".git", ".venv", ".venv-traveo", "node_modules", ".expo", 
    "dist", "build", "__pycache__", ".turbo", "metro-cache"
}
IGNORED_EXTS = {".pyc", ".db", ".sqlite", ".log"}

files_data = []

for root, dirs, files in os.walk(ROOT):
    # filter directories in place
    dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".arena")]
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in IGNORED_EXTS or f.endswith(".db"):
            continue
        full_path = os.path.join(root, f)
        rel_path = os.path.relpath(full_path, ROOT).replace("\\", "/")
        try:
            with open(full_path, "rb") as fp:
                content_bytes = fp.read()
            b64 = base64.b64encode(content_bytes).decode("ascii")
            files_data.append({"p": rel_path, "d": b64})
        except Exception as e:
            print(f"Skipping {rel_path}: {e}")

print(f"Total files packed: {len(files_data)}")

# Generate PowerShell script
ps_path = "/home/user/Traveo/write-portal.ps1"
with open(ps_path, "w", encoding="utf-8") as out:
    out.write('''<#
.SYNOPSIS
    Self-contained Traveo Project Extraction Script
    Writes all latest files directly to C:\\TRAVEO
#>

$TargetDir = "C:\\TRAVEO"
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   WRITING TRAVEO FILES TO $TargetDir..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$files = @(
''')
    for item in files_data:
        # write each file as a PowerShell object
        out.write(f'  [PSCustomObject]@{{ Path = "{item["p"]}"; Data = "{item["d"]}" }}\n')
    
    out.write('''
)

$count = 0
foreach ($f in $files) {
    $dest = Join-Path $TargetDir $f.Path
    $parent = Split-Path -Parent $dest
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $bytes = [System.Convert]::FromBase64String($f.Data)
    [System.IO.File]::WriteAllBytes($dest, $bytes)
    $count++
    if ($count % 20 -eq 0) {
        Write-Host "  Written $count / $($files.Count) files..." -ForegroundColor Gray
    }
}

Write-Host "`n[+] Successfully wrote all $($files.Count) files to $TargetDir!" -ForegroundColor Green
Write-Host "`nNext steps on your Windows PC:" -ForegroundColor Yellow
Write-Host "  1. npm.cmd install" -ForegroundColor White
Write-Host "  2. Backend: cd backend && python -m venv .venv && .venv\\Scripts\\activate && pip install -e . && uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "  3. Passenger: npm.cmd run passenger:web" -ForegroundColor White
Write-Host "  4. Driver: npm.cmd run driver:web" -ForegroundColor White
Write-Host "  5. Admin: npm.cmd run admin" -ForegroundColor White
''')

print(f"Created {ps_path} size: {os.path.getsize(ps_path)} bytes")
