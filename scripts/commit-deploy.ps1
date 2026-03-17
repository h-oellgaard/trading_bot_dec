# Commit and deploy Firestore rules + indexes
# Usage: .\scripts\commit-deploy.ps1 ["commit message"]
#        .\scripts\commit-deploy.ps1  (prompts for message)

param(
    [Parameter(Position = 0)]
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path "$root\.git")) {
    $root = (Get-Location).Path
}
Set-Location $root

# Commit
if ($Message -eq "") {
    $Message = Read-Host "Commit message"
}
if ($Message -ne "") {
    Write-Host "`n=== Staging changes ===" -ForegroundColor Cyan
    git add -A
    git status
    Write-Host "`n=== Committing ===" -ForegroundColor Cyan
    git commit -m "$Message"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n=== Pushing to remote (triggers Render deploy) ===" -ForegroundColor Cyan
        git push
    } else {
        Write-Host "Nothing to commit or commit failed." -ForegroundColor Yellow
    }
}

# Deploy Firestore
Write-Host "`n=== Deploying Firestore (rules + indexes) ===" -ForegroundColor Cyan
firebase deploy --only firestore
if ($LASTEXITCODE -ne 0) {
    Write-Host "Deploy failed. Run 'firebase login' if needed." -ForegroundColor Red
    exit 1
}

Write-Host "`nDone." -ForegroundColor Green
