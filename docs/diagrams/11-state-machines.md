# 11 — State machines

entities ที่มี lifecycle ในโค้ดของ repo นี้:

1. Sales Invoice submit ที่ถูก FX guard คุม (เฉพาะ transition `before_submit`)
2. ผลของ `frappe_dashboard_reader.py` (`status`: planned / applied / blocked)
3. Container lifecycle ตาม profile + healthcheck / `restart` / `depends_on` conditions ใน compose
4. Prometheus alert (ตาม `for:` ใน rules) และ Alertmanager grouping

## 1. Sales Invoice submit guarded by FX guard

repo ไม่ได้เปลี่ยน lifecycle มาตรฐานของ Frappe (`docstatus`) แต่เพิ่ม guard บน transition Draft → Submitted

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Guard: submit requested
    state Guard {
        [*] --> CurrencyCheck
        CurrencyCheck --> BaseRate: same as company currency
        CurrencyCheck --> LookupCheck: different currency
        LookupCheck --> SnapshotCheck: external lookup disabled
        SnapshotCheck --> ObservationCheck: snapshot id found in site conf
        BaseRate --> Pass: rate equals 1
        ObservationCheck --> Pass: verified, ordered, within 24h, rate equal
    }
    Guard --> Submitted: Pass
    Guard --> Draft: FXRejected reason code via frappe.throw
    Submitted --> [*]
```

Reason codes ที่ `fx_guard.py` ใช้: `FX_CURRENCY_MISSING`, `FX_RATE_MISMATCH`, `FX_SNAPSHOT_MISSING`, `FX_DIRECT_PAIR_REQUIRED`, `FX_SNAPSHOT_UNVERIFIED`, `FX_PROVENANCE_MISSING`, `FX_TIME_ALIGNMENT_INVALID`, `FX_SNAPSHOT_STALE`, `FX_RATE_INVALID`, `FX_EXTERNAL_LOOKUP_ENABLED`

Sources: `infra/self-hosted-stack/frappe/custom-apps/solo_empire_fx_guard/solo_empire_fx_guard/fx_guard.py`, `.../hooks.py`

## 2. Dashboard reader run status

```mermaid
stateDiagram-v2
    [*] --> LoggedIn: credentials read, login ok
    [*] --> blocked: FrappeRequestError, OSError, RuntimeError, SubprocessError
    LoggedIn --> planned: no --apply
    LoggedIn --> Applying: --apply
    Applying --> TokenReused: existing token verifies read_all and write_none
    Applying --> TokenIssued: token missing or not verified
    TokenIssued --> applied: re-verify passes
    TokenIssued --> blocked: re-verify fails
    TokenReused --> applied
    planned --> [*]: exit 0
    applied --> [*]: exit 0
    blocked --> [*]: exit 2
```

Sources: `infra/scripts/sync/frappe_dashboard_reader.py` (`run`, `main`)

## 3. Container lifecycle in the lab

```mermaid
stateDiagram-v2
    [*] --> NotCreated
    NotCreated --> Starting: profile selected in lab-up.sh or compose
    Starting --> Running: no healthcheck
    Starting --> Healthy: healthcheck passes
    Healthy --> Unhealthy: retries exceeded
    Unhealthy --> Healthy: check passes again
    Unhealthy --> Starting: autoheal restart, docker-control only, see note
    Running --> Exited: process exits
    Healthy --> Exited: process exits
    Exited --> Starting: restart unless-stopped
    Exited --> Completed: restart no, e.g. redpanda-topic-init
    Running --> Stopped: lab-up.sh down
    Healthy --> Stopped: lab-up.sh down
    Stopped --> [*]
    Completed --> [*]
```

หมายเหตุ autoheal: ใน compose ไม่มี container ใดติด label `autoheal` และ service `autoheal` ไม่ได้ตั้ง env เปลี่ยน label filter — ถ้า upstream default ยังกรองด้วย label นั้น transition นี้จะไม่เกิดจริง (open question) ในทำนองเดียวกัน `watchtower` ตั้ง `WATCHTOWER_LABEL_ENABLE=true` แต่ไม่มี container ที่ติด label enable

ตัวอย่าง conditions จริง: `redpanda-topic-init` รอ `redpanda: service_healthy`; `stream-sink` และ `stream-converter` รอ `redpanda-topic-init: service_completed_successfully`; `kestra` รอ `postgres: service_healthy`; Frappe `configurator` รอ `db: service_healthy` และ backend services รอ `configurator: service_completed_successfully`

Sources: `infra/self-hosted-stack/docker-compose.yml` (`healthcheck`, `restart`, `depends_on`, `autoheal`), `infra/self-hosted-stack/frappe/compose.yaml`, `infra/self-hosted-stack/scripts/lab-up.sh`

## 4. Prometheus alert lifecycle

```mermaid
stateDiagram-v2
    [*] --> Inactive
    Inactive --> Pending: expr true
    Pending --> Inactive: expr false before for elapses
    Pending --> Firing: expr true for the rule duration, 1m to 5m
    Firing --> Inactive: expr false, resolve_timeout 5m
    Firing --> Grouped: sent to alertmanager
    Grouped --> Notified: group_wait 30s, then receiver default or critical
    Notified --> Grouped: repeat_interval 4h
```

หมายเหตุ: receivers `default` และ `critical` ไม่มี integration (ไม่มี email/webhook/chat config) — state "Notified" จึงไม่ส่งไปที่ใดจริง (gap, ดู [20-observability.md](20-observability.md))

Sources: `infra/self-hosted-stack/prometheus/rules.yml`, `infra/self-hosted-stack/alertmanager/alertmanager.yml`

## Open questions

- Stream sink/converter status files (`/var/lib/solo-empire/state/*.json`) มี state อะไรบ้าง — โค้ดอยู่ใน data-lake repo ไม่ใช่ที่นี่
