# 06 — C4 Container

Compose file มี 84 services, 2 networks (`solo-empire-net` bridge, `solo-empire-docker-control` bridge `internal: true`) และ 70 named volumes ภาพนี้แสดง container หลักของ profile ที่ใช้บ่อย (`core`, `observability`, `devsecops`, `data`, `streaming`) ส่วน `optional` (38 services), `disabled` (4) และ admin/control profiles สรุปเป็นกล่องเดียว

จำนวนต่อ profile (นับจาก `profiles:` ใน compose; service หนึ่งอยู่ได้หลาย profile): optional 38, shared-platform 19, data 12, observability 9, devsecops 7, docker-control 7, core 4, streaming 4, disabled 4, docker-admin 2, lab-auto-update 1

```mermaid
C4Container
    title Homelab stack - containers
    Person(owner, "Lab owner")
    System_Boundary(lab, "Compose project self-hosted-stack") {
        Container(traefik, "traefik", "traefik v3.6", "Ingress on 127.0.0.1:80/443, Host rules per service")
        Container(proxy, "docker-socket-proxy", "tecnativa 0.2.0", "Read-only Docker API on internal network")
        Container(coredns, "coredns", "1.11.1", "Wildcard .local to 127.0.0.1 on 127.0.0.1:15353")
        Container(homer, "homer", "v24.05.1", "Service dashboard")
        Container(prom, "prometheus", "v2.51.0", "Scrapes 7 jobs, 30d TSDB retention")
        Container(am, "alertmanager", "v0.27.0", "Routes default and critical")
        Container(graf, "grafana", "10.4.1", "3 provisioned datasources, 3 dashboards")
        Container(loki, "loki", "2.9.4", "Filesystem log store")
        Container(tempo, "tempo", "2.5.0", "OTLP 4317/4318 on localhost, Jaeger HTTP")
        Container(gitea, "gitea", "1.22.1", "Self-hosted Git")
        Container(wps, "woodpecker-server", "v2.7.0", "CI server linked to Gitea")
        Container(vw, "vaultwarden", "1.32.0", "Password vault")
        ContainerDb(pg, "postgres", "16.3-alpine", "Lab relational DB")
        ContainerDb(minio, "minio", "2024-08-03", "S3 lab, console via Traefik")
        Container(kestra, "kestra", "v0.18.0", "Orchestrator, Postgres repo and queue")
        Container(rp, "redpanda", "v26.2.1", "Kafka API, schema registry, proxy on localhost")
        Container(sink, "stream-sink / stream-converter", "solo-empire-data-lake:local", "Avro sink and Parquet/Iceberg converter")
        Container(others, "optional, docker-control, docker-admin, lab-auto-update", "many images", "Learning tools, host-control tools")
    }
    System_Boundary(fr, "Compose project solo-empire-frappe") {
        Container(ffront, "frontend", "nginx in ERPNext image", "127.0.0.1:8090")
        Container(fback, "backend + workers + scheduler", "ERPNext v16 image", "gunicorn, bench workers")
        ContainerDb(fdb, "db", "mariadb 11.8", "Site database")
        ContainerDb(fredis, "redis-cache / redis-queue", "redis 8.6-alpine", "Cache and queue")
    }
    Rel(owner, traefik, "HTTPS service.local")
    Rel(owner, ffront, "HTTP localhost:8090")
    Rel(traefik, proxy, "Docker discovery, events")
    Rel(prom, am, "Alerts")
    Rel(graf, prom, "PromQL")
    Rel(graf, loki, "LogQL")
    Rel(graf, tempo, "Traces")
    Rel(wps, gitea, "Forge API")
    Rel(kestra, pg, "JDBC")
    Rel(sink, rp, "Consume topic")
    Rel(ffront, fback, "Proxy")
    Rel(fback, fdb, "SQL")
    Rel(fback, fredis, "Cache, queue")
```

Sources: `infra/self-hosted-stack/docker-compose.yml`, `infra/self-hosted-stack/traefik/traefik.yml`, `infra/self-hosted-stack/coredns/Corefile`, `infra/self-hosted-stack/prometheus/prometheus.yml`, `infra/self-hosted-stack/grafana/provisioning/datasources/prometheus.yml`, `infra/self-hosted-stack/grafana/provisioning/dashboards/*.json`, `infra/self-hosted-stack/tempo/tempo.yml`, `infra/self-hosted-stack/loki/loki.yml`, `infra/self-hosted-stack/frappe/compose.yaml`, `infra/self-hosted-stack/PROFILES.md`

## Networks

```mermaid
flowchart LR
    subgraph ctl["solo-empire-docker-control (internal: true)"]
        P["docker-socket-proxy"]
    end
    subgraph app["solo-empire-net (bridge)"]
        T["traefik"]
        S["all other lab services"]
    end
    subgraph frn["solo-empire-frappe-network"]
        F["Frappe services"]
    end
    T --- P
    T --> S
    H[("host Docker socket")] --- P
```

Sources: `infra/self-hosted-stack/docker-compose.yml` (`networks`, `traefik.networks`, `docker-socket-proxy.networks`), `infra/self-hosted-stack/frappe/compose.yaml` (`networks.default.name`)

## ความไม่ตรงกันที่พบ (gaps)

- `README.md` ของ stack และ `gatus/config.yaml` อ้างถึง services ที่ **ไม่มี** ใน compose ปัจจุบัน เช่น Gatus, AdGuard, Synapse, Gotify, Wiki.js, Ollama, Jupyter, Nginx, RabbitMQ (README เองเตือนว่า "current Compose service/profile inventory is the source of truth")
- ตาราง Port Mappings ใน stack README แสดง host ports หลายตัว (เช่น 3004, 5432) แต่ compose publish host ports เฉพาะ traefik, coredns, redpanda และ tempo (ทั้งหมด bind `127.0.0.1`)
- `stream-sink` / `stream-converter` build จาก `data-lake/Dockerfile` ที่ COPY `scripts/data_lake` ซึ่งไม่มีใน repo นี้ (`PRODUCT.md` Limits)

## Open questions

- `woodpecker-server` อยู่ใน `shared-platform` ด้วย แต่ `woodpecker-agent` อยู่แค่ `docker-control` — ใน shared-platform อย่างเดียวจึงไม่มี agent รัน pipeline ตั้งใจหรือไม่
