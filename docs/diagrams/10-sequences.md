# 10 — Sequences

4 เส้นทางหลัก: (1) เปิด profile ด้วย `lab-up.sh` (2) HTTPS request ไปยัง service ผ่าน Traefik (3) submit Sales Invoice ผ่าน FX guard (4) provision dashboard reader

## 1. Start profiles

```mermaid
sequenceDiagram
    actor Owner
    participant Lab as "scripts/lab-up.sh"
    participant Compose as "docker compose"
    participant Engine as "Docker engine"
    Owner->>Lab: lab-up.sh shared-platform
    alt .env missing
        Lab->>Lab: cp .env.example .env
    end
    Lab->>Lab: validate each profile name against allow-list
    alt unknown profile
        Lab-->>Owner: "Unknown profile", usage, exit 1
    else all known
        Lab->>Compose: --profile shared-platform up -d
        Compose->>Engine: create networks, volumes, containers
        Engine-->>Compose: started
        Lab->>Compose: --profile shared-platform ps
        Compose-->>Owner: container status
    end
```

Sources: `infra/self-hosted-stack/scripts/lab-up.sh`, `infra/self-hosted-stack/docker-compose.yml`

## 2. Browser to a lab service via Traefik

```mermaid
sequenceDiagram
    actor Browser
    participant Hosts as "hosts file (sync-dns.sh)"
    participant Traefik as "traefik 127.0.0.1:443"
    participant Proxy as "docker-socket-proxy"
    participant Svc as "target container"
    Note over Traefik,Proxy: background: Docker provider watches containers and events via http://docker-socket-proxy:2375
    Traefik->>Proxy: GET containers, events (POST and DELETE disabled)
    Proxy-->>Traefik: labels with Host rules
    Browser->>Hosts: resolve service.local
    Hosts-->>Browser: 127.0.0.1
    Browser->>Traefik: HTTP :80
    Traefik-->>Browser: redirect to https (permanent false)
    Browser->>Traefik: HTTPS :443 Host service.local
    Traefik->>Svc: forward to loadbalancer.server.port on solo-empire-net
    Svc-->>Traefik: response
    Traefik-->>Browser: response, access log entry
```

Sources: `infra/self-hosted-stack/traefik/traefik.yml`, `infra/self-hosted-stack/docker-compose.yml` (`traefik`, `docker-socket-proxy`, per-service labels), `infra/self-hosted-stack/sync-dns.sh`, `infra/self-hosted-stack/coredns/Corefile`

หมายเหตุ: CoreDNS ก็ตอบ `*.local` เป็น `127.0.0.1` ได้บน `127.0.0.1:15353` แต่ไม่มี config ใน repo ที่ชี้ระบบ host ให้ใช้ CoreDNS — browser จึง resolve ผ่าน hosts file ตาม `sync-dns.sh`

## 3. Sales Invoice submit with FX guard

```mermaid
sequenceDiagram
    actor User as "Finance user"
    participant Desk as "Frappe frontend and backend"
    participant Hook as "fx_guard.validate_sales_invoice"
    participant DB as "Site DB"
    participant Conf as "site config"
    User->>Desk: Submit Sales Invoice
    Desk->>Hook: before_submit(doc)
    Hook->>DB: get_value Company default_currency
    DB-->>Hook: company_currency
    alt doc.currency differs from company_currency
        Hook->>DB: get_single_value Currency Exchange Settings disabled
        alt disabled is not 1
            Hook-->>Desk: frappe.throw FX_EXTERNAL_LOOKUP_ENABLED
        end
        Hook->>Conf: get solo_fx_approved_snapshots
        Hook->>Hook: look up doc.custom_fx_snapshot_id
    end
    Hook->>Hook: validate_observation(now = server UTC)
    alt any check fails
        Hook-->>Desk: frappe.throw reason code
        Desk-->>User: submit blocked
    else valid
        Hook-->>Desk: return
        Desk-->>User: invoice submitted
    end
```

Sources: `infra/self-hosted-stack/frappe/custom-apps/solo_empire_fx_guard/solo_empire_fx_guard/fx_guard.py`, `.../hooks.py`, `infra/tests/integrations/frappe_fx_guard_test.py`

## 4. Dashboard reader provisioning (`--apply`)

```mermaid
sequenceDiagram
    actor Admin as "Lab owner"
    participant Script as "frappe_dashboard_reader.py"
    participant FS as ".runtime files"
    participant API as "Frappe REST API"
    participant Bench as "docker exec bench"
    Admin->>Script: --apply
    Script->>FS: read credentials.txt
    Script->>API: POST /api/method/login
    Script->>API: inspect state (before)
    Script->>API: GET or create or update Role
    loop 6 dashboard DocTypes
        Script->>Bench: frappe.permissions.add_permission read
    end
    Script->>API: GET or create or update reader User
    Script->>FS: read dashboard-reader.env
    alt token missing or fails verify
        Script->>API: POST generate_keys
        Script->>FS: write token file, chmod 600
    end
    Script->>API: list each DocType with token, list Custom DocPerm
    alt read_all and write_none
        Script-->>Admin: status applied, token_ready true, exit 0
    else
        Script-->>Admin: status blocked with error code, exit 2
    end
```

Sources: `infra/scripts/sync/frappe_dashboard_reader.py`, `infra/tests/integrations/frappe_dashboard_reader_test.py`

## Open questions

- Sequence ของ streaming (`redpanda` → `stream-sink` → Avro → `stream-converter` → Parquet/Iceberg) ไม่ได้วาดละเอียด เพราะโค้ด `/app/data_lake/stream_sink.py` ไม่อยู่ใน repo นี้ (มีแค่ command args ใน compose)
