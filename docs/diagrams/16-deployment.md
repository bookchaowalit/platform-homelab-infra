# 16 — Deployment

ไม่มี hosting provider (Vercel / Railway / Cloudflare) และไม่มี public domain — "deployment" คือการที่ owner รัน Compose บนเครื่อง lab เอง (WSL2 หรือ native Linux ตาม `PROFILES.md`) ด้วย `.env` local

```mermaid
flowchart TB
    subgraph win["Windows host (optional, WSL2 setups)"]
        WH["hosts file block BEGIN/END Solo Empire Services"]
        WT["Trust store: local cert CN Local Dev"]
        ST["Scheduled task at logon runs sync-dns.sh"]
        WARP["Cloudflare WARP split DNS for .local, if running"]
    end
    subgraph node["Lab machine: Docker engine"]
        subgraph p1["Compose project self-hosted-stack"]
            N1["net solo-empire-net"]
            N2["net solo-empire-docker-control, internal"]
            TR["traefik: 127.0.0.1:80, 127.0.0.1:443"]
            CD["coredns: 127.0.0.1:15353 udp+tcp"]
            TP["tempo: 127.0.0.1:4317, 4318"]
            RP["redpanda: 127.0.0.1:19092, 18081, 18082, 19644"]
            SK["stream-sink, stream-converter: no host ports"]
            SV["other services: no host ports, reached via Traefik Host rules"]
            VOL[("70 named volumes")]
        end
        subgraph p2["Compose project solo-empire-frappe"]
            FF["frontend: 127.0.0.1:8090"]
            FS["backend, websocket, queue-short, queue-long, scheduler, configurator"]
            FV[("db-data, redis-queue-data, sites, logs")]
        end
        LAKE[("host dir for lake, SOLO_EMPIRE_DATA_LAKE_PATH")]
        ENV[(".env and frappe/.runtime/compose.env")]
    end
    ENV --> p1
    ENV --> p2
    ST --> WH
    WH -->|"service.local to 127.0.0.1"| TR
    RP --> SK
    SK -->|"bind mount"| LAKE
```

Sources: `infra/self-hosted-stack/docker-compose.yml` (`ports`, `networks`, `volumes`, `x-data-lake-runtime`), `infra/self-hosted-stack/frappe/compose.yaml`, `infra/self-hosted-stack/frappe/README.md` (start/stop commands), `infra/self-hosted-stack/sync-dns.sh`, `infra/self-hosted-stack/setup-auto-dns.ps1`, `infra/self-hosted-stack/one-time-setup.ps1`, `infra/self-hosted-stack/hosts.solo-empire.fragment`, `infra/self-hosted-stack/PROFILES.md`

## Environments

| Environment | มีจริงไหม | หลักฐาน |
|---|---|---|
| Local lab | มี | ทั้ง repo |
| CI validation | มี (config only, ไม่รัน containers) | `compose-validate.yml` ใช้ `.env.example` |
| Staging / production | **ไม่มี** | `PRODUCT.md` "not hosted anywhere and has no live URL" |

## Images and build

- Third-party images ดึงจาก registries ตาม tag (pgbouncer ใช้ digest)
- `solo-empire-data-lake:local` build จาก `data-lake/Dockerfile` (context `..`) — ต้องมี `scripts/data_lake` และ `requirements-data-lake.txt` ซึ่งไม่อยู่ใน repo นี้
- Frappe custom image build จาก `frappe/Containerfile` บน base `solo-empire-frappe:16-candidate-payments-lmsfix` (local image, ไม่มีวิธี build base ใน repo); compose ใช้ `${CUSTOM_IMAGE}:${CUSTOM_TAG}` default `frappe/erpnext:v16.31.1`

## Open questions

- Base image `solo-empire-frappe:16-candidate-payments-lmsfix` ถูก build จากที่ไหน (คาดว่าจาก official `frappe_docker` + `apps.json` แต่ไม่มี script ใน repo)
- เครื่อง lab ปัจจุบันเป็น WSL2 หรือ native Linux (`PROFILES.md` บอก "may be native Linux")
