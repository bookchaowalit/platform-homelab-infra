# 15 — CI/CD pipeline

มี 2 workflows ใน `.github/workflows/` และ **ไม่มี CD** (ไม่มี deploy job; `PRODUCT.md`: "nothing deploys from `main`") ทุก job รันบน GitHub-hosted runner เพราะ repo เป็น public

```mermaid
flowchart TD
    subgraph triggers["Triggers"]
        PUSH["push to main"]
        PR["pull_request"]
        PRM["pull_request to main"]
        WD["workflow_dispatch"]
    end

    subgraph ci["ci.yml (concurrency ci-ref, cancel-in-progress)"]
        SCR["job scripts: uses ci-python.yml @ 87dc5e1c, python 3.11"]
        SEC["job security: uses security.yml @ 87dc5e1c"]
    end

    subgraph cip["ci-python.yml job python"]
        P1["Checkout"] --> P2["Set up uv and Python"]
        P2 --> P3["Install: uv sync --frozen --all-extras"]
        P3 --> P4["Lint: Ruff check + format check"]
        P4 --> P5["Typecheck: strict mypy from pyproject"]
        P5 --> P6["Test: 5 offline suites"]
        P6 --> P7["Coverage gate: skipped, no threshold input"]
    end

    subgraph secj["security.yml jobs (parallel)"]
        S1["gitleaks"]
        S2["semgrep"]
        S3["osv-scanner"]
        S4["trivy-fs, honours .trivyignore.yaml"]
    end

    subgraph cv["compose-validate.yml job compose-config"]
        C1["Checkout"] --> C2["source .env.example, docker compose config --quiet"]
        C2 --> C3["python3 compose_validation_test.py"]
    end

    PUSH --> ci
    PR --> ci
    WD --> ci
    PUSH --> cv
    PRM --> cv
    SCR --> cip
    SEC --> secj
    ci --> DONE["Status checks on commit or PR, no deploy"]
    cv --> DONE
```

Test suites ใน step Test (จาก `test-command`): `compose_validation_test.py`, `frappe_dashboard_reader_test.py`, `frappe_fx_guard_test.py`, `mlops_observability_test.py`, `minio_policy_test.py`

Sources: `.github/workflows/ci.yml`, `.github/workflows/compose-validate.yml`, `pyproject.toml`, `.trivyignore.yaml`, platform-ci-workflows `.github/workflows/ci-python.yml` และ `.github/workflows/security.yml` @ `87dc5e1c7e0416886a6371d5a101bb2ccba38edd` (อ่านจาก local clone ของ platform-ci-workflows)

## Dependency automation

```mermaid
flowchart LR
    RN["Renovate, before 9am Monday, Asia/Bangkok"] --> G1["group platform-ci-workflows"]
    RN --> G2["pin GitHub Action digests"]
    RN --> G3["python non-major group"]
    RN --> G4["lockFileMaintenance, first day of month"]
    RN --> G5["vulnerability alerts, label security"]
    G1 --> PRS["PR into main, runs ci.yml and compose-validate.yml"]
    G2 --> PRS
    G3 --> PRS
    G4 --> PRS
    G5 --> PRS
```

Sources: `renovate.json`

## Lab-internal CI (not GitHub)

`infra/self-hosted-stack/gitea/.woodpecker.yml` เป็น **ตัวอย่างสำหรับเรียนรู้** ของ Woodpecker ใน lab (lint → test → build เมื่อมี Dockerfile → deploy ที่แค่ `echo`) ไม่ได้ใช้กับ repo นี้ และ step test ใช้ `|| echo "No tests found"` จึงไม่ fail จริง

## Gaps

- `frappe/compose.yaml` และ `frappe/Containerfile` ไม่ถูก validate/build ใน CI
- `data-lake/Dockerfile` ไม่ถูก build (และ build ไม่ได้จาก repo นี้)
- ไม่มี required status checks เพราะ `main` ไม่มี branch protection
