# ADR-0001 — Docker Compose with profiles as a local-only lab

- Status: accepted (retro-documented)
- Date: 2026-11-04 (decision visible since the initial public release `55b34a2`, 2026-10-12)

## Context

repo ต้องเก็บ services สำหรับเรียนรู้ DevOps / data / observability ราว 80 ตัวไว้ที่เดียว บนเครื่อง WSL2 หรือ Linux ของ owner โดยไม่มีค่าคลาวด์ (`DOCPACK/00-product-card.md` §2)

## Decision

ใช้ Docker Compose ไฟล์เดียว (`infra/self-hosted-stack/docker-compose.yml`, 84 services) แบ่งด้วย `profiles:` (core, observability, devsecops, data, streaming, optional, docker-control, docker-admin, lab-auto-update, disabled และ alias `shared-platform`) และเปิดผ่าน `scripts/lab-up.sh` ที่ตรวจชื่อ profile ก่อนรัน ไม่มี service ใดที่ไม่มี profile จึงไม่มีอะไรขึ้นถ้ารัน `docker compose up` เปล่า ๆ ตามที่ header เตือน stack นี้ "NOT production infrastructure"

## Evidence

- `docker-compose.yml` header (lines 1–28) และ `profiles:` ของทุก service
- `infra/self-hosted-stack/scripts/lab-up.sh` (allow-list ของ profile)
- `infra/self-hosted-stack/PROFILES.md`, `SERVICE-OWNERSHIP.md`
- `PRODUCT.md`: "The stack is started by hand on the lab machine; nothing deploys from `main`."
- `compose_validation_test.py` เช็คว่ามี local-lab warning header

## Consequences

- ไม่มี deploy pipeline, ไม่มี uptime SLA, ไม่มี RTO/RPO (ดู [14-backup-dr.md](../14-backup-dr.md))
- เอกสารเก่าใน stack README อ้าง services ที่ถูกถอดไปแล้ว — compose เป็น source of truth
- Production path ที่ README อ้าง (`infra/platform/`, Kubernetes) ไม่อยู่ใน repo นี้
