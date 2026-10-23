# Product: solo-homelab (platform-homelab-infra)

## What it is

Infrastructure-as-code for the owner's self-hosted lab: a Docker Compose stack in
`infra/self-hosted-stack/` (Traefik, Prometheus, Grafana, Loki, Tempo, Alertmanager, Gatus,
Gitea, MinIO, Homer, CoreDNS) and a Frappe/ERPNext setup in `frappe/` with one custom app,
`solo_empire_fx_guard` (fail-closed FX check on Sales Invoice submit). Plus two stdlib Python
helper scripts in `infra/scripts/` (Frappe dashboard reader, FX guard host import).

## Who it is for

The owner only, on their own machine/lab. It is not hosted anywhere and has no live URL.

## What works today

- `docker compose config` validates the stack with the placeholder `.env.example` (CI job
  `compose-validate.yml`).
- Five offline test suites (compose security checks, Frappe dashboard reader, FX guard,
  MLOps observability config, MinIO lake policies) run in CI.
- Strict mypy and Ruff over the scripts and custom app; dev tools pinned in the root `uv.lock`.
- Shared CI `platform-ci-workflows` v1.1.1 (`ci-python.yml` + `security.yml`).

## Limits

- `infra/self-hosted-stack/data-lake/Dockerfile` still COPYs `scripts/data_lake` from the old
  monorepo, so that image does not build from this repo alone.
- The stack is started by hand on the lab machine; nothing deploys from `main`.
- `.env` and `frappe/.runtime/` are local-only and never committed.

## Status

Active lab infrastructure (showcase verdict in DOCPACK). No production users.

Sentry waiver: IaC and lab compose stack only; nothing here runs as a hosted service, the third-party containers bring their own logging, and the stdlib scripts run by hand.
