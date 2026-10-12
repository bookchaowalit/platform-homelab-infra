---
title: "Heavy Services Removed from Lightweight Stack"
tags: [documentation, infra]
created: 2026-07-09
updated: 2026-08-08
description: "Documentation for Heavy Services Removed from Lightweight Stack."
---

# Heavy Services Removed from Lightweight Stack

This document lists services removed from the self-hosted stack in two phases:
1. **Phase 1** (130 → 105): Heavy/resource-intensive services unsuitable for lightweight environments
2. **Phase 2** (105 → 81): Overlapping/duplicate services where a lighter/better alternative already exists

Phase 1 services are suitable for **company servers** with more resources (2GB+ RAM). Phase 2 services were deduplicated — the lightest, fastest, most scalable option was kept from each category.

---

## 🗄️ AI & Machine Learning (High RAM)

### Ollama
- **Image**: `ollama/ollama:latest`
- **RAM**: ~2GB+ (downloads and runs LLMs locally)
- **Purpose**: Local LLM inference (Llama, Mistral, CodeLlama, etc.)
- **Use Case**: Company AI/ML workloads, private chatbots, code assistance
- **Why Removed**: Too heavy for lightweight stack; requires GPU for optimal performance
- **Company Server Fit**: ✅ Excellent for AI teams, R&D departments

### OpenWebUI
- **Image**: `ghcr.io/open-webui/open-webui:main`
- **RAM**: ~300MB
- **Purpose**: Web UI for Ollama/LLM interaction
- **Use Case**: Chat interface for internal AI models
- **Why Removed**: Depends on Ollama; UI layer adds overhead
- **Company Server Fit**: ✅ Great paired with Ollama for internal AI chat

### Superset
- **Image**: `apache/superset:latest`
- **RAM**: ~500MB-1GB
- **Purpose**: Enterprise BI and data visualization platform
- **Use Case**: Business intelligence, analytics dashboards, SQL exploration
- **Why Removed**: Heavy Java/Python stack; slow startup
- **Company Server Fit**: ✅ Excellent for data teams, executives, reporting

---

## 📱 Social & Communication Platforms (Medium-High RAM)

### Misskey
- **Image**: `misskey/misskey:latest`
- **RAM**: ~300MB
- **Purpose**: Decentralized social media platform (ActivityPub)
- **Use Case**: Internal company social network, community building
- **Why Removed**: Node.js heavy; requires many dependencies
- **Company Server Fit**: ✅ Good for internal social platform, team engagement

### Friendica
- **Image**: `friendica/friendica:latest`
- **RAM**: ~200MB
- **Purpose**: Decentralized social network (ActivityPub, Diaspora)
- **Use Case**: Federated social platform
- **Why Removed**: PHP/Apache stack; redundant with Misskey
- **Company Server Fit**: ⚠️ Niche; Misskey is more modern

### Synapse (Matrix)
- **Image**: `matrixdotorg/synapse:latest`
- **RAM**: ~300MB
- **Purpose**: Matrix homeserver for federated chat
- **Use Case**: Enterprise messaging, bridge to Slack/Discord/Teams
- **Why Removed**: Python/Twisted; complex setup; redundant with simpler chat
- **Company Server Fit**: ✅ Excellent for secure, federated messaging

### Dendrite
- **Image**: `matrixorg/dendrite:latest`
- **RAM**: ~100MB
- **Purpose**: Next-gen Matrix homeserver (Go-based)
- **Use Case**: Lightweight Matrix alternative to Synapse
- **Why Removed**: Still in development; fewer features than Synapse
- **Company Server Fit**: ⚠️ Experimental; Synapse is more stable

---

## 🔄 ETL & Data Processing (High RAM)

### RabbitMQ
- **Image**: `rabbitmq:3-management`
- **RAM**: ~200MB
- **Purpose**: Message broker with management UI
- **Use Case**: Task queues, event-driven architecture, microservices
- **Why Removed**: Erlang-based; heavier than NATS/Redis for simple use
- **Company Server Fit**: ✅ Excellent for enterprise messaging, microservices

### Prefect
- **Image**: `prefecthq/prefect:2-latest`
- **RAM**: ~400MB
- **Purpose**: Modern workflow orchestration (Airflow alternative)
- **Use Case**: Data pipelines, ETL scheduling, task dependencies
- **Why Removed**: Python heavy; overkill for simple automation
- **Company Server Fit**: ✅ Great for data engineering teams

### DuckDB
- **Image**: `duckdb/duckdb:latest`
- **RAM**: ~200MB (in-memory analytics)
- **Purpose**: In-process SQL OLAP database
- **Use Case**: Fast analytical queries, data exploration
- **Why Removed**: Not a service; better as embedded library
- **Company Server Fit**: ⚠️ Use as library, not container

### ETL Pipeline (Custom)
- **Image**: Custom Python ETL
- **RAM**: ~300MB
- **Purpose**: Data extraction, transformation, loading
- **Use Case**: Sync data between systems
- **Why Removed**: Custom code; better handled by Kestra/Prefect
- **Company Server Fit**: ⚠️ Replace with Prefect or Airflow

### Vector
- **Image**: `timberio/vector:latest`
- **RAM**: ~150MB
- **Purpose**: High-performance log/metrics aggregator
- **Use Case**: Collect, transform, ship logs to Loki/Elasticsearch
- **Why Removed**: Rust-based but heavy config; Loki handles logs
- **Company Server Fit**: ✅ Excellent for log shipping, observability

---

## 🔍 Search & Discovery (Medium RAM)

### Redash
- **Image**: `redash/redash:latest`
- **RAM**: ~400MB
- **Purpose**: Query builder and visualization
- **Use Case**: SQL queries, dashboards, data exploration
- **Why Removed**: Python/Django; redundant with Metabase
- **Company Server Fit**: ✅ Good for analysts, data teams

---

## 📊 Monitoring & Observability (Medium RAM)

### Netdata
- **Image**: `netdata/netdata:latest`
- **RAM**: ~150MB
- **Purpose**: Real-time infrastructure monitoring
- **Use Case**: System metrics, alerts, dashboards
- **Why Removed**: C/Python; Prometheus+Grafana covers this
- **Company Server Fit**: ✅ Excellent for real-time monitoring

### Glances
- **Image**: `nicolargo/glances:latest`
- **RAM**: ~100MB
- **Purpose**: Cross-platform system monitoring
- **Use Case**: Top-like interface, API for metrics
- **Why Removed**: Python; redundant with Node Exporter
- **Company Server Fit**: ⚠️ Good for quick diagnostics

### SNMP Exporter
- **Image**: `prom/snmp-exporter:latest`
- **RAM**: ~50MB
- **Purpose**: SNMP to Prometheus metrics
- **Use Case**: Network device monitoring (switches, routers)
- **Why Removed**: Niche; only needed for SNMP devices
- **Company Server Fit**: ✅ Essential for network monitoring

### StatsD Exporter
- **Image**: `prom/statsd-exporter:latest`
- **RAM**: ~30MB
- **Purpose**: StatsD to Prometheus metrics
- **Use Case**: Application metrics collection
- **Why Removed**: Niche; Prometheus client libraries preferred
- **Company Server Fit**: ⚠️ Only if apps use StatsD protocol

---

## 📧 Email & Mailing (Medium RAM)

### HyperKitty
- **Image**: `maxking/mailman-hyperkitty:latest`
- **RAM**: ~200MB
- **Purpose**: Mailman 3 web UI for mailing lists
- **Use Case**: Mailing list archives, management
- **Why Removed**: Python/Django; Listmonk is simpler
- **Company Server Fit**: ⚠️ Only if using Mailman 3

### TT-RSS
- **Image**: `cluebot/ttrss:latest`
- **RAM**: ~150MB
- **Purpose**: Tiny Tiny RSS - web-based RSS reader
- **Use Case**: News aggregation, RSS feeds
- **Why Removed**: PHP; redundant with FreshRSS/Miniflux
- **Company Server Fit**: ⚠️ FreshRSS is more modern

---

## 🛠️ Development & CI/CD (Medium RAM)

### Forgejo
- **Image**: `codeberg/forgejo:latest`
- **RAM**: ~200MB
- **Purpose**: Soft fork of Gitea with more features
- **Use Case**: Git hosting, CI/CD
- **Why Removed**: Redundant with Gitea; kept Gitea for simplicity
- **Company Server Fit**: ✅ Excellent for Git hosting, more features than Gitea

### Woodpecker Broker
- **Image**: `woodpecker/broker:latest`
- **RAM**: ~50MB
- **Purpose**: Woodpecker CI message broker
- **Use Case**: Distributed CI/CD
- **Why Removed**: Unnecessary; server handles messaging
- **Company Server Fit**: ⚠️ Only for distributed CI setups

---

## 🎥 Media & Streaming (High RAM)

### Piped / Piped-API
- **Image**: `1337kavin/piped:latest`
- **RAM**: ~300MB
- **Purpose**: Alternative YouTube frontend
- **Use Case**: Privacy-focused YouTube viewing
- **Why Removed**: Java/Spring; heavy; niche use
- **Company Server Fit**: ⚠️ Legal concerns; not for production

### Invidious
- **Image**: `quay.io/invidious/invidious:latest`
- **RAM**: ~200MB
- **Purpose**: Alternative YouTube frontend (Crystal)
- **Use Case**: Privacy-focused YouTube viewing
- **Why Removed**: Crystal lang; redundant with Piped
- **Company Server Fit**: ⚠️ Legal concerns; not for production

### Libreddit / Teddit
- **Image**: `spikecodes/libreddit:latest`
- **RAM**: ~100MB
- **Purpose**: Alternative Reddit frontend
- **Use Case**: Privacy-focused Reddit viewing
- **Why Removed**: Rust; niche; Reddit API changes broke it
- **Company Server Fit**: ❌ Reddit API changes make this obsolete

---

## 🗂️ File & Storage (Medium RAM)

### Pictrs
- **Image**: `asonix/pictrs:latest`
- **RAM**: ~150MB
- **Purpose**: Simple image hosting service
- **Use Case**: Image storage for Lemmy/Mastodon
- **Why Removed**: Rust; niche; only needed for federated social
- **Company Server Fit**: ⚠️ Only if running Lemmy/Mastodon

---

## 🖥️ Desktop Applications (Not Services)

### Logseq
- **Image**: Desktop app (not Docker)
- **RAM**: ~300MB
- **Purpose**: Knowledge management, note-taking
- **Use Case**: Personal wiki, outliner
- **Why Removed**: Desktop app, not a service
- **Company Server Fit**: ❌ Not suitable for server

### DBeaver
- **Image**: Desktop app (not Docker)
- **RAM**: ~500MB
- **Purpose**: Universal database tool
- **Use Case**: SQL queries, database management
- **Why Removed**: Desktop app, not a service
- **Company Server Fit**: ❌ Not suitable for server; use Adminer instead

---

## 🌐 Networking & DNS (Low-Medium RAM)

### Stubby
- **Image**: `klutchell/stubby:latest`
- **RAM**: ~30MB
- **Purpose**: DNS-over-TLS stub resolver
- **Use Case**: Encrypted DNS queries
- **Why Removed**: Niche; CoreDNS handles DNS
- **Company Server Fit**: ⚠️ Only if DNS-over-TLS required

### Requestly
- **Image**: `requestly/requestly:latest`
- **RAM**: ~200MB
- **Purpose**: API mocking and request interception
- **Use Case**: API testing, debugging
- **Why Removed**: Node.js; redundant with MockServer/WireMock
- **Company Server Fit**: ⚠️ MockServer is more robust

---

## 📈 Analytics & Metrics (Medium RAM)

### Zenith
- **Image**: `zenithhq/zenith:latest`
- **RAM**: ~100MB
- **Purpose**: Timeseries database
- **Use Case**: Metrics storage, monitoring
- **Why Removed**: Niche; Prometheus/InfluxDB cover this
- **Company Server Fit**: ⚠️ InfluxDB is more established

---

## Summary by Resource Requirements

### High RAM (500MB+)
- **Ollama** (~2GB) - Local LLM inference
- **Superset** (~500MB) - Business intelligence
- **DBeaver** (~500MB) - Desktop DB tool

### Medium RAM (200-400MB)
- **Misskey** (~300MB) - Social platform
- **Synapse** (~300MB) - Matrix chat
- **Prefect** (~400MB) - Workflow orchestration
- **Redash** (~400MB) - Query builder
- **Piped** (~300MB) - YouTube frontend
- **Logseq** (~300MB) - Knowledge management
- **OpenWebUI** (~300MB) - LLM UI

### Low-Medium RAM (100-200MB)
- **RabbitMQ** (~200MB) - Message broker
- **DuckDB** (~200MB) - Analytics DB
- **Vector** (~150MB) - Log aggregator
- **Netdata** (~150MB) - Real-time monitoring
- **Friendica** (~200MB) - Social network
- **Forgejo** (~200MB) - Git hosting
- **HyperKitty** (~200MB) - Mailing list UI
- **TT-RSS** (~150MB) - RSS reader
- **Invidious** (~200MB) - YouTube frontend
- **Pictrs** (~150MB) - Image hosting
- **Requestly** (~200MB) - API mocking

### Low RAM (<100MB)
- **Glances** (~100MB) - System monitoring
- **SNMP Exporter** (~50MB) - Network monitoring
- **StatsD Exporter** (~30MB) - App metrics
- **Stubby** (~30MB) - DNS-over-TLS
- **Woodpecker Broker** (~50MB) - CI messaging
- **Zenith** (~100MB) - Timeseries DB
- **Libreddit** (~100MB) - Reddit frontend
- **Dendrite** (~100MB) - Matrix (Go)

---

## Recommended Company Server Stack

For a company server with 16-32GB RAM, consider adding:

### Tier 1: Essential (Add These First)
1. **Ollama + OpenWebUI** - Internal AI chatbot
2. **Superset** - Business intelligence
3. **RabbitMQ** - Enterprise messaging
4. **Synapse** - Secure federated chat
5. **Prefect** - Data pipeline orchestration

### Tier 2: Nice to Have
6. **Netdata** - Real-time monitoring
7. **Forgejo** - Enhanced Git hosting
8. **Redash** - SQL query builder
9. **Vector** - Log shipping

### Tier 3: Specialized
10. **SNMP Exporter** - Network device monitoring
11. **Misskey** - Internal social platform
12. **Piped** - Video streaming (legal considerations)

---

## Docker Compose Snippet (Company Server Additions)

```yaml
# Add to docker-compose.yml for company server

services:
  # AI/ML
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    deploy:
      resources:
        limits:
          memory: 2G

  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: openwebui
    restart: unless-stopped
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - openwebui-data:/app/data

  # Business Intelligence
  superset:
    image: apache/superset:latest
    container_name: superset
    restart: unless-stopped
    ports:
      - "8088:8088"
    environment:
      - SUPERSET_SECRET_KEY=your-secret-key
      - SUPERSET_LOAD_EXAMPLES=yes
    volumes:
      - superset-data:/app/superset_home

  # Enterprise Messaging
  rabbitmq:
    image: rabbitmq:3-management
    container_name: rabbitmq
    restart: unless-stopped
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      - RABBITMQ_DEFAULT_USER=admin
      - RABBITMQ_DEFAULT_PASS=soloempire2026
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq

  # Federated Chat
  synapse:
    image: matrixdotorg/synapse:latest
    container_name: synapse
    restart: unless-stopped
    ports:
      - "8008:8008"
    environment:
      - SYNAPSE_SERVER_NAME=chat.company.local
      - SYNAPSE_REPORT_STATS=no
    volumes:
      - synapse-data:/data

  # Workflow Orchestration
  prefect:
    image: prefecthq/prefect:2-latest
    container_name: prefect
    restart: unless-stopped
    ports:
      - "4200:4200"
    volumes:
      - prefect-data:/root/.prefect

volumes:
  ollama-data:
  openwebui-data:
  superset-data:
  rabbitmq-data:
  synapse-data:
  prefect-data:
```

---

## Migration Notes

When moving from lightweight stack to company server:

1. **Resource Allocation**: Assign 2-4GB RAM minimum for heavy services
2. **Database Backups**: Ensure PostgreSQL backups are configured
3. **SSL/TLS**: Use Let's Encrypt or internal CA for all services
4. **Authentication**: Enable OAuth2/LDAP integration where possible
5. **Monitoring**: Add SNMP Exporter for network devices
6. **Log Shipping**: Use Vector to ship logs to centralized Loki
7. **Backup Strategy**: Implement 3-2-1 backup rule for critical data

---

---

## Phase 2: Overlapping Services Removed (105 → 81)

Deduplicated 24 services across 18 categories. Kept the **lightest, fastest, most scalable** option.

| # | Removed | Kept | Category | Reason |
|---|---------|------|----------|--------|
| 1 | Shiori | linkding | Bookmarks | linkding lighter, better UI |
| 2 | Typesense | Meilisearch | Search | Meilisearch faster, simpler API |
| 3 | Gotify | ntfy | Push notifications | ntfy ~10MB, simpler protocol |
| 4 | Garage | MinIO | S3 storage | MinIO industry standard |
| 5 | Filegator | Filebrowser + Alist | File managers | Redundant with 2 keepers |
| 6 | Filestash | Filebrowser + Alist | File managers | Redundant with 2 keepers |
| 7 | WireMock | MockServer | API mocking | MockServer covers both |
| 8 | JSON Server | MockServer | API mocking | MockServer covers both |
| 9 | Nginx | Caddy | Web servers | Caddy auto-TLS, simpler config |
| 10 | HAProxy | Traefik | Load balancer | Traefik is primary proxy |
| 11 | Dnsmasq | CoreDNS | DNS | CoreDNS plugin-based, modern |
| 12 | Nginx Proxy Manager | Traefik | Reverse proxy GUI | Traefik already primary |
| 13 | Flatnotes | Memos + Joplin | Notes | Redundant with 2 keepers |
| 14 | Draw.io | Excalidraw | Diagrams | Excalidraw lighter, real-time |
| 15 | HedgeDoc | CryptPad | Collab editing | CryptPad E2E encrypted |
| 16 | Docmost | BookStack + Outline | Wiki/Knowledge | Redundant with 2 keepers |
| 17 | Wiki.js | BookStack + Outline | Wiki/Knowledge | Redundant with 2 keepers |
| 18 | FreshRSS | Miniflux | RSS readers | Miniflux lighter, Go-based |
| 19 | WriteFreely | Ghost | Blogging | Ghost more powerful, single |
| 20 | Plume | Ghost | Blogging | Ghost more powerful, single |
| 21 | Dashy | Homer | Dashboards | Homer lighter, simpler |
| 22 | Maybe | Firefly III | Finance | Firefly III mature, proven |
| 23 | Logseq | Memos + Joplin | Notes | Redundant with keepers |
| 24 | Gatus | Uptime Kuma | Health monitoring | Uptime Kuma better UI |

---

**Last Updated**: 2026-07-08  
**Lightweight Stack**: 81 services (docker-compose.yml) — zero overlap, optimized  
**Phase 1 Removed**: 25 heavy services (company server reference)  
**Phase 2 Removed**: 24 overlapping services (deduplicated)
