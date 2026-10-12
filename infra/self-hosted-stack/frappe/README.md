---
title: Frappe Self-hosted Boundary
description: Deployment boundary and local operating rules for the internal Frappe suite
updated: 2026-09-10
status: internal-development-validated
tags: [infra, self-hosted, frappe, docker, boundary]
related: [../../../operations/commercial/frappe/README, ../../README]
---

# Frappe Self-hosted Boundary

This directory owns deployment notes and future local configuration for the
internal Frappe suite. It is a separate stateful application boundary from the
main Solo Empire Compose lab.

## Ownership

- Upstream container orchestration: official [`frappe_docker`](https://github.com/frappe/frappe_docker)
- Commercial operating model: [`operations/commercial/frappe/`](../../../operations/commercial/frappe/README.md)
- Runtime data: dedicated ignored Docker volumes or machine-local storage
- Secrets: configured secret manager or ignored local environment
- Integration code: `infra/` after the data contract is approved

Do not put a populated Frappe bench, `sites/`, uploads, database files, or
credentials in Git. Do not attach Frappe to the main Solo Empire SQLite file.

## Current status

The local internal-development candidate is running from a custom image built
from the pinned app manifest. The site passed install, migration, login,
authenticated route, backup, and restore checks. The image includes the narrow
LMS SQLite search compatibility patch in the tracked Containerfile.
This is not production approval; role, secret, network, data-contract, and
upgrade review remain before an internal pilot.
See the [deployment contract](../../../operations/commercial/frappe/DEPLOYMENT.md)
and [app matrix](../../../operations/commercial/frappe/APP-MATRIX.md).
The current role baseline is in [ROLE-PROFILES.yaml](ROLE-PROFILES.yaml), and
the security promotion gates are in [SECURITY-READINESS.md](SECURITY-READINESS.md).
The future projection identity fields are cataloged in
[SOURCE-ID-FIELDS.yaml](SOURCE-ID-FIELDS.yaml); they do not contain source
records or secrets.
The private/offline exchange-rate boundary is documented in the
[Frappe exchange-rate policy](../../../operations/commercial/frappe/EXCHANGE-RATE-POLICY.md);
it is fail-closed and is not applied to the main site without an explicit
owner decision.
The reviewed `solo_empire_fx_guard` custom app is packaged under
[`custom-apps/solo_empire_fx_guard/`](custom-apps/solo_empire_fx_guard/); its
`before_submit` hook was verified on a disposable site. The local candidate
image `solo-empire-frappe:16-candidate-fx-guard` is running on the site, with
`solo_empire_fx_guard`, `crm`, `telephony`, `helpdesk`, `payments`, and `lms`
installed. HRMS remains pending a documented privacy boundary for personnel and
payroll data.

## Local development access

- URL: http://127.0.0.1:8090
- Site: solo-empire.localhost
- Credentials: ignored local file `.runtime/credentials.txt`
- Start: `docker compose --env-file .runtime/compose.env --project-name solo-empire-frappe -f compose.yaml up -d`
- Status: `docker compose --env-file .runtime/compose.env --project-name solo-empire-frappe -f compose.yaml ps`
- Stop without deleting volumes: `docker compose --env-file .runtime/compose.env --project-name solo-empire-frappe -f compose.yaml stop`

## Candidate release train

- [`apps.json.example`](./apps.json.example) — official Frappe Docker custom-app
  manifest shape, with public repositories and candidate branches.
- [`APP-LOCK.yaml`](./APP-LOCK.yaml) — commit snapshot and compatibility status.

The lock is validated for the local internal-development candidate. It is not
production or internal-pilot approval; role, secret, network, data-contract,
and upgrade review remain before promotion.
