# homelab

Self-hosted stack สำหรับ homelab/lab: Docker Compose (Traefik, Prometheus, Grafana, Loki, Tempo, Alertmanager, Gatus, Gitea, MinIO, Homer, CoreDNS) และ Frappe/ERPNext (`frappe/` + custom app `solo_empire_fx_guard`)

ที่มา: ย้ายจาก `solo-empire/infra/self-hosted-stack/` (2026-10-11) พร้อมประวัติ git, ร่วมกับ Frappe sync scripts/tests และ test ของ Prometheus/MinIO ที่อ่านไฟล์ในชุดนี้.
repo นี้คงโครงสร้าง `infra/...` เดิมไว้เพื่อให้ path ใน compose/tests ทำงานเหมือนเดิม.

## ตรวจสอบ (offline)

```bash
python3 infra/tests/platform/compose_validation_test.py
python3 infra/tests/integrations/frappe_dashboard_reader_test.py
python3 infra/tests/integrations/frappe_fx_guard_test.py
python3 infra/tests/mlops/mlops_observability_test.py
python3 infra/tests/data_lake/minio_policy_test.py
cd infra/self-hosted-stack && set -a && . ./.env.example && set +a && docker compose config --quiet
```

Lint และ type check (เหมือน CI, เครื่องมือ pin ไว้ใน `uv.lock` ที่ root — สคริปต์ใช้แค่ stdlib):

```bash
uv sync --frozen --all-extras
uv run ruff check . && uv run ruff format --check .
uv run mypy .   # strict สำหรับสคริปต์และ custom app; test ผ่อนเรื่อง annotation
```

สิ่งที่ repo นี้เป็นและไม่เป็น: [PRODUCT.md](PRODUCT.md)

## หมายเหตุ

- `infra/self-hosted-stack/data-lake/Dockerfile` ยัง COPY `scripts/data_lake` จาก monorepo เดิม — ต้องชี้ไป repo `data-lake` ก่อน build ใหม่
- `.env` / `frappe/.runtime/` เป็นไฟล์ local ห้าม commit; ไม่เคยมี runtime data อยู่ใน solo-empire
- โค้ดที่อ้างพาธ `infra/self-hosted-stack/frappe/.runtime` (เช่น dashboard `frappe_client.ts`) ต้องชี้มา checkout ของ repo นี้
