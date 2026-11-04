# ADR-0005 — Secrets only in ignored local files (.env, frappe/.runtime)

- Status: accepted (retro-documented)
- Date: 2026-11-04

## Context

lab ต้องใช้ credential ของหลาย services แต่ repo เป็น public

## Decision

- Compose อ่าน secret ผ่าน `${VAR}` จาก `infra/self-hosted-stack/.env` ที่ gitignore; repo เก็บแค่ `.env.example` ที่เป็น placeholder
- Frappe ใช้ `--env-file .runtime/compose.env`; credentials และ reader token อยู่ใน `frappe/.runtime/` ที่ gitignore; token file เขียนด้วย mode 600 และ script ไม่พิมพ์ค่า credential
- Generated TLS config `traefik/dynamic/*.yml` gitignore; repo เก็บแค่ public certificates (`traefik/certs/*.crt`)
- CI สแกนด้วย gitleaks (shared `security.yml`) และ `compose_validation_test.py` หา hardcoded password patterns

## Evidence

- `.gitignore` (root) และ `infra/self-hosted-stack/.gitignore`
- `docker-compose.yml` env ทั้งหมดอยู่ในรูป `${...}`
- `infra/scripts/sync/frappe_dashboard_reader.py` (`write_token_file`, docstring "No credential value is printed")
- `infra/self-hosted-stack/frappe/SECURITY-READINESS.md` (Secret boundary passed, Secret manager pending)

## Consequences

- ไม่มี secret manager (Infisical หรืออื่น ๆ) ผูกกับ repo นี้; rotation เป็นงานมือ
- backup ของ `.env` และ `.runtime/` ไม่อยู่ใน `backup.sh`
