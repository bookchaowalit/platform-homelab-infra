# Solo Empire - One-Time Setup
# Run ONCE as Administrator. Fixes DNS + HTTPS for all *.local services.
# After this, everything works automatically.

# ─── Admin check ───
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Restarting as Administrator..." -ForegroundColor Yellow
    Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

Write-Host ""
Write-Host "=== Solo Empire - One-Time Setup ===" -ForegroundColor Cyan
Write-Host ""

# ─── Step 1: Fix Cloudflare WARP DNS ───
Write-Host "[1/5] Checking Cloudflare WARP..." -ForegroundColor Yellow

$warpConfigDir = "C:\ProgramData\Cloudflare"
$warpConfigFile = "$warpConfigDir\mdm.xml"
if (Get-Process CloudflareWARP -ErrorAction SilentlyContinue) {
    if (-not (Test-Path $warpConfigDir)) { New-Item -Path $warpConfigDir -ItemType Directory -Force | Out-Null }
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
    Set-Content -Path $warpConfigFile -Value $warpXml -Force
    Write-Host "  WARP split DNS configured for .local domains" -ForegroundColor Green
    # Restart WARP to apply
    Restart-Service CloudflareWARP -ErrorAction SilentlyContinue
    Write-Host "  WARP restarted" -ForegroundColor Green
} else {
    Write-Host "  WARP not running, skipping" -ForegroundColor Gray
}

# ─── Step 2: Install SSL certificate ───
Write-Host "[2/5] Installing SSL certificate for *.local..." -ForegroundColor Yellow

$certPath = "\\wsl$\Ubuntu\home\bookchaowalit\book\solo-empire\infra\self-hosted-stack\traefik\certs\local.crt"

if (-not (Test-Path $certPath)) {
    # Try alternate WSL path
    $certPath = "\\wsl.localhost\Ubuntu\home\bookchaowalit\book\solo-empire\infra\self-hosted-stack\traefik\certs\local.crt"
}

if (Test-Path $certPath) {
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($certPath)
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "LocalMachine")
    $store.Open("ReadWrite")

    # Check if already installed
    $existing = $store.Certificates | Where-Object { $_.Subject -match "CN=Local Dev" }
    if ($existing) {
        Write-Host "  SSL certificate already installed" -ForegroundColor Green
    } else {
        $store.Add($cert)
        Write-Host "  SSL certificate installed successfully!" -ForegroundColor Green
    }
    $store.Close()
} else {
    Write-Host "  WARNING: Certificate file not found. HTTPS will show warnings." -ForegroundColor Red
    Write-Host "  Make sure WSL2 is running and the stack is up." -ForegroundColor Yellow
}

# ─── Step 3: Disable Secure DNS in Chrome ───
Write-Host "[3/5] Disabling Secure DNS in Chrome..." -ForegroundColor Yellow

$chromePolicyPath = "HKLM:\SOFTWARE\Policies\Google\Chrome"
if (-not (Test-Path $chromePolicyPath)) { New-Item -Path $chromePolicyPath -Force | Out-Null }
Set-ItemProperty -Path $chromePolicyPath -Name "DnsOverHttps" -Value 0 -Type DWord -Force

# Also set for Edge
Write-Host "[4/5] Disabling Secure DNS in Edge..." -ForegroundColor Yellow

$edgePolicyPath = "HKLM:\SOFTWARE\Policies\Microsoft\Edge"
if (-not (Test-Path $edgePolicyPath)) { New-Item -Path $edgePolicyPath -Force | Out-Null }
Set-ItemProperty -Path $edgePolicyPath -Name "DnsOverHttps" -Value 0 -Type DWord -Force

# ─── Step 4: Sync DNS ───
Write-Host "[5/5] Syncing DNS domains to hosts file..." -ForegroundColor Yellow

$wslIP = (bash -c "hostname -I 2>/dev/null")
$wslIP = ($wslIP -split '\s+')[0]
if (-not $wslIP) {
    $wslIP = (wsl hostname -I).Split(' ')[0]
}

if ($wslIP) {
    Write-Host "  WSL2 IP: $wslIP" -ForegroundColor Cyan

    $composePath = "\\wsl$\Ubuntu\home\bookchaowalit\book\solo-empire\infra\self-hosted-stack\docker-compose.yml"
    if (-not (Test-Path $composePath)) {
        $composePath = "\\wsl.localhost\Ubuntu\home\bookchaowalit\book\solo-empire\infra\self-hosted-stack\docker-compose.yml"
    }

    if (Test-Path $composePath) {
        $content = Get-Content $composePath -Raw
        $domains = [regex]::Matches($content, 'Host\(`([^`]+)`\)') |
            ForEach-Object { $_.Groups[1].Value } |
            Sort-Object -Unique

        $hostsFile = "$env:SystemRoot\System32\drivers\etc\hosts"
        $marker = "# Solo Empire Services"

        # Remove old entries
        $hostsContent = Get-Content $hostsFile
        $newContent = @()
        $skip = $false
        foreach ($line in $hostsContent) {
            if ($line.Trim() -eq $marker) { $skip = $true; continue }
            if ($skip -and $line -match "^\d+\.\d+\.\d+\.\d+.*\.local") { continue }
            if ($skip -and $line.Trim() -eq '') { $skip = $false; continue }
            $newContent += $line
        }

        # Add new
        # Add new entries - split into lines of 8 domains each
        # (Windows hosts file has a practical limit on line length)
        $newContent += ""
        $newContent += $marker
        for ($i = 0; $i -lt $domains.Count; $i += 8) {
            $end = [Math]::Min($i + 7, $domains.Count - 1)
            $chunk = $domains[$i..$end]
            $newContent += "$wslIP $($chunk -join ' ')"
        }
        Set-Content -Path $hostsFile -Value $newContent

        # Flush DNS
        ipconfig /flushdns | Out-Null
        Write-Host "  Synced $($domains.Count) domains (split into lines of 8)" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: docker-compose.yml not found" -ForegroundColor Red
    }
} else {
    Write-Host "  WARNING: Could not get WSL2 IP. Is WSL running?" -ForegroundColor Red
}

# ─── Done ───
Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "  - Cloudflare WARP: split DNS for .local (if WARP running)" -ForegroundColor Cyan
Write-Host "  - SSL certificate: installed in Windows trust store" -ForegroundColor Cyan
Write-Host "  - Secure DNS: disabled in Chrome & Edge (via policy)" -ForegroundColor Cyan
Write-Host "  - DNS domains: synced to hosts file" -ForegroundColor Cyan
Write-Host "  - Auto-sync: runs silently on WSL start" -ForegroundColor Cyan
Write-Host ""
Write-Host "  RESTART your browser now, then try:" -ForegroundColor Yellow
Write-Host "    https://homer.local" -ForegroundColor White
Write-Host "    https://grafana.local" -ForegroundColor White
Write-Host "  Traefik administrative dashboard is disabled and has no browser URL." -ForegroundColor DarkYellow
Write-Host ""
Write-Host "Press Enter to exit..."
Read-Host
