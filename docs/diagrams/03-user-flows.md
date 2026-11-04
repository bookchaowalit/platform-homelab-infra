# 03 — User flows

ไม่มี UI ของ repo เอง "routes/pages" ในที่นี้คือ CLI entrypoints (`lab-up.sh`, `sync-dns.sh`, `backup.sh`, `frappe_dashboard_reader.py`) และ Traefik Host routers (61 rules รูปแบบ `<service>.local` ใน `docker-compose.yml`) flow แบ่งตาม actor ใน [02-use-cases.md](02-use-cases.md)

## Flow A — Lab owner: เปิด shared platform ครั้งแรก

```mermaid
flowchart TD
    A1["cd infra/self-hosted-stack"] --> A2{".env exists?"}
    A2 -->|"no"| A3["lab-up.sh copies .env.example to .env"]
    A2 -->|"yes"| A4["Use existing .env"]
    A3 --> A5["Edit secrets locally"]
    A4 --> A6["./scripts/lab-up.sh shared-platform"]
    A5 --> A6
    A6 --> A7["docker compose --profile shared-platform up -d, then ps"]
    A7 --> A8{"Host OS"}
    A8 -->|"native Linux"| A9["sudo bash sync-dns.sh updates /etc/hosts"]
    A8 -->|"WSL2"| A10["sync-dns.sh updates Windows hosts via powershell.exe"]
    A9 --> A11["Open https://service.local URL"]
    A10 --> A11
    A11 --> A12{"Resolves?"}
    A12 -->|"no, WARP or mDNS"| A13["fix-warp-dns.ps1 or curl --resolve to 127.0.0.1"]
    A12 -->|"yes"| A14["Traefik routes by Host rule to the container"]
```

Sources: `infra/self-hosted-stack/scripts/lab-up.sh`, `infra/self-hosted-stack/sync-dns.sh`, `infra/self-hosted-stack/fix-warp-dns.ps1`, `infra/self-hosted-stack/PROFILES.md` (DNS section), `infra/self-hosted-stack/docker-compose.yml`

## Flow B — Lab owner: เลือก profile ที่เสี่ยงกว่า (opt-in)

```mermaid
flowchart LR
    B1["Need host Docker control?"] -->|"CI agent, cAdvisor, Uptime Kuma, Trivy"| B2["lab-up.sh shared-platform docker-control"]
    B1 -->|"Portainer, Dozzle"| B3["lab-up.sh docker-admin"]
    B1 -->|"Image auto-update"| B4["lab-up.sh lab-auto-update"]
    B1 -->|"Data exercise"| B5["lab-up.sh core data"]
    B1 -->|"Event streaming"| B6["lab-up.sh streaming"]
    B6 --> B7["redpanda healthy, topic-init completes, sink and converter start"]
```

Sources: `infra/self-hosted-stack/PROFILES.md`, `infra/self-hosted-stack/SERVICE-OWNERSHIP.md`, `infra/self-hosted-stack/docker-compose.yml` (`profiles`, `depends_on` ของ `redpanda-topic-init`, `stream-sink`, `stream-converter`)

## Flow C — Windows admin: one-time setup

```mermaid
flowchart TD
    C1["Run one-time-setup.ps1 as Administrator"] --> C2["If WARP running: write split DNS for .local, restart WARP"]
    C2 --> C3["Install local cert into Windows trust store"]
    C3 --> C4["Disable Secure DNS in Chrome and Edge via policy"]
    C4 --> C5["Sync service.local names into Windows hosts"]
    C5 --> C6["setup-auto-dns.ps1 registers a logon scheduled task that runs sync-dns.sh in WSL"]
```

Sources: `infra/self-hosted-stack/one-time-setup.ps1`, `infra/self-hosted-stack/setup-auto-dns.ps1`, `infra/self-hosted-stack/README.md` (DNS & HTTPS Setup)

## Flow D — Frappe Finance user: submit Sales Invoice

```mermaid
flowchart TD
    D1["Open ERPNext at 127.0.0.1:8090"] --> D2["Create Sales Invoice"]
    D2 --> D3["Submit"]
    D3 --> D4["before_submit: validate_sales_invoice"]
    D4 --> D5{"Invoice currency equals company currency?"}
    D5 -->|"yes"| D6{"conversion_rate equals 1?"}
    D6 -->|"yes"| D9["Submitted"]
    D6 -->|"no"| D10["frappe.throw FX_RATE_MISMATCH"]
    D5 -->|"no"| D7{"External FX lookup disabled and snapshot id set and found?"}
    D7 -->|"no"| D11["frappe.throw reason code"]
    D7 -->|"yes"| D8{"Observation verified, fresh within 24h, rate equal?"}
    D8 -->|"yes"| D9
    D8 -->|"no"| D11
```

หมายเหตุ: app นี้ "not installed on the main site by default" (custom app README) — flow นี้เกิดเฉพาะ site ที่ติดตั้ง app แล้ว

Sources: `infra/self-hosted-stack/frappe/custom-apps/solo_empire_fx_guard/solo_empire_fx_guard/fx_guard.py`, `.../hooks.py`, `.../install.py`, `infra/self-hosted-stack/frappe/custom-apps/solo_empire_fx_guard/README.md`, `infra/self-hosted-stack/frappe/compose.yaml` (frontend port)

## Flow E — Frappe Administrator: provision dashboard reader

```mermaid
flowchart TD
    E1["python infra/scripts/sync/frappe_dashboard_reader.py"] --> E2["Read admin values from ignored .runtime/credentials.txt"]
    E2 --> E3["POST /api/method/login"]
    E3 --> E4{"--apply?"}
    E4 -->|"no"| E5["Report status planned, write_performed false"]
    E4 -->|"yes"| E6["Create or update custom Role"]
    E6 --> E7["docker exec bench add_permission read on 6 DocTypes"]
    E7 --> E8["Create or update reader System User"]
    E8 --> E9{"Existing token verifies read_all and write_none?"}
    E9 -->|"yes"| E12["Status applied, token_ready true"]
    E9 -->|"no"| E10["generate_keys, write .runtime/dashboard-reader.env mode 600"]
    E10 --> E11{"Verify again"}
    E11 -->|"pass"| E12
    E11 -->|"fail"| E13["Status blocked, exit 2"]
```

Sources: `infra/scripts/sync/frappe_dashboard_reader.py`, `infra/tests/integrations/frappe_dashboard_reader_test.py`

## Open questions

- Flow ของ consumer ที่อ่าน token file (`dashboard-reader.env`) อยู่นอก repo นี้ (README อ้าง dashboard `frappe_client.ts`) — ไม่ได้วาดเพราะไม่มีโค้ดที่นี่
- `traefik/dynamic/*.yml` (TLS config) ถูก gitignore จึงยืนยันไม่ได้ว่า cert ที่ Traefik เสิร์ฟคือ `traefik/certs/local.crt`
