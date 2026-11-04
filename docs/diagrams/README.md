# Core 22 SDLC diagram pack — platform-homelab-infra

ชุดภาพ Core 22 ตาม SDLC Diagram Catalog v2 วาดจากโค้ดและ config ใน repo นี้ (ณ `origin/main` `a6d8aa8`, 2026-10-23; เขียน 2026-11-04)
repo นี้คือ Infrastructure-as-Code ของ lab ส่วนตัว (product name solo-homelab): Docker Compose 84 services แบ่ง 11 profiles ใน `infra/self-hosted-stack/`, Frappe/ERPNext เป็น Compose project แยกพร้อม custom app `solo_empire_fx_guard`, และ stdlib scripts 3 ไฟล์ ไม่มี hosted runtime, ไม่มี live URL, ไม่มี CD

ทุกไฟล์มี `Sources:` ใต้ภาพ และ "Open questions" สำหรับสิ่งที่ยืนยันจากโค้ดไม่ได้ hostnames แบบ `<service>.local` และ private addresses ไม่ถูกคัดลอก (อธิบายเป็นรูปแบบ)

| # | Item | Status | File | Sources read |
|---|---|---|---|---|
| 01 | Business process As-Is / To-Be | done | [01-business-process.md](01-business-process.md) | `lab-up.sh`, `sync-dns.sh`, `docker-compose.yml`, `frappe/README.md`, `PRODUCT.md`, `SECURITY-READINESS.md` |
| 02 | Use cases | done | [02-use-cases.md](02-use-cases.md) | scripts, PowerShell helpers, `ROLE-PROFILES.yaml`, `hooks.py`, `frappe_dashboard_reader.py`, workflows, `renovate.json` |
| 03 | User flows | done | [03-user-flows.md](03-user-flows.md) | `lab-up.sh`, `sync-dns.sh`, `one-time-setup.ps1`, `setup-auto-dns.ps1`, `fx_guard.py`, `frappe_dashboard_reader.py` |
| 04 | Traceability (RTM) | done | [04-traceability.md](04-traceability.md) | `PRODUCT.md`, `infra/tests/**`, workflows, compose, policies README |
| 05 | C4 Context | done | [05-c4-context.md](05-c4-context.md) | compose images/env, `Corefile`, `ci.yml`, `renovate.json`, `APP-LOCK.yaml` |
| 06 | C4 Container | done | [06-c4-container.md](06-c4-container.md) | `docker-compose.yml`, `frappe/compose.yaml`, observability configs |
| 07 | C4 Component | done | [07-c4-component.md](07-c4-component.md) | `solo_empire_fx_guard/*`, `frappe_dashboard_reader.py`, `prometheus.yml`, `rules.yml`, `alertmanager.yml` |
| 08 | ADRs | done (5) | [08-adr/](08-adr/) | compose, `traefik.yml`, `frappe/*`, workflows, `.gitignore`, tests |
| 09 | ERD | done (Frappe entities + lake layout) | [09-erd.md](09-erd.md) | `fx_guard.py`, `install.py`, `frappe_dashboard_reader.py`, `SOURCE-ID-FIELDS.yaml`, `minio/policies/*` |
| 10 | Sequences | done (4) | [10-sequences.md](10-sequences.md) | `lab-up.sh`, `traefik.yml`, compose, `fx_guard.py`, `frappe_dashboard_reader.py` |
| 11 | State machines | done (4) | [11-state-machines.md](11-state-machines.md) | `fx_guard.py`, `frappe_dashboard_reader.py`, compose healthchecks, `rules.yml`, `alertmanager.yml` |
| 12 | API & integrations | done | [12-api-integration.md](12-api-integration.md) | compose ports/env, `traefik.yml`, `prometheus.yml`, Grafana datasources, `frappe_dashboard_reader.py` |
| 13 | Threat model | done | [13-threat-model.md](13-threat-model.md) | compose, `traefik.yml`, `loki.yml`, `tempo.yml`, `SERVICE-OWNERSHIP.md`, `SECURITY-READINESS.md`, tests, `.trivyignore.yaml` |
| 14 | Backup & DR | done | [14-backup-dr.md](14-backup-dr.md) | `scripts/backup.sh`, compose volumes, `frappe/compose.yaml`, `SECURITY-READINESS.md` |
| 15 | CI/CD pipeline | done | [15-cicd-pipeline.md](15-cicd-pipeline.md) | `.github/workflows/*.yml`, platform-ci-workflows `ci-python.yml` / `security.yml` @ `87dc5e1c`, `renovate.json`, `gitea/.woodpecker.yml` |
| 16 | Deployment | done (local only) | [16-deployment.md](16-deployment.md) | compose ports/networks/volumes, `frappe/compose.yaml`, `Containerfile`, DNS scripts |
| 17 | Test coverage matrix | done | [17-test-coverage-matrix.md](17-test-coverage-matrix.md) | `infra/tests/**`, workflows, local run of 5 suites |
| 18 | Git & release workflow | done | [18-git-release-workflow.md](18-git-release-workflow.md) | `git log`, `gh pr list`, `gh api` branch protection + rulesets |
| 19 | Service dependency map | done | [19-service-dependency-map.md](19-service-dependency-map.md) | compose `depends_on`/env, `prometheus.yml`, Grafana datasources, `frappe/compose.yaml`, `gatus/config.yaml` |
| 20 | Observability | done | [20-observability.md](20-observability.md) | `prometheus.yml`, `rules.yml`, `alertmanager.yml`, Grafana provisioning, `loki.yml`, `tempo.yml`, `PRODUCT.md` |
| 21 | Incident response | done (mostly gaps) | [21-incident-response.md](21-incident-response.md) | `alertmanager.yml`, `rules.yml`, stack README, `PROFILES.md`, `backup.sh` |
| 22 | DORA | done (4/5 computed on a merge-to-main proxy; recovery time not computable) | [22-dora.md](22-dora.md) | `git log`, `gh run list`, `gh pr view 1` |

## ADR list

- [ADR-0001](08-adr/ADR-0001-compose-profiles-local-lab.md) Docker Compose + profiles เป็น local-only lab
- [ADR-0002](08-adr/ADR-0002-traefik-readonly-socket-proxy.md) Traefik ผ่าน read-only Docker socket proxy, bind localhost
- [ADR-0003](08-adr/ADR-0003-frappe-separate-project-fx-guard.md) Frappe เป็น Compose project แยก + FX guard แบบ fail-closed
- [ADR-0004](08-adr/ADR-0004-shared-ci-offline-tests-no-cd.md) Shared reusable CI + offline tests, ไม่มี CD
- [ADR-0005](08-adr/ADR-0005-local-ignored-secrets.md) Secrets อยู่แค่ใน ignored local files

## Key gaps found (สรุป)

- Alertmanager receivers ไม่มี integration — alert ไม่ถึงใคร
- ไม่มี auth middleware บน 61 Traefik routers; oauth2-proxy ไม่ได้ผูกกับ router ใด
- `backup.sh` เป็น manual, ไม่ off-host, ไม่เข้ารหัส, อ้าง volumes ที่ไม่มีแล้ว 9 ตัว และไม่ครอบคลุม MinIO / Kestra / Frappe; ไม่มี restore script; RTO/RPO ไม่ได้ define
- `gatus/config.yaml` มีแต่ไม่มี service gatus; rules ฝั่ง database และ container ไม่มี exporter/scrape
- `main` ไม่มี branch protection; Frappe compose และ image ไม่ถูก validate ใน CI
- Stack README/port table และ `backup.sh` ล้าหลัง compose ปัจจุบัน

## Validation

```bash
node ~/work/core22/tools/validate.mjs docs/diagrams/*.md docs/diagrams/08-adr/*.md
```
