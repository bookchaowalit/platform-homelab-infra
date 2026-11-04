# ADR-0003 — Frappe/ERPNext as a separate Compose project with a fail-closed FX guard app

- Status: accepted (retro-documented)
- Date: 2026-11-04

## Context

Frappe เป็น stateful application ที่มี DB, Redis และ workers ของตัวเอง และใช้สำหรับงาน commercial/finance ในอนาคต การแลกเปลี่ยนเงินตราต้องไม่ดึง rate จากภายนอกโดยไม่ได้ตรวจ

## Decision

- แยก Frappe เป็น Compose project `solo-empire-frappe` (`frappe/compose.yaml`, network `solo-empire-frappe-network`) ตามรูปแบบ official `frappe_docker`; frontend publish `127.0.0.1:8090` เท่านั้น
- Pin framework และ apps ด้วย commit ใน `APP-LOCK.yaml`; สร้าง custom image ด้วย `Containerfile` ที่ patch LMS `build_index` และ COPY custom app
- Custom app `solo_empire_fx_guard` hook `before_submit` ของ Sales Invoice: invoice ที่ไม่ใช่ base currency ต้องมี `custom_fx_snapshot_id` ที่ชี้ไป snapshot ใน site config, external lookup ต้องปิด, observation ต้อง verified, มี provenance, เวลาเรียงถูกและไม่เกิน 24 ชั่วโมง, rate ต้องเท่ากัน มิฉะนั้น `frappe.throw(<reason code>)`
- ติดตั้ง app บน site เป็น explicit operator action (ไม่ auto-install)

## Evidence

- `infra/self-hosted-stack/frappe/compose.yaml`, `Containerfile`, `APP-LOCK.yaml`, `README.md`, `SECURITY-READINESS.md`
- `.../solo_empire_fx_guard/fx_guard.py`, `hooks.py`, `install.py`
- `infra/tests/integrations/frappe_fx_guard_test.py` (7 tests)

## Consequences

- `APP-LOCK.yaml` ระบุ `production_approval: not-approved`; promotion gates ยังเปิดอยู่ ([01-business-process.md](../01-business-process.md) To-Be)
- Frappe compose ไม่ถูก validate ใน CI (มีแค่ main compose)
