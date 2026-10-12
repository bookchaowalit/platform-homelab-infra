# Solo Empire - Dynamic DNS Setup for Windows
# This script adds all *.local domains to Windows hosts file
# Run as Administrator!

param([switch]$Remove)

# Check for admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Restarting as Administrator..." -ForegroundColor Yellow
    $argList = "-ExecutionPolicy Bypass -File `"$PSCommandPath`""
    if ($Remove) { $argList += " -Remove" }
    Start-Process powershell -Verb RunAs -ArgumentList $argList
    exit
}

$hostsFile = "$env:SystemRoot\System32\drivers\etc\hosts"
$marker = "# Solo Empire Services"

# Get WSL2 IP (first IP only)
$allIPs = bash -c "hostname -I 2>/dev/null"
$wslIP = ($allIPs -split '\s+')[0].Trim()
if (-not $wslIP) {
    # Fallback: try to get IP from WSL
    $wslIP = (bash -c "ip addr show eth0 2>/dev/null | grep 'inet ' | awk '{print `$2}' | cut -d/ -f1").Trim()
}
if (-not $wslIP) {
    Write-Error "Could not get WSL2 IP. Is WSL running?"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "WSL2 IP: $wslIP" -ForegroundColor Cyan

# Auto-detect WSL distro path
$wslDistros = bash -c "wsl.exe -l -q 2>/dev/null" 
if (-not $wslDistros) {
    $wslDistros = wsl.exe -l -q 2>$null
}
$distroName = ($wslDistros | Where-Object { $_ -match 'ubuntu' } | Select-Object -First 1).Trim()
if (-not $distroName) {
    $distroName = "Ubuntu"
}

$composePath = "\\wsl$\$distroName\home\bookchaowalit\book\solo-empire\infra\self-hosted-stack\docker-compose.yml"

if (-not (Test-Path $composePath)) {
    Write-Error "Cannot find docker-compose.yml at: $composePath"
    Write-Host "Trying alternate path..." -ForegroundColor Yellow
    # Try without distro name (WSL2 newer format)
    $composePath = "\\wsl.localhost\$distroName\home\bookchaowalit\book\solo-empire\infra\self-hosted-stack\docker-compose.yml"
    if (-not (Test-Path $composePath)) {
        Write-Error "Cannot find docker-compose.yml. Tried:"
        Write-Error "  \\wsl$\$distroName\..."
        Write-Error "  \\wsl.localhost\$distroName\..."
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "Reading: $composePath" -ForegroundColor Cyan

# Read file content and extract domains using regex
$content = Get-Content $composePath -Raw
$domains = [regex]::Matches($content, 'Host\(``([^`]+)``\)') | 
    ForEach-Object { $_.Groups[1].Value } | 
    Sort-Object -Unique

if ($domains.Count -eq 0) {
    # Try alternate pattern (single backtick in file)
    $domains = [regex]::Matches($content, 'Host\(`([^`]+)`\)') | 
        ForEach-Object { $_.Groups[1].Value } | 
        Sort-Object -Unique
}

Write-Host "Found $($domains.Count) service domains" -ForegroundColor Cyan

if ($domains.Count -eq 0) {
    Write-Error "No domains found. Check docker-compose.yml format."
    Read-Host "Press Enter to exit"
    exit 1
}

if ($Remove) {
    # Remove existing entries
    $hostsContent = Get-Content $hostsFile
    $newContent = @()
    $skip = $false
    foreach ($line in $hostsContent) {
        if ($line -eq $marker) { $skip = $true; continue }
        if ($skip -and $line -match "^\d+\.\d+\.\d+\.\d+.*\.local") { continue }
        if ($skip -and $line -eq "") { $skip = $false; continue }
        $newContent += $line
    }
    Set-Content -Path $hostsFile -Value $newContent
    Write-Host "Removed Solo Empire entries from hosts file" -ForegroundColor Green
} else {
    # Remove old entries first
    $hostsContent = Get-Content $hostsFile
    $newContent = @()
    $skip = $false
    foreach ($line in $hostsContent) {
        if ($line -eq $marker) { $skip = $true; continue }
        if ($skip -and $line -match "^\d+\.\d+\.\d+\.\d+.*\.local") { continue }
        if ($skip -and $line -eq "") { $skip = $false; continue }
        $newContent += $line
    }
    
    # Add new entries
    $newContent += ""
    $newContent += $marker
    $newContent += "$wslIP $($domains -join ' ')"
    
    Set-Content -Path $hostsFile -Value $newContent
    Write-Host "Added $($domains.Count) domains to hosts file" -ForegroundColor Green
}

# Flush DNS
ipconfig /flushdns | Out-Null
Write-Host "DNS cache flushed" -ForegroundColor Green
Write-Host ""
Write-Host "You can now access services at:" -ForegroundColor Yellow
$domains | Select-Object -First 10 | ForEach-Object { Write-Host "  https://$_" }
if ($domains.Count -gt 10) {
    Write-Host "  ... and $($domains.Count - 10) more"
}
Write-Host ""
Write-Host "Press Enter to exit..."
Read-Host
