# 09 — ERD

repo ไม่มี migration หรือ ORM ของตัวเอง ข้อมูล persisted ที่ repo **define หรือเขียน** มีสองกลุ่ม:

1. Frappe records ที่ custom app และ script สร้าง/อ่าน (custom field, role, user, permission, snapshot ใน site config)
2. MinIO lake prefix layout ที่ policy JSON ผูกสิทธิ์ไว้

ข้อมูลของ third-party services อื่น (Gitea, Vaultwarden, Postgres ฯลฯ) อยู่ใน named volumes โดย schema เป็นของ upstream — ดู data-store map ใน [14-backup-dr.md](14-backup-dr.md)

## A. Frappe entities ที่ repo แตะ

```mermaid
erDiagram
    COMPANY ||--o{ SALES_INVOICE : "company"
    SALES_INVOICE }o--o| FX_SNAPSHOT : "custom_fx_snapshot_id"
    CURRENCY_EXCHANGE_SETTINGS ||--o{ SALES_INVOICE : "disabled must be 1 for non-base"
    ROLE ||--o{ CUSTOM_DOCPERM : "role"
    USER ||--o{ HAS_ROLE : "roles"
    ROLE ||--o{ HAS_ROLE : "role"
    CUSTOM_DOCPERM }o--|| DASHBOARD_DOCTYPE : "parent"

    COMPANY {
        string name PK
        string default_currency
    }
    SALES_INVOICE {
        string name PK
        string company FK
        string currency
        decimal conversion_rate
        string custom_fx_snapshot_id "Data, read_only, no_copy"
    }
    CURRENCY_EXCHANGE_SETTINGS {
        int disabled "single doctype"
    }
    FX_SNAPSHOT {
        string snapshot_id PK "key in site conf solo_fx_approved_snapshots"
        string base_currency
        string quote_currency
        decimal rate
        string quality "must be verified"
        string source_type "must be reference"
        string source_ref
        string reviewed_by
        string as_of "ISO with Z"
        string captured_at "ISO with Z"
        string reviewed_at "ISO with Z"
    }
    ROLE {
        string role_name PK "Solo Empire Dashboard Reader"
        int is_custom
        int desk_access
        int disabled
    }
    USER {
        string email PK "named reader user"
        int enabled
        string user_type "System User"
    }
    HAS_ROLE {
        string parent FK
        string role FK
    }
    CUSTOM_DOCPERM {
        string parent FK
        string role FK
        int read
        int write
        int create
        int delete
        int submit
        int cancel
        int amend
        int share
    }
    DASHBOARD_DOCTYPE {
        string name PK "CRM Lead, CRM Deal, Customer, Sales Invoice, Project, ToDo"
    }
```

Sources: `infra/self-hosted-stack/frappe/custom-apps/solo_empire_fx_guard/solo_empire_fx_guard/fx_guard.py`, `.../install.py`, `infra/scripts/sync/frappe_dashboard_reader.py` (`DASHBOARD_DOCTYPES`, `run`, `verify_token`), `infra/tests/integrations/frappe_fx_guard_test.py` (snapshot fields)

## B. Projection identity fields (catalog, Frappe)

`SOURCE-ID-FIELDS.yaml` ระบุ custom fields 3 ตัวบน `CRM Lead` (source `opportunities`), `Customer` (source `clients`), `CRM Deal` (source `crm_deals`) โดย `SECURITY-READINESS.md` ระบุว่า "created on `CRM Lead`, `Customer`, and `CRM Deal`" — แต่ใน repo นี้ไม่มีโค้ดที่สร้าง fields เหล่านี้

```mermaid
erDiagram
    CRM_LEAD {
        string custom_solo_empire_source_id "unique per doctype"
        string custom_solo_empire_source_table "opportunities"
        string custom_solo_empire_contract_version "frappe-projection.v1"
    }
    CUSTOMER {
        string custom_solo_empire_source_id "unique per doctype"
        string custom_solo_empire_source_table "clients"
        string custom_solo_empire_contract_version "frappe-projection.v1"
    }
    CRM_DEAL {
        string custom_solo_empire_source_id "unique per doctype"
        string custom_solo_empire_source_table "crm_deals"
        string custom_solo_empire_contract_version "frappe-projection.v1"
    }
```

Sources: `infra/self-hosted-stack/frappe/SOURCE-ID-FIELDS.yaml`, `infra/self-hosted-stack/frappe/SECURITY-READINESS.md`

## C. Lake object layout ที่ MinIO policies ผูกไว้

```mermaid
flowchart TD
    B["bucket solo-empire-portfolio, prefix lake/"] --> L["landing/"]
    B --> BR["bronze/"]
    B --> SI["silver/"]
    B --> GO["gold/"]
    B --> CT["control/"]
    CT --> CK["checkpoints/"]
    CT --> MF["manifests/ source=*, stream/, stream-parquet/ and derived"]
    CT --> QU["quarantine/"]
    I(["lake-ingest"]) -->|"Get, Put"| L
    I -->|"Get, Put"| BR
    I -->|"Get, Put"| CK
    I -->|"Get, Put"| QU
    TR(["lake-transform"]) -->|"read"| BR
    TR -->|"write"| SI
    TR -->|"write"| GO
    C(["lake-consumer"]) -->|"list, read"| GO
    O(["lake-operator"]) -->|"bucket setup, bounded recovery"| B
```

Sources: `infra/self-hosted-stack/minio/policies/README.md`, `infra/self-hosted-stack/minio/policies/lake-ingest.json`, `lake-transform.json`, `lake-consumer.json`, `lake-operator.json`, `infra/tests/data_lake/minio_policy_test.py`

## Open questions

- `FX_SNAPSHOT` ไม่ใช่ DocType แต่เป็น dict ใน site config — ผู้เขียน/ผู้ review และ retention ไม่ได้ define
- Policies ถูก apply ใน MinIO ของ lab แล้วหรือยัง (README: "This repository does not create users ... or apply policies automatically")
