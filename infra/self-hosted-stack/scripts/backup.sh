#!/bin/bash
# Solo Empire Self-Hosted Stack Backup Script
# Backs up critical data from Docker volumes to /data/backups/
#
# Usage: ./backup.sh [full|critical]
#   full     - Backup all volumes (default)
#   critical - Backup only essential data (databases, configs)
#
# Cron example (daily at 2 AM):
#   0 2 * * * /path/to/backup.sh critical >> /var/log/solo-empire-backup.log 2>&1

set -euo pipefail

# Configuration — paths relative to this script (never hardcode checkout path).
STACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${SOLO_EMPIRE_STACK_BACKUP_DIR:-$HOME/solo-empire-backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup mode
MODE="${1:-full}"
log_info "Starting backup (mode: $MODE) at $(date)"

# Function to backup a Docker volume
backup_volume() {
    local volume_name="$1"
    local backup_name="$2"
    local full_volume="self-hosted-stack_${volume_name}"
    
    if ! docker volume inspect "$full_volume" &>/dev/null; then
        log_warn "Volume $full_volume does not exist, skipping"
        return 0
    fi
    
    local backup_file="${BACKUP_DIR}/${backup_name}_${TIMESTAMP}.tar.gz"
    
    log_info "Backing up $volume_name -> $backup_file"
    
    docker run --rm \
        -v "${full_volume}:/source:ro" \
        -v "${BACKUP_DIR}:/backup" \
        alpine:latest \
        tar -czf "/backup/${backup_name}_${TIMESTAMP}.tar.gz" -C /source .
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log_info "  ✓ $backup_name backed up ($size)"
    else
        log_error "  ✗ Failed to backup $backup_name"
        return 1
    fi
}

# Function to backup PostgreSQL database
backup_postgres() {
    log_info "Backing up PostgreSQL databases..."
    
    local backup_file="${BACKUP_DIR}/postgres_all_${TIMESTAMP}.sql.gz"
    
    docker exec se-postgres pg_dumpall -U postgres | gzip > "$backup_file"
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log_info "  ✓ PostgreSQL backed up ($size)"
    else
        log_error "  ✗ Failed to backup PostgreSQL"
        return 1
    fi
}

# Function to backup Gitea repositories
backup_gitea() {
    log_info "Backing up Gitea repositories..."
    
    local backup_file="${BACKUP_DIR}/gitea_repos_${TIMESTAMP}.tar.gz"
    
    # Dump Gitea data
    docker exec se-gitea tar -czf /tmp/gitea-dump.tar.gz -C /data .
    docker cp se-gitea:/tmp/gitea-dump.tar.gz "$backup_file"
    docker exec se-gitea rm /tmp/gitea-dump.tar.gz
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        log_info "  ✓ Gitea backed up ($size)"
    else
        log_error "  ✗ Failed to backup Gitea"
        return 1
    fi
}

# Function to backup Garage (S3)
backup_garage() {
    log_info "Backing up Garage metadata..."
    
    local backup_file="${BACKUP_DIR}/garage_meta_${TIMESTAMP}.tar.gz"
    
    # Backup Garage meta volume (data is in garage-data volume)
    backup_volume "garage-data" "garage_data"
}

# ============================================================
# Critical backups (always run)
# ============================================================
log_info "=== Critical Backups ==="

# PostgreSQL (most critical - contains all relational data)
backup_postgres

# Gitea (code repositories)
backup_gitea

# Vaultwarden (passwords)
backup_volume "vaultwarden-data" "vaultwarden"

# Grafana dashboards and configs
backup_volume "grafana-data" "grafana"

# Step CA (PKI certificates)
backup_volume "step-ca-data" "step_ca"

# Gatus (monitoring history)
backup_volume "gatus-data" "gatus"

if [ "$MODE" = "full" ]; then
    log_info "=== Full Backup (additional volumes) ==="
    
    # DuckDB analytics
    backup_volume "duckdb-data" "duckdb"
    
    # Prefect flows
    backup_volume "prefect-data" "prefect"
    
    # InfluxDB time-series
    backup_volume "influxdb-data" "influxdb"
    
    # Qdrant vector DB
    backup_volume "qdrant-data" "qdrant"
    
    # Valkey (Redis) cache
    backup_volume "valkey-data" "valkey"
    
    # PocketBase
    backup_volume "pocketbase-data" "pocketbase"
    
    # Wiki.js
    backup_volume "wikijs-data" "wikijs"
    
    # Listmonk (email campaigns)
    backup_volume "listmonk-data" "listmonk"
    
    # Gotify (notifications)
    backup_volume "gotify-data" "gotify"
    
    # NATS (message persistence)
    backup_volume "nats-data" "nats"
    
    # RabbitMQ
    backup_volume "rabbitmq-data" "rabbitmq"
    
    # Mosquitto (MQTT)
    backup_volume "mosquitto-data" "mosquitto"
    
    # Filebrowser
    backup_volume "filebrowser-data" "filebrowser"
    
    # Ollama (LLM models)
    backup_volume "ollama-data" "ollama"
    
    # Jupyter notebooks
    backup_volume "jupyter-data" "jupyter"
    
    # Garage (S3 data lake)
    backup_garage
fi

# ============================================================
# Cleanup old backups
# ============================================================
log_info "=== Cleanup (retention: ${RETENTION_DAYS} days) ==="

find "$BACKUP_DIR" -name "*.tar.gz" -mtime +${RETENTION_DAYS} -delete
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete

deleted_count=$(find "$BACKUP_DIR" -name "*.tar.gz" -o -name "*.sql.gz" | wc -l)
log_info "Current backup count: $deleted_count"

# ============================================================
# Summary
# ============================================================
total_size=$(du -sh "$BACKUP_DIR" | cut -f1)
log_info "=== Backup Complete ==="
log_info "Total backup size: $total_size"
log_info "Backup location: $BACKUP_DIR"
log_info "Completed at: $(date)"
