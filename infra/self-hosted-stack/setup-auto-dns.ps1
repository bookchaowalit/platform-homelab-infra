# Solo Empire - Setup auto DNS sync as Windows scheduled task
# Run ONCE as Administrator. After this, DNS syncs automatically on login.

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

$taskName = "SoloEmpire-DNS-Sync"
# Run this script from the homelab checkout (infra\self-hosted-stack); the WSL path is derived from it.
$stackDir = (wsl.exe wslpath -u "$PSScriptRoot").Trim()
$scriptPath = Join-Path $PSScriptRoot "sync-dns.bat"

# Remove existing task if any
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Create scheduled task: runs on user login only (hidden, no popup)
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -Command `"wsl.exe -e bash -lc 'cd $stackDir && ./sync-dns.sh'`""

$triggerLogin = New-ScheduledTaskTrigger -AtLogOn

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggerLogin -Principal $principal -Settings $settings -Description "Auto-sync Solo Empire *.local domains to Windows hosts file" -Force

Write-Host ""
Write-Host "Scheduled task '$taskName' created!" -ForegroundColor Green
Write-Host "  - Runs silently on Windows login (no popup)" -ForegroundColor Cyan
Write-Host "  - You never need to run anything manually again" -ForegroundColor Cyan
Write-Host ""
Write-Host "Running initial sync now..." -ForegroundColor Yellow

# Run immediately (hidden)
Start-Process powershell -WindowStyle Hidden -Wait -ArgumentList "-Command `"wsl.exe -e bash -lc 'cd $stackDir && ./sync-dns.sh'`""

Write-Host ""
Write-Host "Setup complete! Press Enter to exit."
Read-Host
