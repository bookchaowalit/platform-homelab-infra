# 19 — Service dependency map

Runtime dependencies จาก `depends_on`, env/URL ใน config และ data sources ของ Grafana เส้นทึบ = `depends_on` หรือ connection ที่ config ระบุ, เส้นประ = dependency ที่ config อ้างแต่ไม่มีใน compose

```mermaid
flowchart LR
    subgraph core["core"]
        TR["traefik"]
        DSP["docker-socket-proxy"]
        CD["coredns"]
        HM["homer"]
    end
    subgraph obs["observability"]
        PR["prometheus"]
        AM["alertmanager"]
        GR["grafana"]
        LK["loki"]
        TP["tempo"]
        NE["node-exporter"]
    end
    subgraph dso["devsecops"]
        GT["gitea"]
        WS["woodpecker-server"]
        O2["oauth2-proxy"]
    end
    subgraph dctl["docker-control"]
        WA["woodpecker-agent"]
    end
    subgraph data["data / optional"]
        PG[("postgres")]
        VK[("valkey")]
        PGB["pgbouncer"]
        PGR["postgrest"]
        KE["kestra"]
        IX["influxdb"]
        LM["listmonk"]
        MF["miniflux"]
        UM["umami"]
        OL["outline"]
        FI["firefly"]
        RC["redis-commander"]
        BS["bookstack"]
        BSD[("bookstack-db")]
    end
    subgraph strm["streaming"]
        RP["redpanda"]
        RTI["redpanda-topic-init"]
        SS["stream-sink"]
        SC["stream-converter"]
    end
    subgraph fr["solo-empire-frappe"]
        CFG["configurator"]
        FDB[("db mariadb")]
        RCH[("redis-cache")]
        RQU[("redis-queue")]
        FB["backend"]
        FWS["websocket"]
        FFR["frontend"]
        QS["queue-short, queue-long, scheduler"]
    end
    EXT1["public DNS"]
    EXT2["GitHub OAuth"]
    MLOPS["MLOps reference target"]

    TR --> DSP
    CD --> EXT1
    PR --> NE
    PR --> TR
    PR --> LK
    PR --> TP
    PR --> IX
    PR --> AM
    PR -.->|"file_sd, empty"| MLOPS
    GR --> PR
    GR --> LK
    GR --> TP
    WS --> GT
    WA --> WS
    O2 --> EXT2
    PGB --> PG
    PGR --> PG
    KE --> PG
    LM --> PG
    MF --> PG
    UM --> PG
    OL --> PG
    OL --> VK
    FI --> PG
    RC --> VK
    BS --> BSD
    RTI --> RP
    SS --> RTI
    SC --> RTI
    SS --> RP
    CFG --> FDB
    CFG --> RCH
    CFG --> RQU
    FB --> CFG
    FWS --> CFG
    QS --> CFG
    FFR --> FB
    FFR --> FWS
```

Sources: `infra/self-hosted-stack/docker-compose.yml` (`depends_on`, `woodpecker-*` env, `oauth2-proxy` env, `stream-sink` command), `infra/self-hosted-stack/prometheus/prometheus.yml`, `infra/self-hosted-stack/grafana/provisioning/datasources/prometheus.yml`, `infra/self-hosted-stack/coredns/Corefile`, `infra/self-hosted-stack/frappe/compose.yaml`

## Missing dependencies (rules/config ที่ชี้ไปของที่ไม่มี)

- Rules `PostgresDown`, `PostgresHighConnections` ใช้ `pg_up`, `pg_stat_activity_count` — ไม่มี postgres exporter ใน compose
- Rule `RedisHighMemory` ใช้ `redis_memory_*` — ไม่มี redis exporter
- Rule `ContainerHighMemory` ใช้ `container_memory_*` (cAdvisor) — cAdvisor ไม่ได้อยู่ใน scrape config
- `gatus/config.yaml` มี 79 endpoints แต่ไม่มี service `gatus` ใน compose (และ endpoint Traefik ชี้ไป `:8088` ที่ปิดไว้)
- `backup.sh` อ้าง volumes ของ services ที่ไม่มีแล้ว (ดู [14-backup-dr.md](14-backup-dr.md))

## Open questions

- `stream-sink` / `stream-converter` ใช้ Schema Registry (`:8081`) หรือไม่ — ดูได้จากโค้ดใน data-lake repo เท่านั้น
