# 21 — Incident response

repo ไม่มี runbook หรือ on-call และ Alertmanager receivers (`default`, `critical`) **ไม่มี integration** ใด ๆ ดังนั้น "alert channel" ที่มีจริงมีแค่: (1) Alertmanager UI ผ่าน Traefik (2) Grafana dashboards (3) `docker compose ps` health status (4) GitHub Actions failure บน commit/PR flow ด้านล่างเป็นสิ่งที่ทำได้จากเครื่องมือที่มีใน repo พร้อมจุดที่เป็น gap

```mermaid
flowchart TD
    subgraph detect["Detect"]
        A1["Prometheus rule fires, for 1m to 5m"]
        A2["Container unhealthy in docker compose ps"]
        A3["GitHub Actions run fails"]
        A4["Owner notices UI down"]
    end
    A1 --> AM["Alertmanager groups by alertname, severity; critical inhibits warning"]
    AM --> NO["Receiver has no integration: nobody is paged (gap)"]
    NO --> V["Owner opens Alertmanager or Grafana by hand"]
    A2 --> V
    A4 --> V
    A3 --> GH["Owner reads the failed job log on GitHub"]
    V --> T{"Triage"}
    T -->|"one service"| L1["docker compose logs -f service, docker stats"]
    T -->|"host resource"| L2["Grafana System Metrics, node-exporter alerts"]
    T -->|"name does not resolve"| L3["getent hosts, sync-dns.sh, fix-warp-dns.ps1"]
    L1 --> F{"Fix"}
    L2 --> F
    L3 --> F
    GH --> F2["Fix on branch or main, re-run CI"]
    F -->|"config"| F3["Edit compose or config, docker compose restart service"]
    F -->|"bad image"| F4["Pin previous tag in compose, up -d"]
    F -->|"data loss"| F5["Restore from backup.sh archives by hand, no restore script (gap)"]
    F3 --> PM["Postmortem: no template or location in repo (gap)"]
    F4 --> PM
    F5 --> PM
    F2 --> PM
```

Sources: `infra/self-hosted-stack/alertmanager/alertmanager.yml`, `infra/self-hosted-stack/prometheus/rules.yml`, `infra/self-hosted-stack/README.md` (Common Commands), `infra/self-hosted-stack/PROFILES.md` (DNS troubleshooting), `infra/self-hosted-stack/fix-warp-dns.ps1`, `infra/self-hosted-stack/scripts/backup.sh`, `.github/workflows/*.yml`

## Frappe incidents

`SECURITY-READINESS.md` "Review triggers" ระบุให้ re-run security review หลัง "incident" แต่ไม่มีขั้นตอน incident เอง; backup/restore ของ Frappe เป็น drill ที่ทำมือ (ไม่มี script ใน repo)

## Gaps

- ไม่มี notification channel (Telegram/email/webhook) ใน Alertmanager
- ไม่มี runbook, severity matrix, postmortem template
- Autoheal (opt-in) อาจไม่ restart อะไรเลยเพราะไม่มี container ติด label (ดู [11-state-machines.md](11-state-machines.md))

## Open questions

- Lab นี้ต้องการ incident process ไหม หรือยอมรับ "owner ดูเองเมื่อใช้งาน" (ไม่มี production users ตาม `PRODUCT.md`)
