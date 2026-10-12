---
title: Frappe Security and Role Readiness
description: Security baseline, role-profile catalog, and promotion gates for the private Frappe candidate.
updated: 2026-09-08
status: candidate-baseline
tags: [frappe, security, roles, privacy, self-hosted, readiness]
parent: Frappe Self-hosted Boundary
related: [README, ROLE-PROFILES]
---

# Frappe Security and Role Readiness

This is the security baseline for the local Frappe candidate. It is an
internal-development control record, not production approval or legal advice.

## Current control evidence

| Control | Evidence | Status |
|---|---|---|
| Local network exposure | Frontend is bound to `127.0.0.1:8090`; database and Redis ports are internal Compose ports | passed |
| Secret boundary | Runtime credentials are in ignored `.runtime/`; no credential values are tracked | passed |
| Administrator access | `Administrator` is retained as break-glass account only; no routine user created | policy set |
| Role baseline | [ROLE-PROFILES.yaml](ROLE-PROFILES.yaml) seeded as Role Profile records without custom permissions | passed |
| Projection identity fields | [SOURCE-ID-FIELDS.yaml](SOURCE-ID-FIELDS.yaml) created on `CRM Lead`, `Customer`, and `CRM Deal` | passed |
| Permission smoke | [PERMISSION-SMOKE.md](../../../operations/commercial/frappe/PERMISSION-SMOKE.md) checked Role Profile/DocType permissions and removed broad HR export role | passed with correction |
| Data minimization | No Solo Empire records have been written to Frappe by the integration | passed |
| Backup/recovery | Main site backup, disposable restore drill, and candidate FX-app backup/restore rehearsal passed; off-host retention/DR remains unverified | passed for candidate; production DR pending |
| Queue/runtime health | Recent queue logs clean after the tracked LMS compatibility patch | passed |
| External exposure | No public domain, webhook, or external client access configured | passed for local candidate |
| Exchange-rate boundary | [Frappe exchange-rate policy](../../../operations/commercial/frappe/EXCHANGE-RATE-POLICY.md) plus disposable installed-hook submit evidence; main site remains `disabled=0` pending owner action | candidate hook verified; not applied |
| Secret manager | Local ignored runtime only; production secret manager not configured | pending |
| Upgrade rehearsal | Not yet completed against the pinned app lock | pending |

## Role profile policy

The candidate uses Frappe's standard roles grouped into the profiles in
[ROLE-PROFILES.yaml](ROLE-PROFILES.yaml). Profiles are a human-readable access
boundary; they do not replace DocType permission review.

| Profile | Intended use | Sensitive boundary |
|---|---|---|
| Solo Empire Owner | Approval and configuration | System Manager; not routine use |
| Solo Empire Commercial | CRM and customer context | No payroll or accounting administration |
| Solo Empire Finance | Accounting and reconciliation | Finance records and tax evidence |
| Solo Empire Delivery | Projects and delivery tasks | No HR/payroll administration |
| Solo Empire Learning | LMS learning and authoring | Learner and course content |
| Solo Empire HR | HRMS and employee records | Restricted personal/payroll data |
| Solo Empire Support | Helpdesk operations | Ticket and support content |

The same person may hold several profiles in a solo-operator setup, but routine
work should use the narrowest profile. No profile should receive `Administrator`
unless it is a temporary break-glass action with a recorded reason.

## Promotion gates

The site may move from local development to an internal pilot only after:

1. Create named non-Administrator users and assign only required profiles.
2. Verify representative read/create/update restrictions for CRM, finance,
   delivery, LMS, HRMS, and Helpdesk.
3. Configure a production-grade secret manager and rotate all candidate
   credentials used during testing.
4. Keep the service private behind an approved network boundary; do not expose
   MariaDB or Redis.
5. Complete the real-source lake-backed projection and target reconciliation;
   source identity reconciliation and the synthetic fixture pipeline have
   already passed.
6. Complete an upgrade rehearsal from the pinned app lock with backup and
   restore verification.
7. Record residual risks and an accountable approval before real records or
   external users are introduced.
8. Apply and evidence the [exchange-rate policy](../../../operations/commercial/frappe/EXCHANGE-RATE-POLICY.md)
   for any non-base-currency workflow; do not rely on ERPNext external lookup
   during a private/offline pilot.

## Review triggers

Re-run this review after an app/framework upgrade, new integration, new user,
permission change, network exposure, data-classification change, incident, or
retention-policy change.
