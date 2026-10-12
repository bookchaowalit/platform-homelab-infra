---
title: "Service Ownership Boundaries"
tags: [documentation, infra]
created: 2026-08-03
updated: 2026-09-08
description: "Documentation for Service Ownership Boundaries."
---

# Service Ownership Boundaries

> Local lab policy for separating shared platform tooling from project-owned
> stateful services. This file does not turn the Compose lab into production
> infrastructure and does not migrate existing data.

## Shared platform

These services are intended to be shared by projects in the local lab:

- `core`: Traefik, CoreDNS, Homer, and the read-only Docker socket proxy
- `observability`: Prometheus, Grafana, Loki, Tempo, Alertmanager, exporters,
  Pushgateway, and Graphite (without direct Docker socket consumers)
- `devsecops`: Gitea, Woodpecker server, Step CA, Vaultwarden, OAuth2 Proxy,
  and SpiceDB (without the Docker-backed agent/scanner)
- `docker-control`: Woodpecker server + Agent, Autoheal, Diun, cAdvisor, Uptime
  Kuma, and Trivy; every service in this profile has a direct host-control
  dependency or is coupled to that control-plane and requires explicit opt-in
- `docker-admin`: Portainer and Dozzle; direct Docker API access is isolated
  from the normal `optional` profile
- `streaming`: Redpanda plus the local Avro sink/converter workers for event-
  streaming experiments; it is not the durable data lake or a production
  shared service

Start only this shared layer with:

```bash
./scripts/lab-up.sh shared-platform
```

The `shared-platform` profile is an alias for the shared services above. It
does not start the `data` profile.

## Project-owned data

The following services hold application or project state and must not be
treated as one production database shared by all applications:

| Service | Project boundary |
|---|---|
| PostgreSQL / PgBouncer | Database and role per project; dedicated cluster for critical workloads |
| Valkey | Instance or ACL boundary per project; do not rely on database index alone |
| NATS / Mosquitto | Account, subject/topic, and ACL boundary per project |
| Redpanda | Topic, consumer-group, and ACL boundary per project; 24-hour lab replay window |
| MinIO | Bucket and access-key boundary per project |
| Qdrant | Collection and API-key boundary per project, or dedicated instance |
| InfluxDB | Organization/bucket/token boundary per project |
| PocketBase | Dedicated instance and volume per project |
| PostgREST | Dedicated database role/schema per project |
| Kestra | Namespace/workspace and credentials per project |
| Metabase | Shared UI is possible, but datasource and permissions must be separated |

The Compose `data` profile is a **single local lab instance** of these
services. It is useful for learning and development, but it is not a safe
multi-project production tenancy model. Do not put unrelated production apps
on `se-postgres`, `se-valkey`, or `se-minio` with the same credentials.

## Kubernetes production mapping

For the future Kubernetes platform:

```text
platform namespace
  ingress, Argo CD, observability, policy, certificate, secrets integration

project-a namespace
  app-a, service-a, network policy, project secrets

project-b namespace
  app-b, service-b, network policy, project secrets

managed data layer
  database/schema/user/bucket/queue boundary per project
```

Stateful data should prefer managed PostgreSQL and object storage. A shared
managed database cluster is acceptable for cost control when every project has
its own database/schema, role, credentials, backup scope, and network policy.
Critical or noisy workloads should receive a dedicated database or cluster.

## Non-negotiable boundaries

- Never share database passwords between projects.
- Never grant an application an owner/admin role on a shared database.
- Never expose PostgreSQL, Valkey, NATS, or MinIO directly to the public
  internet.
- Keep project secrets in the project secret store and sync them with
  External Secrets in Kubernetes.
- Backups must be restorable per project, not only as one combined volume.
- This lab remains local-only; no cloud or Kubernetes deployment is performed
  by this ownership change.

## Observed local usage allow-list (2026-09-08)

This is a read-only workstation snapshot, not a production approval and not a
claim that every running container has business data. It records the smallest
useful set to keep available and the stateful services that should remain
on-demand until a project gives them an owner, contract, and data source.

| Boundary | Local decision | Observed state |
|---|---|---|
| Compose lab overall | Do not aim for all services | 43/86 configured services running; 1 topic-init container completed successfully; the rest are stopped by profile design |
| `shared-platform` | Keep available for daily platform work | 19/19 configured services running; metrics/logging are mostly platform signals |
| `data` profile | Start only for a bounded data exercise | 14/14 running; `solo_empire` Postgres is empty, while Kestra has lab flows/configuration |
| `streaming` profile | Start only for an event/lake exercise | Redpanda and workers running; topic has no retained messages and the sink has processed 0 records |
| `docker-control` / `docker-admin` / `lab-auto-update` | Explicit opt-in only | Direct host-control or admin/update boundary; not needed for normal app work |
| Optional/disabled profiles | Leave stopped | Learning experiments; no current evidence of an approved business data consumer |
| Main SQLite control plane | Canonical local operations data | 120/142 tables contain rows; this is the populated operational source, not Compose Postgres |
| `data/lake` | Canonical local lake mirror | 78 files and 21 manifests; approximately 1,955 manifest records |
| `data/lake-local` | Test/dbt projection only | 356 files and 76 manifests; do not merge it into the canonical lake silently |
| Frappe Compose project | Separate application boundary | Installed apps are present, but business doctypes are mostly empty (Customer, Invoice, Employee, Lead, Deal, Project, Course = 0) |
| OpenMetadata | Catalog boundary, currently unpopulated | Entity tables for databases, schemas, tables, pipelines, and glossary terms are 0; provider adapter is disabled |

Stateful containers such as MinIO, Qdrant, NATS JetStream, InfluxDB metrics,
PocketBase business collections, Uptime Kuma monitors, Gitea repositories,
Woodpecker pipelines, and Metabase data sources must therefore be treated as
empty or configuration-only until a later evidence-backed audit says otherwise.
Do not seed synthetic or real business data merely to make a container appear
“used”; create a project-owned intake contract and lake lineage first.
