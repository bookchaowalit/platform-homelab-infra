---
title: "Solo Empire Self-Hosted Infrastructure Stack"
tags: [documentation, infra]
created: 2026-07-09
updated: 2026-09-08
description: "Documentation for Solo Empire Self-Hosted Infrastructure Stack."
---

# Solo Empire Self-Hosted Infrastructure Stack

> **LOCAL DEVELOPMENT / LEARNING LAB ONLY**
>
> This Compose stack is for trusted local workstations (e.g. WSL2). It is **not**
> production infrastructure and must not be exposed to the public internet.
>
> - Secrets: copy `.env.example` → `.env` (gitignored) and set values locally.
> - Watchtower is **disabled by default** (profile `lab-auto-update` only). Do not
>   use Watchtower as a production update workflow.
> - Traefik HTTP/HTTPS ports are bound to `127.0.0.1` by default; its
>   administrative dashboard is disabled.
> - The SQLite browser is disabled at the Traefik edge because the mounted
>   database contains private operational data.
> - Traefik uses a read-only Docker socket proxy on an internal control
>   network. Services that still require a direct Docker socket are isolated
>   behind explicit opt-in profiles: `docker-control` (platform telemetry/CI),
>   `docker-admin` (Portainer/Dozzle), `lab-auto-update` (Watchtower), and
>   `data` (Kestra). Do not expose those profiles outside this trusted lab.
> - Production multi-app deployment: see [`infra/platform/`](../platform/) and
>   [`operations/platform/KUBERNETES-PLATFORM-READINESS.md`](../../operations/platform/KUBERNETES-PLATFORM-READINESS.md).

Lightweight infrastructure for learning data engineering, DevOps, networking, security, databases, messaging, ML, and observability on WSL2.

**Profile-based lab · do not start all ~80 services at once · zero production intent**

## Compose profiles (use these)

| Profile | Use for |
|---------|---------|
| `core` | Traefik, CoreDNS, Homer, read-only Docker socket proxy |
| `observability` | Prometheus, Grafana, Loki, Tempo, Alertmanager |
| `devsecops` | Gitea, Woodpecker CI server, Step CA, Vaultwarden |
| `data` | PostgreSQL, MinIO, NATS, Qdrant, Kestra, Metabase, … |
| `streaming` | Optional single-broker Redpanda Kafka-compatible event-streaming lab |
| `optional` | Adminer and other learning tools without Docker host access |
| `docker-control` | Woodpecker server + Agent, Autoheal, Diun, cAdvisor, Uptime Kuma, Trivy (direct host control; opt-in) |
| `docker-admin` | Portainer and Dozzle (direct host control; opt-in) |
| `lab-auto-update` | Watchtower only (lab; not production) |

Full guide: [`PROFILES.md`](./PROFILES.md)

Ownership rules: [`SERVICE-OWNERSHIP.md`](./SERVICE-OWNERSHIP.md)

The default shared profiles intentionally do not start containers with direct
Docker API or host-runtime access. Add `docker-control` only for a trusted
local exercise that needs those services; use `docker-admin` for Portainer or
Dozzle. `Kestra` remains in `data` because its lab Docker task runner is part
of that profile's explicit local-control boundary.

```bash
cd infra/self-hosted-stack
cp -n .env.example .env

# Recommended shared platform only (no project data services):
./scripts/lab-up.sh shared-platform

# Add platform services that need direct Docker control only when required:
# ./scripts/lab-up.sh shared-platform docker-control

# Full local practice set, including lab-only data services:
./scripts/lab-up.sh core observability devsecops data

# Or manually:
docker compose --profile core --profile observability up -d

# Optional Kafka-compatible streaming lake lab (not part of data/shared-platform):
docker compose --profile streaming up -d
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                WSL2 Ubuntu (32GB RAM) — 40 Services, ~2.0GB                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DATA ENGINEERING          MONITORING              DEVOPS                    │
│  ┌──────────┐ ┌────────┐  ┌──────────┐ ┌──────┐  ┌──────┐ ┌────────┐    │
│  │Data Lake │→│ MinIO │  │Prometheus│→│Grafana│  │Gitea │→│Woodpecker│    │
│  │(Workers) │ │(S3    │  │(Metrics) │ │(UI)  │  │(Git) │ │(CI/CD) │    │
│  │          │ │ Lab)  │  │  :9090   │ │:3000 │  │:3004 │ │ :3005  │    │
│  └──────────┘ └────────┘  └──────────┘ └──────┘  └──────┘ └────────┘    │
│       │              │           │                                          │
│       ▼              ▼           ▼                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────┐  ┌──────┐  ┌──────┐               │
│  │  DuckDB  │  │  Vector  │  │ Loki │  │Dozzle│  │Tempo │               │
│  │(Analytics│  │(Pipeline)│  │(Logs)│  │(Logs)│  │(Trace│               │
│  │  CLI     │  │  :9100   │  │:3100 │  │:8080 │  │:3200 │               │
│  └──────────┘  └──────────┘  └──────┘  └──────┘  └──────┘               │
│                                                                              │
│  SECURITY                DATABASES               MESSAGING                  │
│  ┌──────────┐ ┌────────┐  ┌────────┐ ┌────────┐  ┌──────┐ ┌────────┐    │
│  │Vaultwarden│ │Step-CA│  │Valkey  │ │PocketB.│  │ NATS │ │Mosquitto│    │
│  │(Passwords)│ │(PKI)  │  │(Cache) │ │(SQLite)│  │(Msg) │ │(MQTT)  │    │
│  │  :3011   │ │:3012  │  │ :6379  │ │ :3014  │  │:4222 │ │ :1883  │    │
│  └──────────┘ └────────┘  └────────┘ └────────┘  └──────┘ └────────┘    │
│  ┌──────┐ ┌────────┐ ┌────────┐ ┌────────┐  ┌────────┐                   │
│  │Trivy │ │InfluxDB│ │Qdrant  │ │Postgres│  │RabbitMQ│                   │
│  │(CVE) │ │(TSDB)  │ │(Vector)│ │(RDBMS) │  │(AMQP)  │                   │
│  │:8080 │ │:3015   │ │:3016   │ │:5432   │  │:5672   │                   │
│  └──────┘ └────────┘ └────────┘ └────────┘  └────────┘                   │
│                                                                              │
│  API & PROTOCOLS         FILE & STORAGE          COMMUNICATION              │
│  ┌──────────┐ ┌────────┐  ┌──────────┐          ┌────────┐ ┌────────┐    │
│  │ PostgREST│ │Filebrws│  │ Synapse  │          │Listmonk│ │ Gotify │    │
│  │(Auto REST│ │(Files) │  │(Matrix)  │          │(Email) │ │(Push)  │    │
│  │  :3017   │ │:3019   │  │  :3021   │          │ :3022  │ │ :3020  │    │
│  └──────────┘ └────────┘  └──────────┘          └────────┘ └────────┘    │
│                                                                              │
│  CODE QUALITY            ML & DATA SCIENCE        NETWORKING               │
│  ┌──────────┐            ┌────────┐ ┌────────┐  ┌────────┐ ┌────────┐    │
│  │  Wiki.js │            │Ollama  │ │Jupyter │  │CoreDNS │ │ Caddy  │    │
│  │(Wiki/KB) │            │(Local  │ │(Notebk)│  │(DNS)   │ │(AutoTLS│    │
│  │  :3024   │            │ LLM)   │ │ :3026  │  │ :5353  │ │:2080   │    │
│  └──────────┘            │:11434  │ └────────┘  └────────┘ └────────┘    │
│                           └────────┘                                       │
│  ┌────────┐ ┌────────┐                                                  │
│  │ Nginx  │ │ Gatus  │                                                  │
│  │(Static)│ │(Health)│                                                  │
│  │ :8082  │ │ :3027  │                                                  │
│  └────────┘ └────────┘                                                  │
│                                                                              │
│  INFRASTRUCTURE (background)                                                │
│  Traefik (:80/:443; dashboard disabled) · AdGuard (:3003) · Watchtower     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

> **Live inventory note:** the diagram and learning tables include optional or
> historical exercises. The current Compose service/profile inventory is the
> source of truth; check it with `docker compose --profile '*' config --services`.

## Services by Domain

### Data Engineering

| Service | Image | Port | Concept | Cloud Alt |
|---------|-------|------|---------|-----------|
| **Data Lake runtime** | data-lake-core:local | internal | Python/PyArrow ingest, Avro sink, Parquet/Iceberg conversion | Managed jobs / Spark / Flink |
| **MinIO** | minio/minio | internal `:9000`, console via Traefik | S3-compatible Object Storage learning lab | AWS S3 / Cloudflare R2 |
| **Redpanda** | docker.redpanda.com/redpandadata/redpanda:v26.2.1 | :19092 / :18081 / :18082 | Kafka-compatible event streaming; single-broker lab only | Managed Kafka / Redpanda Cloud |
| **Stream sink** | data-lake-core:local | — | Redpanda → Avro + manifest/checkpoint | Kafka Connect / Flink |
| **Stream converter** | data-lake-core:local | — | Avro → Bronze Parquet → Iceberg | Managed Spark/Flink |
| **DuckDB** | python:3.11-slim | CLI only | Embedded OLAP analytics | MotherDuck |
| **ETL Pipeline** | se-etl-pipeline | — | Prometheus → DuckDB ETL | Custom |
| **Vector log shipper** | — | — | Historical/optional exercise; not defined in the current Compose inventory | Datadog |

The MinIO role-policy baseline for the canonical lake prefix is maintained in
[`minio/policies/`](./minio/policies/). It is an offline, reviewable artifact
only; apply it to a local lab identity after the policy test and operator gate.

### Monitoring & Observability

| Service | Image | Port | Concept | Cloud Alt |
|---------|-------|------|---------|-----------|
| **Prometheus** | prom/prometheus:v2.51.0 | :9090 | Time-series metrics | Grafana Cloud |
| **Grafana** | grafana/grafana:10.4.1 | :3000 | Dashboard visualization | Grafana Cloud |
| **Node Exporter** | prom/node-exporter:v1.7.0 | :9100 | Host system metrics | Cloud native |
| **Loki** | grafana/loki:2.9.4 | :3100 | Log aggregation | Grafana Cloud Logs |
| **Tempo** | grafana/tempo:latest | :3200 | Distributed tracing | Grafana Cloud Tempo |
| **Dozzle** | amir20/dozzle | :8080 | Docker log viewer | None |
| **Gatus** | twinproduction/gatus | :3027 | Uptime health checks | Healthchecks.io |

### DevOps & CI/CD

| Service | Image | Port | Concept | Cloud Alt |
|---------|-------|------|---------|-----------|
| **Gitea** | gitea/gitea | :3004, :2222 | Self-hosted Git | GitHub |
| **Woodpecker** | woodpeckerci/woodpecker:v3 | :3005 | CI/CD pipelines | GitHub Actions |
| **Ansible** | CLI only | — | Config management | Terraform Cloud |
| **Watchtower** | containrrr/watchtower (profile `lab-auto-update`) | — | Lab-only auto-update; **not** for production | Manual / GitOps |

### Security & Identity

| Service | Image | Port | Concept | Cloud Alt |
|---------|-------|------|---------|-----------|
| **Vaultwarden** | vaultwarden/server | :3011 | Password vault, AES-256 | 1Password |
| **Step CA** | smallstep/step-ca | :3012 | Internal PKI, mTLS, X.509 | Let's Encrypt |
| **Trivy** | aquasec/trivy | :8080 | Container CVE scanning, SBOM | Snyk |

### Database Engines

| Service | Image | Port | Concept | Cloud Alt |
|---------|-------|------|---------|-----------|
| **Valkey** | valkey/valkey | :6379 | In-memory key-value, pub/sub | Redis Cloud |
| **PocketBase** | ghcr.io/muchobien/pocketbase | :3014 | Embedded DB + REST + Auth | Supabase |
| **InfluxDB** | influxdb:2.7 | :3015 | Time-series DB, Flux queries | InfluxDB Cloud |
| **Qdrant** | qdrant/qdrant | :3016 | Vector similarity search | Pinecone |
| **PostgreSQL** | postgres:16-alpine | :5432 | ACID relational DB | RDS, Supabase |

### Messaging & Events

| Service | Image | Port | Concept | Cloud Alt |
|---------|-------|------|---------|-----------|
| **NATS** | nats:latest | :4222, :8222 | Lightweight messaging, JetStream | AWS SNS/SQS |
| **Mosquitto** | eclipse-mosquitto | :1883 | MQTT, IoT protocol | AWS IoT Core |
| **RabbitMQ** | rabbitmq:3-management | :5672, :15672 | AMQP, exchanges, DLQ | CloudAMQP |

### API & Protocols

| Service | Image | Port | Concept | Cloud Alt |
|---------|-------|------|---------|-----------|
| **PostgREST** | postgrest/postgrest | :3017 | Auto REST from DB schema | PostgREST Cloud |

### File & Storage

| Service | Image | Port | Concept | Cloud Alt |
|---------|-------|------|---------|-----------|
| **Filebrowser** | filebrowser/filebrowser | :3019 | Web file manager | Google Drive |

### Communication

| Service | Image | Port | Concept | Cloud Alt |
|---------|-------|------|---------|-----------|
| **Synapse** | matrixdotorg/synapse | :3021 | Matrix protocol, E2E encryption | Matrix.org |
| **Listmonk** | listmonk/listmonk | :3022 | Email newsletters, campaigns | Mailchimp |
| **Gotify** | gotify/server | :3020 | Push notifications, WebSocket | Firebase |

### Code Quality & Documentation

| Service | Image | Port | Concept | Cloud Alt |
|---------|-------|------|---------|-----------|
| **Wiki.js** | requarks/wiki | :3024 | Knowledge base, versioning | Notion, Confluence |

### ML & Data Science

| Service | Image | Port | Concept | Cloud Alt |
|---------|-------|------|---------|-----------|
| **Ollama** | ollama/ollama | :11434 | Local LLM inference | OpenAI API |
| **Jupyter** | jupyter/minimal-notebook | :3026 | Interactive notebooks | Google Colab |

### Networking & Infrastructure

| Service | Image | Port | Concept | Cloud Alt |
|---------|-------|------|---------|-----------|
| **Traefik** | traefik:v3.6 | :80, :443 | Reverse proxy, TLS, routing; dashboard disabled | Cloudflare |
| **AdGuard Home** | adguard/adguardhome | :3003 | DNS filtering, ad blocking | NextDNS |
| **CoreDNS** | coredns/coredns | :5353 | Programmable DNS | Route 53 |
| **Caddy** | caddy:latest | :2080, :2443 | Auto-TLS, ACME client | None |
| **Nginx** | nginx:alpine | :8082 | Static serving, load balancing | CloudFront |

## Port Mappings

| Service | Host Port | Container Port |
|---------|-----------|----------------|
| Traefik HTTP | 80 | 80 |
| Traefik HTTPS | 443 | 443 |
| Traefik Dashboard | not published | internal entrypoint disabled |
| Mosquitto MQTT | 1883 | 1883 |
| Ollama | 11434 | 11434 |
| Valkey | 6379 | 6379 |
| Postgres | 5432 | 5432 |
| NATS | 4222 | 4222 |
| NATS Monitor | 8222 | 8222 |
| RabbitMQ AMQP | 5672 | 5672 |
| RabbitMQ Mgmt | 15672 | 15672 |
| MinIO S3 | internal only | 9000 |
| MinIO Console | `https://minio.local` via Traefik | 9001 |
| AdGuard Home | 3003 | 80 |
| Gitea | 3004 | 3000 |
| Gitea SSH | 2222 | 22 |
| Woodpecker CI | 3005 | 8000 |
| Vaultwarden | 3011 | 80 |
| Step CA | 3012 | 9000 |
| PocketBase | 3014 | 8080 |
| InfluxDB | 3015 | 8086 |
| Qdrant | 3016 | 6333 |
| PostgREST | 3017 | 3000 |
| Filebrowser | 3019 | 80 |
| Gotify | 3020 | 80 |
| Synapse | 3021 | 8008 |
| Listmonk | 3022 | 9000 |
| Wiki.js | 3024 | 3000 |
| Jupyter | 3026 | 8888 |
| Gatus | 3027 | 8080 |
| Caddy HTTP | 2080 | 80 |
| Caddy HTTPS | 2443 | 443 |
| Nginx | 8082 | 80 |
| Tempo | 3200 | 3200 |
| Tempo Jaeger | 14268 | 14268 |
| CoreDNS | 5353 | 53 |

## Credentials

All secrets are injected from a local **`.env`** file (never committed).

```bash
cp .env.example .env
# edit .env — set strong unique values for every password/token
docker compose config --quiet   # validate after filling .env
docker compose up -d
```

See [`.env.example`](./.env.example) for the full variable list (names + safe placeholders only).

| Service | Variable(s) |
|---------|-------------|
| Grafana | `GF_SECURITY_ADMIN_USER`, `GF_SECURITY_ADMIN_PASSWORD` |
| PostgreSQL | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` |
| Vaultwarden | `VAULTWARDEN_ADMIN_TOKEN` |
| Woodpecker | `WOODPECKER_AGENT_SECRET` |
| MinIO | `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` |
| InfluxDB | `INFLUXDB_ADMIN_USER`, `INFLUXDB_ADMIN_PASSWORD` |

**Never** reuse lab passwords in production or commit `.env`.

## Quick Start

### 1. Start the Stack

```bash
cd <path-to-solo-homelab>/infra/self-hosted-stack
cp -n .env.example .env   # first time only; then edit secrets
docker compose up -d
# Optional lab auto-updater (NOT for production):
# docker compose --profile lab-auto-update up -d
```

### 2. Verify Services

```bash
docker compose ps    # All 82 containers should be Up
docker stats --no-stream  # Check ~2.0GB total RAM
```

### 3. Access via HTTPS (Recommended)

Most enabled services are accessible via `https://<service>.local` through
Traefik reverse proxy with trusted SSL. The Traefik dashboard and SQLite
browser are intentionally not routed:

```
https://homer.local       # Service Dashboard
# Traefik dashboard is disabled and has no public/local route.
https://grafana.local     # Grafana
https://gitea.local       # Gitea (Git)
https://vaultwarden.local # Vaultwarden (Passwords)
https://wikijs.local      # Wiki.js
https://filebrowser.local # Filebrowser
https://gotify.local      # Gotify (Push)
https://listmonk.local    # Listmonk (Email)
https://jupyter.local     # Jupyter
https://gatus.local       # Gatus (health checks)
https://tempo.local       # Tempo (tracing)
https://rabbitmq.local    # RabbitMQ Management
https://nats.local        # NATS Monitor
https://adguard.local     # AdGuard Home
```

> **First-time setup:** Run `one-time-setup.ps1` as Administrator on Windows to install the SSL cert and sync DNS. See [DNS & HTTPS Setup](#dns--https-setup) below.

### 4. Direct Port Access (Fallback)

```
# Traefik dashboard is disabled and has no host port.
http://localhost:3003   # AdGuard Home
http://localhost:3004   # Gitea
http://localhost:3005   # Woodpecker CI
http://localhost:3011   # Vaultwarden
http://localhost:3019   # Filebrowser
http://localhost:3020   # Gotify
http://localhost:3021   # Synapse (Matrix)
http://localhost:3022   # Listmonk
http://localhost:3024   # Wiki.js
http://localhost:3026   # Jupyter
http://localhost:3027   # Gatus (health checks)
http://localhost:3200   # Tempo (tracing)
http://localhost:15672  # RabbitMQ Management
http://localhost:8222   # NATS Monitor
http://localhost:2080   # Caddy
http://localhost:8082   # Nginx
```

## Data Engineering Pipeline

```
Prometheus (metrics) → Python ETL → DuckDB (analytics) → Grafana (visualization)
```

- **Extract:** Queries Prometheus every 5 min for CPU, memory, disk, network
- **Transform:** Aggregates time-series data, adds business labels
- **Load:** Inserts into DuckDB (6 tables + 1 view)
- **Visualize:** Pre-built Grafana dashboard with 10 panels

## DNS & HTTPS Setup

All 64 `.local` domains use HTTPS with a trusted SSL certificate. On WSL2, DNS is handled via the Windows hosts file.

### One-Time Setup (Windows)

Run as **Administrator** in PowerShell:

```powershell
# From Windows PowerShell (adjust UNC for your WSL distro + checkout):
# & "\\wsl$\Ubuntu\home\<user>\book\solo-empire\infra\self-hosted-stack\one-time-setup.ps1"
```

This does:
1. Installs SSL cert (`CN=Local Dev`) into Windows trust store
2. Disables Secure DNS in Chrome & Edge (via policy)
3. Syncs all 64 domains to `C:\Windows\System32\drivers\etc\hosts`
4. Configures Cloudflare WARP split DNS (if running)

### Auto-Sync

DNS syncs silently on Windows login (no popup).

Manual sync from WSL:
```bash
bash infra/self-hosted-stack/sync-dns.sh
```

Manual sync from Windows PowerShell (Admin):
```powershell
bash ./sync-dns.sh   # run from this directory (infra/self-hosted-stack)
```

## File Structure

```
self-hosted-stack/
├── docker-compose.yml          # Main orchestration (lab only)
├── .env.example                # Secret variable names + placeholders
├── .env                        # Local secrets (gitignored)
├── one-time-setup.ps1          # Windows one-time DNS + HTTPS setup
├── sync-dns.sh                 # Auto-sync domains to Windows hosts
├── sync-dns.bat                # Windows batch wrapper for sync-dns.sh
├── setup-auto-dns.ps1          # Windows scheduled task setup
├── traefik/                    # Reverse proxy + TLS certs
├── homer/                      # Service dashboard (homer.local)
├── prometheus/                 # Metrics scrape config
├── grafana/provisioning/       # Auto-configured datasources + dashboards
├── duckdb/                     # Analytics DB + ETL scripts
├── etl-pipeline/               # Standalone ETL container
├── data-lake/                  # Data-lake image and streaming workers
├── adguard/                    # DNS filtering config
├── ansible/                    # Infrastructure playbook
├── loki/                       # Log aggregation config
├── coredns/Corefile            # DNS server config
├── tempo/tempo.yml             # Distributed tracing config
├── synapse/                    # Matrix server config (generated)
├── frappe/                     # Isolated Frappe suite deployment boundary (planned local)
└── README.md
```

## Learning Path

### Phase 1: Infrastructure Basics (Week 1-2)
- Docker Compose orchestration (40 services)
- Reverse proxy routing (Traefik)
- Service discovery via Docker labels
- Network isolation & DNS

### Phase 2: Data Engineering (Week 2-4)
- Time-series metrics (Prometheus)
- Analytics database (DuckDB)
- Dashboard visualization (Grafana)
- ETL pipeline patterns

### Phase 3: DevOps & CI/CD (Week 4-7)
- Self-hosted Git (Gitea)
- CI/CD pipelines (Woodpecker)
- Config management (Ansible)

### Phase 4: Advanced Domains (Week 7-10)
- Data lake patterns (MinIO / S3, Parquet, Iceberg)
- Streaming patterns (Redpanda, Avro, Schema Registry)
- Bounded orchestration labs (CLI workers; Prefect optional)
- DNS filtering (AdGuard Home)

### Phase 5: Security, DBs, Messaging (Week 10-14)
- Secrets management (Vaultwarden)
- PKI/mTLS (Step CA)
- Vulnerability scanning (Trivy)
- Multiple database engines (Valkey, InfluxDB, Qdrant, Postgres)
- Messaging patterns (NATS, MQTT, AMQP)

### Phase 6: Networking, ML, Observability (Week 14+)
- Programmable DNS (CoreDNS)
- Auto-TLS (Caddy)
- Local LLM inference (Ollama)
- Distributed tracing (Tempo)

## Common Commands

```bash
# Start/stop/restart
docker compose up -d
docker compose down
docker compose restart <service>

# Logs
docker compose logs -f <service>
docker logs se-traefik --tail 50

# Resource usage
docker stats --no-stream

# Execute in container
docker exec -it se-prometheus sh

# Update all images
docker compose pull && docker compose up -d

# Backup a volume
docker run --rm -v solo-empire-self-hosted-stack_duckdb-data:/data -v $(pwd):/backup alpine tar czf /backup/duckdb-backup.tar.gz /data
```

## Observability Integrations

```
Docker logs → Loki → Grafana (only when a log shipper is explicitly enabled)
Prometheus → scrapes the enabled metrics targets → Grafana (metrics)
Grafana datasources: Prometheus + Loki + Tempo (traces)
```

**Prometheus fixed scrape targets:** prometheus, node-exporter, traefik, loki, influxdb, tempo
**Prometheus optional target:** `solo-empire-mlops-reference` via the empty-by-default file-SD target file

**Grafana datasources:** Prometheus (metrics), Loki (logs), Tempo (traces) — all auto-provisioned

**Log shipping:** No Vector container is enabled in the current Compose file; Loki remains available for an explicitly approved log-shipping exercise.

## Known Issues

- **Data Lake** is an optional profile; do not start it with every other data service

## Cloud Alternatives

| Self-Hosted | Cloud Alternative | Free Tier | Recommendation |
|-------------|-------------------|-----------|----------------|
| Grafana | Grafana Cloud | 3 users, 10 dashboards | Use cloud |
| Loki | Grafana Cloud Logs | 50GB/month | Use cloud |
| Prometheus | Grafana Cloud Metrics | 10K series | Keep self-hosted |
| DuckDB | MotherDuck | 10GB free | Try cloud |
| Traefik | Cloudflare | Already using | Already using |
| MinIO | AWS S3 / Cloudflare R2 | Provider-dependent | Keep MinIO for local learning only |
| Healthchecks | Healthchecks.io | Free | Already using |

---

**Location:** `infra/self-hosted-stack/` (relative to monorepo root)

**Updated:** 2026-08-07

**Status:** Local learning lab (Compose). Production path: `infra/platform/` Kubernetes + GitOps.

## Local documents

- [Exercises](EXERCISES.md)
- [Heavy Services](HEAVY-SERVICES.md)
