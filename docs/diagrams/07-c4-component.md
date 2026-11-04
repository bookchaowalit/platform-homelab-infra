# 07 — C4 Component

โค้ดที่ repo เขียนเองมีสองชิ้น: Frappe custom app `solo_empire_fx_guard` (รันใน Frappe backend) และ script `frappe_dashboard_reader.py` (รันบน host) นอกนั้นเป็น config ของ image ภายนอก ภาพที่ 3 แสดง component ภายใน Prometheus config

## A. FX guard ภายใน Frappe backend

```mermaid
C4Component
    title solo_empire_fx_guard inside the Frappe backend container
    Container_Boundary(backend, "Frappe backend (ERPNext v16 image)") {
        Component(hooks, "hooks.py", "Frappe hooks", "doc_events Sales Invoice before_submit, after_install, before_uninstall")
        Component(adapter, "validate_sales_invoice", "Python", "Reads company currency, Currency Exchange Settings, site conf snapshots")
        Component(core, "validate_observation", "Python, stdlib", "Pair, quality, provenance, time order, 24h freshness, rate equality")
        Component(parse, "timestamp / amount", "Python, stdlib", "Strict Z timestamps, finite positive Decimal")
        Component(install, "install.py", "Frappe custom field API", "Creates or removes custom_fx_snapshot_id on Sales Invoice")
    }
    ComponentDb(sitedb, "Site DB", "MariaDB", "Company, Currency Exchange Settings, Custom Field")
    ComponentDb(conf, "site config", "JSON", "solo_fx_approved_snapshots")
    Rel(hooks, adapter, "before_submit")
    Rel(adapter, core, "calls")
    Rel(core, parse, "calls")
    Rel(adapter, sitedb, "frappe.db.get_value, get_single_value")
    Rel(adapter, conf, "frappe.conf.get")
    Rel(hooks, install, "after_install, before_uninstall")
    Rel(install, sitedb, "create_custom_fields, delete_doc")
```

Sources: `infra/self-hosted-stack/frappe/custom-apps/solo_empire_fx_guard/solo_empire_fx_guard/hooks.py`, `.../fx_guard.py`, `.../install.py`, `.../commands.py` (ไม่มี bench commands)

## B. Dashboard reader provisioning script

```mermaid
C4Component
    title frappe_dashboard_reader.py on the lab host
    Container_Boundary(script, "infra/scripts/sync/frappe_dashboard_reader.py") {
        Component(main, "main", "argparse", "--apply, --json, --base-url, --site, --container, --credentials, --token-file")
        Component(run, "run", "Python", "dry-run report or apply steps")
        Component(client, "FrappeAdminClient", "urllib, cookie jar", "login, get, list, create, update, generate_keys")
        Component(perm, "add_read_permission", "subprocess", "docker exec bench execute add_permission")
        Component(verify, "verify_token", "Python", "read_all on 6 DocTypes, write_none on Custom DocPerm")
        Component(files, "read_key_value_file / write_token_file", "Python", "ignored .runtime files, mode 600")
    }
    System_Ext(frappeapi, "Frappe REST API", "127.0.0.1:8090 by default")
    System_Ext(docker, "Docker CLI", "Frappe backend container")
    Rel(main, run, "calls")
    Rel(run, client, "uses")
    Rel(run, perm, "per DocType")
    Rel(run, verify, "checks token")
    Rel(run, files, "reads credentials, writes token")
    Rel(client, frappeapi, "HTTP")
    Rel(perm, docker, "exec")
```

Sources: `infra/scripts/sync/frappe_dashboard_reader.py`, `infra/tests/integrations/frappe_dashboard_reader_test.py`

## C. Monitoring config components

```mermaid
flowchart LR
    subgraph promcfg["prometheus/prometheus.yml"]
        J1["job prometheus"]
        J2["job node-exporter"]
        J3["job traefik"]
        J4["job loki"]
        J5["job influxdb"]
        J6["job tempo"]
        J7["job solo-empire-mlops-reference via file_sd, empty"]
    end
    subgraph rules["prometheus/rules.yml"]
        G1["infrastructure: 6 rules"]
        G2["traefik: 2 rules"]
        G3["services: 3 rules"]
        G4["mlops-reference: 3 rules"]
        G5["databases: 3 rules"]
    end
    subgraph amcfg["alertmanager/alertmanager.yml"]
        RT["route group_by alertname, severity"]
        RD["receiver default"]
        RC["receiver critical"]
    end
    promcfg --> rules
    rules --> RT
    RT -->|"severity critical"| RC
    RT -->|"severity warning or other"| RD
```

Sources: `infra/self-hosted-stack/prometheus/prometheus.yml`, `infra/self-hosted-stack/prometheus/rules.yml`, `infra/self-hosted-stack/prometheus/mlops-targets.json`, `infra/self-hosted-stack/alertmanager/alertmanager.yml`

## Test-only components

- `infra/scripts/sync/frappe_fx_guard.py` — import shim ที่เพิ่ม `custom-apps/` เข้า `sys.path` เพื่อให้ test รันนอก Frappe
- `infra/scripts/platform/platform_output.py` — `configure_utf8_stdio()` ใช้โดย `compose_validation_test.py`

## Open questions

- ใครเป็นผู้เขียน `solo_fx_approved_snapshots` ลง site config — app "does not fetch rates, write snapshots" (custom app README) จึงเป็นงาน operator ที่ไม่มี tooling ใน repo
