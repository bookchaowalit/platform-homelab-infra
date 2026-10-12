---
title: "Docker Compose Lab Profiles"
tags: [documentation, infra]
created: 2026-08-03
updated: 2026-09-08
description: "Documentation for Docker Compose Lab Profiles."
---

# Docker Compose Lab Profiles

> Local learning / DevSecOps / data engineering only. Not production.

Do **not** run all ~80 services at once. Use profiles.

## Profiles

| Profile | Count (approx) | Purpose |
|---------|----------------|---------|
| `shared-platform` | 19 | Shared alias for core + observability + DevSecOps tools; no direct Docker socket consumers |
| `core` | 4 | Traefik, CoreDNS, Homer, read-only Docker socket proxy |
| `observability` | 9 | Prometheus, Grafana, Loki, Tempo, Alertmanager, … |
| `devsecops` | 7 | Gitea, Woodpecker server, Step CA, Vaultwarden, … |
| `data` | 14 | PostgreSQL, Valkey, NATS, MinIO, Qdrant, Kestra, Metabase, … |
| `streaming` | 4 | Redpanda, topic bootstrap, Avro sink, and Parquet/Iceberg converter lab |
| `optional` | ~38 | Adminer, search tools, wikis, finance apps, … (no Docker host access) |
| `docker-control` | 7 | Woodpecker server + Agent, Autoheal, Diun, cAdvisor, Uptime Kuma, Trivy (direct host control for selected services) |
| `docker-admin` | 2 | Portainer and Dozzle (direct host control) |
| `lab-auto-update` | 1 | Watchtower (lab only; not for production updates) |
| `disabled` | 4 | Broken/unused experiments (hoppscotch, cryptpad, nitter, breezewiki) |

The `data` profile is a single local lab instance, not a production shared data
plane. See [SERVICE-OWNERSHIP.md](./SERVICE-OWNERSHIP.md) for project boundaries.
Shared DB services (`postgres`, `valkey`, `pgbouncer`) also belong to
**`optional`** for legacy lab compatibility; this does not imply that their
credentials or databases are safe to share across production projects.

## Prerequisites

```bash
cd infra/self-hosted-stack
cp -n .env.example .env   # first time; then set real local secrets
# .env is gitignored — never commit it
```

## Recommended start order

### 0) Shared platform only (recommended default)

```bash
./scripts/lab-up.sh shared-platform
```

This starts the central ingress, observability, CI/CD, security, and local
operations tools without PostgreSQL, Valkey, NATS, MinIO, project data
services, or direct Docker socket consumers. Traefik reaches Docker only via
the read-only proxy on its internal control network.

If a platform exercise genuinely needs host Docker control, opt in explicitly:

```bash
./scripts/lab-up.sh shared-platform docker-control
```

Portainer/Dozzle and Watchtower are separate higher-risk opt-ins:

```bash
./scripts/lab-up.sh docker-admin
./scripts/lab-up.sh lab-auto-update
```

### 1) Core + observability (lightest useful lab)

```bash
docker compose --profile core --profile observability up -d
```

### 2) DevSecOps / CI lab

```bash
docker compose --profile core --profile devsecops up -d
```

### 3) Data engineering lab

```bash
docker compose --profile core --profile data up -d
```

Kestra in the `data` profile requires the Docker socket because its lab task
runner executes Docker jobs. Treat the whole `data` profile as trusted local
control-plane input and never expose its ports publicly.

### 3a) Optional streaming lab

Redpanda and the two lake workers are deliberately isolated from the `data`
profile. Start them only when testing a real Kafka-compatible producer, Avro
contract, consumer group, or Object Storage sink:

```bash
docker compose --profile streaming up -d
```

Host clients use `localhost:19092`; containers on `solo-empire-net` use
`se-redpanda:9092`. The profile bootstraps `se.events` with a 24-hour retention
window, runs the sink continuously, and scans for Avro files for conversion
every 60 seconds. Runtime heartbeats live in the `streaming-state` volume and
are exposed through container healthchecks. The single broker uses a 1-core
development configuration and is not a production availability or durability
boundary.

### 4) Combined local “platform practice” set (legacy lab bundle)

```bash
docker compose \
  --profile core \
  --profile observability \
  --profile devsecops \
  --profile data \
  up -d
```

~40 containers — still far less than the full optional set.

### 5) Optional learning tools (heavier)

```bash
docker compose --profile core --profile data --profile optional up -d
```

## Helper script

```bash
./scripts/lab-up.sh core observability
./scripts/lab-up.sh core observability devsecops data
./scripts/lab-up.sh status
./scripts/lab-up.sh down
```

## What is intentionally NOT here

| Tool | Status on this machine |
|------|------------------------|
| Kubernetes / kubectl / helm | Install separately when you bootstrap a dev cluster |
| Argo CD | Design in `infra/platform/` only — install on a cluster later |
| OpenTofu/Terraform | Design docs only until a cloud provider is chosen |
| Full 80-service `up -d` | Avoid — use profiles |

## Stop / cleanup

```bash
# Stop only this project’s profile set (does not touch other compose projects)
docker compose --profile core --profile observability --profile devsecops --profile data --profile streaming --profile optional --profile docker-control --profile docker-admin --profile lab-auto-update down

# Remove volumes only if you intentionally want a wipe
# docker compose down -v
```

Other projects’ containers (e.g. `scannpop-backend-*`) are separate Compose projects — leave them alone.

## Notes from first bring-up on this machine

- CoreDNS lab port is **`15353`** (host), not `5353` (often already in use).
- Traefik administrative dashboard is disabled; no `:8088` host port is published.
- Kestra uses lab Postgres DB `kestra` + local storage; create DB once if needed:
  `docker exec se-postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c 'CREATE DATABASE kestra;'`
- pgbouncer image is pinned by digest (upstream version tags are sparse).
- Kubernetes / Argo CD / OpenTofu are **not** part of this lab — see `infra/platform/`.

## DNS for `*.local` (browser “site can’t be reached”)

Docker/Traefik can be healthy while the **browser still fails** if `*.local` does not resolve.

This machine may be **native Linux** (not WSL). In that case:

```bash
cd infra/self-hosted-stack
# needs your sudo password once:
sudo bash sync-dns.sh
# or:
sudo sh -c 'grep -q "BEGIN Solo Empire Services" /etc/hosts || cat hosts.solo-empire.fragment >> /etc/hosts'
getent hosts grafana.local
```

Bypass DNS for a one-off test:

```bash
curl -k --resolve grafana.local:443:127.0.0.1 https://grafana.local/
```

Notes:

- `loki.local` / `tempo.local` are API backends (404 on `/` is normal).
- 302 from Grafana/Prometheus/Kestra is usually a login/redirect, not downtime.
- Cloudflare WARP can ignore `/etc/hosts` for browsers; exclude `.local` or pause WARP if needed.
- Windows helper scripts derive the stack directory from their own location (`%~dp0` / `$PSScriptRoot`), so they work wherever homelab is cloned.
