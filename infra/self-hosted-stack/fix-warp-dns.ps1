# Quick fix for Cloudflare WARP DNS hijacking .local domains
# Run as Administrator from Windows PowerShell

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Restarting as Administrator..." -ForegroundColor Yellow
    Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

# Get WSL2 IP
$wslIP = (bash -c "hostname -I 2>/dev/null")
$wslIP = ($wslIP -split '\s+')[0]
Write-Host "WSL2 IP: $wslIP" -ForegroundColor Cyan

# Fix WARP adapter DNS - point it to WSL2 IP so .local resolves
Write-Host "Fixing CloudflareWARP DNS..." -ForegroundColor Yellow
Set-DnsClientServerAddress -InterfaceAlias 'CloudflareWARP' -ServerAddresses $wslIP
$check = Get-DnsClientServerAddress -InterfaceAlias 'CloudflareWARP' -AddressFamily IPv4
Write-Host "  WARP DNS now: $($check.ServerAddresses -join ', ')" -ForegroundColor Green

# Write WARP split DNS config
$warpDir = "C:\ProgramData\Cloudflare"
if (-not (Test-Path $warpDir)) { New-Item -Path $warpDir -ItemType Directory -Force | Out-Null }
$warpXml = @'
<config>
  <service-mode-v2>
    <dns>
      <fallback>false</fallback>
      <resolve>
        <include>
          <match>.local</match>
        </include>
      </resolve>
    </dns>
  </service-mode-v2>
</config>
'@
Set-Content -Path "$warpDir\mdm.xml" -Value $warpXml -Force
Write-Host "  WARP split DNS config written" -ForegroundColor Green

# Flush DNS
ipconfig /flushdns | Out-Null

# Test
Write-Host ""
Write-Host "Testing..." -ForegroundColor Yellow
try {
    $result = [System.Net.Dns]::GetHostEntry('homer.local')
    Write-Host "  homer.local -> $($result.AddressList[0])" -ForegroundColor Green
    Write-Host ""
    Write-Host "SUCCESS! Open your browser and try https://homer.local" -ForegroundColor Green
} catch {
    Write-Host "  Still failing. Try: Disable Cloudflare WARP app completely." -ForegroundColor Red
}

Write-Host ""
Write-Host "Press Enter to exit..."
Read-Host
