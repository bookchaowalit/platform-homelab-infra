@echo off
:: Solo Empire - DNS Sync (run from Windows)
:: Double-click this file or run from Admin PowerShell to sync all *.local domains
:: Requires: WSL2 running; run from the homelab checkout (path is derived from this file)

:: Check for admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo Syncing Solo Empire DNS...
wsl -e bash -lc "cd \"$(wslpath -u '%~dp0')\" && ./sync-dns.sh"
echo.
echo Done! Press any key to exit.
pause >nul
