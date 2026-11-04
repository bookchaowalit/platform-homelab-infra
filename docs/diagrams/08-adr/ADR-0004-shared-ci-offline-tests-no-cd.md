# ADR-0004 — Shared reusable CI with offline stdlib tests; no CD

- Status: accepted (retro-documented)
- Date: 2026-11-04 (CI adopted in PR #1 `89f1b84`, 2026-10-17; v1.1.1 in `a6d8aa8`, 2026-10-23)

## Context

repo เป็น public IaC ไม่มี runtime ที่ host อยู่ ต้องการ gate คุณภาพและ security เหมือน repo อื่นของ platform

## Decision

- `ci.yml` เรียก `bookchaowalit/platform-ci-workflows` `ci-python.yml` และ `security.yml` pin ด้วย SHA `87dc5e1c…` (v1.1.1) บน GitHub-hosted runner (repo public)
- `test-command` รัน 5 offline suites ที่ใช้แค่ stdlib (ไม่มี pytest dependency) และ Python 3.11 ให้ตรงกับ lake worker image
- `compose-validate.yml` แยกต่างหาก: `docker compose config --quiet` ด้วย `.env.example` + `compose_validation_test.py`
- Dev tools (ruff, mypy) pin ใน root `uv.lock`; ไม่มี runtime dependencies
- ไม่มี deploy job; Renovate ดูแล action digests และ shared workflow

## Evidence

- `.github/workflows/ci.yml`, `.github/workflows/compose-validate.yml`
- `pyproject.toml`, `uv.lock`, `renovate.json`
- `PRODUCT.md` (What works today)
- `gh run list`: ทุก run บน main สำเร็จ (ดู [22-dora.md](../22-dora.md))

## Consequences

- ไม่มี coverage gate (ไม่ได้ส่ง `coverage-threshold`)
- `main` ไม่มี branch protection / ruleset (`gh api .../branches/main/protection` คืน 404 "Branch not protected", rulesets ว่าง) — CI ไม่ใช่ required check
