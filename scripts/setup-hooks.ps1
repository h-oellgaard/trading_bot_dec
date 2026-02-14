# Setup git hooks to run tests before push
# Run: .\scripts\setup-hooks.ps1

git config core.hooksPath .githooks
Write-Host "Git hooks configured. Tests will run before each push." -ForegroundColor Green
