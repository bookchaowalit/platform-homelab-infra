#!/usr/bin/env bash
# Solo Empire - Auto DNS Sync for local lab *.local hostnames
#
# Supports:
#   1) Native Linux  → updates /etc/hosts (needs sudo)
#   2) WSL2          → updates Windows hosts via powershell.exe (needs Admin)
#
# Usage:
#   bash sync-dns.sh
#   TARGET_IP=127.0.0.1 bash sync-dns.sh   # force IP (default: 127.0.0.1 on Linux)
#
# Note: .local is often intercepted by mDNS/WARP. After sync, test with:
#   getent hosts grafana.local
#   curl -k --resolve grafana.local:443:127.0.0.1 https://grafana.local/

set -euo pipefail

STACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$STACK_DIR/docker-compose.yml}"
MARKER="# Solo Empire Services"
BEGIN_MARKER="# BEGIN Solo Empire Services"
END_MARKER="# END Solo Empire Services"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "ERROR: compose file not found: $COMPOSE_FILE"
  exit 1
fi

# Extract Host(`...`) domains from compose labels
mapfile -t DOMAINS < <(grep -oP 'Host\(`[^`]+`\)' "$COMPOSE_FILE" | sed 's/Host(`//;s/`)//' | sort -u)
DOMAIN_COUNT="${#DOMAINS[@]}"
if [[ "$DOMAIN_COUNT" -eq 0 ]]; then
  echo "ERROR: no Host(\`...\`) domains found in $COMPOSE_FILE"
  exit 1
fi

is_wsl() {
  [[ -n "${WSL_DISTRO_NAME:-}" ]] || grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null
}

find_powershell() {
  local c
  for c in \
    powershell.exe \
    /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe \
    /mnt/c/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe
  do
    if command -v "$c" >/dev/null 2>&1 || [[ -x "$c" ]]; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

pick_linux_ip() {
  if [[ -n "${TARGET_IP:-}" ]]; then
    echo "$TARGET_IP"
    return
  fi
  # Prefer loopback: Traefik publishes 80/443 on the host
  echo "127.0.0.1"
}

sync_linux_hosts() {
  local ip hosts_file tmp block
  ip="$(pick_linux_ip)"
  hosts_file="/etc/hosts"
  tmp="$(mktemp)"

  echo "Mode: native Linux"
  echo "Target IP: $ip"
  echo "Domains: $DOMAIN_COUNT"
  echo "Hosts file: $hosts_file"

  # Build block: one domain per line (clearest for debugging)
  {
    echo "$BEGIN_MARKER"
    echo "$MARKER"
    for d in "${DOMAINS[@]}"; do
      printf '%s %s\n' "$ip" "$d"
    done
    echo "$END_MARKER"
  } >"$tmp.block"

  # Strip previous Solo Empire blocks (old or new markers)
  if [[ -r "$hosts_file" ]]; then
    awk -v begin="$BEGIN_MARKER" -v end="$END_MARKER" -v old="$MARKER" '
      $0 == begin { skip=1; next }
      $0 == end { skip=0; next }
      skip { next }
      # legacy format from older sync-dns: marker then IP lines with .local
      $0 == old { skip_legacy=1; next }
      skip_legacy && /^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/ && /\.local/ { next }
      skip_legacy && /^[[:space:]]*$/ { skip_legacy=0; next }
      skip_legacy { skip_legacy=0 }
      { print }
    ' "$hosts_file" >"$tmp.base"
  else
    : >"$tmp.base"
  fi

  {
    cat "$tmp.base"
    echo ""
    cat "$tmp.block"
    echo ""
  } >"$tmp.new"

  if [[ "$(id -u)" -eq 0 ]]; then
    cp "$tmp.new" "$hosts_file"
  else
    if ! sudo -n true 2>/dev/null; then
      echo ""
      echo "Need sudo to write $hosts_file"
    fi
    sudo cp "$tmp.new" "$hosts_file"
  fi

  rm -f "$tmp" "$tmp.base" "$tmp.block" "$tmp.new"

  # Best-effort resolver flush
  if command -v resolvectl >/dev/null 2>&1; then
    sudo resolvectl flush-caches 2>/dev/null || resolvectl flush-caches 2>/dev/null || true
  fi

  echo "Synced $DOMAIN_COUNT domains → $hosts_file ($ip)"
  echo ""
  echo "Quick checks:"
  echo "  getent hosts grafana.local"
  echo "  curl -k -I https://grafana.local/"
  echo "  curl -k --resolve grafana.local:443:127.0.0.1 https://grafana.local/   # bypass DNS"
  echo ""
  echo "If .local still fails with Cloudflare WARP: disable WARP briefly or add"
  echo ".local as a split-tunnel / local domain exclusion in WARP settings."
}

sync_windows_hosts() {
  local wsl_ip ps_domains ps
  wsl_ip="${TARGET_IP:-$(hostname -I | awk '{print $1}')}"
  if [[ -z "$wsl_ip" ]]; then
    echo "ERROR: Cannot determine WSL2 IP"
    exit 1
  fi

  ps="$(find_powershell)" || {
    echo "ERROR: powershell.exe not found (is Windows interop available?)"
    echo "On native Linux this script updates /etc/hosts instead."
    exit 1
  }

  ps_domains="$(printf "%s\n" "${DOMAINS[@]}" | sed "s/^/'/;s/$/'/" | paste -sd, -)"

  echo "Mode: WSL2 → Windows hosts"
  echo "WSL2 IP: $wsl_ip"
  echo "Domains: $DOMAIN_COUNT"
  echo "PowerShell: $ps"

  "$ps" -NoProfile -ExecutionPolicy Bypass -Command "
    \$hostsFile = 'C:\Windows\System32\drivers\etc\hosts'
    \$marker = '$MARKER'
    \$wslIP = '$wsl_ip'
    \$allDomains = @($ps_domains)

    \$warpAdapter = Get-NetAdapter -Name 'CloudflareWARP' -ErrorAction SilentlyContinue
    if (\$warpAdapter) {
        \$warpDir = 'C:\ProgramData\Cloudflare'
        if (-not (Test-Path \$warpDir)) { New-Item -Path \$warpDir -ItemType Directory -Force | Out-Null }
        \$warpXml = @'
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
        Set-Content -Path \"\$warpDir\mdm.xml\" -Value \$warpXml -Force -ErrorAction SilentlyContinue
        Set-DnsClientServerAddress -InterfaceAlias 'CloudflareWARP' -ServerAddresses \$wslIP -ErrorAction SilentlyContinue
    }

    \$lines = Get-Content \$hostsFile
    \$newLines = @()
    \$skip = \$false
    foreach (\$line in \$lines) {
        if (\$line.Trim() -eq \$marker) { \$skip = \$true; continue }
        if (\$line.Trim() -eq '# BEGIN Solo Empire Services') { \$skip = \$true; continue }
        if (\$line.Trim() -eq '# END Solo Empire Services') { \$skip = \$false; continue }
        if (\$skip -and \$line -match '^\d+\.\d+\.\d+\.\d+.*\.local') { continue }
        if (\$skip -and \$line.Trim() -eq '') { \$skip = \$false; continue }
        \$newLines += \$line
    }

    \$newLines += ''
    \$newLines += '# BEGIN Solo Empire Services'
    \$newLines += \$marker
    for (\$i = 0; \$i -lt \$allDomains.Count; \$i += 8) {
        \$end = [Math]::Min(\$i + 7, \$allDomains.Count - 1)
        \$chunk = \$allDomains[\$i..\$end]
        \$joined = \$chunk -join ' '
        \$newLines += (\$wslIP + ' ' + \$joined)
    }
    \$newLines += '# END Solo Empire Services'

    try {
        Set-Content -Path \$hostsFile -Value \$newLines -ErrorAction Stop
    } catch {
        Write-Host 'ERROR: Cannot write Windows hosts file. Run PowerShell as Administrator.'
        exit 1
    }

    ipconfig /flushdns | Out-Null
    Write-Host 'DNS synced'
  " 2>&1

  echo "Synced $DOMAIN_COUNT domains to Windows hosts file ($wsl_ip)"
}

# --- main ---
if is_wsl && find_powershell >/dev/null 2>&1; then
  sync_windows_hosts
else
  sync_linux_hosts
fi
