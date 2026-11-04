# 01 — Business process (As-Is / To-Be)

repo นี้เป็น Infrastructure-as-Code ของ lab ส่วนตัว ไม่ใช่ service ที่ host อยู่ (`PRODUCT.md`: "It is not hosted anywhere and has no live URL")
"business process" จึงคือขั้นตอนที่ owner ใช้งาน lab: เตรียม secret ใน `.env`, เปิด Compose ตาม profile, sync DNS ของ `*.local`, เข้าใช้ผ่าน Traefik และเปิด Frappe/ERPNext เป็น Compose project แยก

## As-Is (จากโค้ดวันนี้)

```mermaid
flowchart TD
    A["Owner clones repo"] --> B["cp .env.example .env and set local secrets"]
    B --> C{"Which work?"}
    C -->|"shared lab"| D["scripts/lab-up.sh profile ..."]
    C -->|"Frappe ERP"| F1["cd frappe; docker compose --env-file .runtime/compose.env --project-name solo-empire-frappe -f compose.yaml up -d"]
    D --> D1{"Profile known?"}
    D1 -->|"no"| D2["Print usage, exit 1"]
    D1 -->|"yes"| D3["docker compose --profile ... up -d"]
    D3 --> E["sync-dns.sh writes service.local names to hosts file"]
    E --> G["Browser opens https://service.local via Traefik"]
    D3 --> H["Prometheus scrapes, rules evaluate, Alertmanager groups"]
    H --> I["Owner views Grafana dashboards"]
    F1 --> F2["Frontend on 127.0.0.1:8090"]
    F2 --> F3["Sales Invoice submit runs FX guard hook"]
    F2 --> F4["Optional: frappe_dashboard_reader.py --apply creates read-only token"]
    G --> J["Optional manual backup: scripts/backup.sh critical or full"]
    D --> K["lab-up.sh down stops all known profiles"]
```

Sources: `infra/self-hosted-stack/scripts/lab-up.sh`, `infra/self-hosted-stack/sync-dns.sh`, `infra/self-hosted-stack/docker-compose.yml`, `infra/self-hosted-stack/frappe/README.md`, `infra/self-hosted-stack/frappe/compose.yaml`, `infra/self-hosted-stack/frappe/custom-apps/solo_empire_fx_guard/solo_empire_fx_guard/hooks.py`, `infra/scripts/sync/frappe_dashboard_reader.py`, `infra/self-hosted-stack/scripts/backup.sh`, `infra/self-hosted-stack/prometheus/prometheus.yml`, `PRODUCT.md`

### Change process (repo level, As-Is)

```mermaid
flowchart LR
    C1["Edit compose / config / scripts"] --> C2["Push to main or open PR"]
    C2 --> C3["CI: ci.yml scripts + security"]
    C2 --> C4["Compose Validate: docker compose config"]
    C3 --> C5["Green on main"]
    C4 --> C5
    C5 --> C6["Owner pulls on lab machine and restarts profiles by hand"]
```

Sources: `.github/workflows/ci.yml`, `.github/workflows/compose-validate.yml`, `PRODUCT.md` ("The stack is started by hand on the lab machine; nothing deploys from `main`.")

## To-Be (เฉพาะที่ repo docs ระบุ)

ไม่มี `specs/` หรือ `docs/UPGRADE-PLAN.md` และ GitHub issues ว่าง (`gh issue list` คืนค่าว่าง) To-Be ที่มีหลักฐานจึงมาจาก `PRODUCT.md` (Limits), `README.md` (หมายเหตุ) และ promotion gates ของ Frappe ใน `frappe/SECURITY-READINESS.md`

```mermaid
flowchart TD
    T1["data-lake/Dockerfile points to data-lake repo instead of monorepo paths"] --> T2["Lake worker image builds from this repo"]
    T3["Frappe: named non-Administrator users with profiles"] --> T4["Representative permission checks per module"]
    T4 --> T5["Production-grade secret manager, rotate candidate credentials"]
    T5 --> T6["Real-source lake-backed projection and reconciliation"]
    T6 --> T7["Upgrade rehearsal from APP-LOCK with backup/restore"]
    T7 --> T8["Recorded residual risks and accountable approval"]
    T8 --> T9["Internal pilot"]
```

Sources: `PRODUCT.md` (Limits), `README.md` (หมายเหตุ), `.trivyignore.yaml`, `infra/self-hosted-stack/frappe/SECURITY-READINESS.md` (Promotion gates)

## Open questions

- To-Be ของ Compose lab เอง (เช่น ย้ายไป Kubernetes ตามที่ README ของ stack อ้างถึง `infra/platform/`) — path นั้นไม่มีใน repo นี้ จึงไม่ถือเป็น To-Be ที่ยืนยันได้
- จะเก็บ lab นี้เป็น `showcase` ต่อหรือ `archive` (DOCPACK product card ระบุว่า "จะเปลี่ยนเป็น `archive` หากเลิกใช้ lab")
