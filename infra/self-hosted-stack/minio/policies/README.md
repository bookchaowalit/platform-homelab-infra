---
title: MinIO Data Lake Policies
tags: [data-lake, minio, access-control, least-privilege]
created: 2026-09-08
updated: 2026-09-08
description: Reviewable MinIO policy artifacts for the local lake lab and the canonical portfolio bucket prefix.
status: current
---

# MinIO data-lake policies

These JSON documents are the reviewable least-privilege baseline for the
canonical `solo-empire-portfolio/lake` bucket prefix:

| Policy | Intended identity | Scope |
|---|---|---|
| `lake-ingest.json` | `lake-ingest` | Immutable landing/Bronze/checkpoint/ingest-manifest/quarantine writes and idempotent reads |
| `lake-transform.json` | `lake-transform` | Bronze/lineage reads plus Silver/Gold and derived-manifest writes |
| `lake-consumer.json` | `lake-consumer` | Gold-only list/read |
| `lake-operator.json` | `lake-operator` | Bucket setup and bounded object recovery; never an application identity |

The policies deliberately do not grant `s3:*`, public access, object delete to
application roles, or access to credentials. `HeadObject` is covered by
`s3:GetObject` in the S3 policy model; this is needed for immutable retry
checks. `lake-transform` can read existing Silver/Gold objects only to verify
an idempotent output key, not to publish a second serving contract.

## Apply gate

This repository does not create users, generate passwords, or apply policies
automatically. Before applying, an operator must approve the bucket name and
prefix, provision identities through the secret-management boundary, and run
the offline policy test:

```bash
task test:data-lake
```

For the local lab, use the root credential only for the one-time administrative
operation. The Compose service intentionally does **not** publish the S3 API
port on the host, so run `mc` from a client attached to the Compose
`solo-empire-net` network and address the service as `http://se-minio:9000`.
Keep the values in the ignored environment/secret manager and pass them to
`mc` through the process environment; never paste or commit them:

```bash
mc alias set local http://se-minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
mc admin policy create local lake-ingest infra/self-hosted-stack/minio/policies/lake-ingest.json
mc admin policy create local lake-transform infra/self-hosted-stack/minio/policies/lake-transform.json
mc admin policy create local lake-consumer infra/self-hosted-stack/minio/policies/lake-consumer.json
mc admin policy create local lake-operator infra/self-hosted-stack/minio/policies/lake-operator.json
```

Attach a policy to a short-lived, workload-specific MinIO identity only after
review. Do not attach `lake-operator` to a pipeline, API, consumer, or worker.
The local Compose MinIO service remains a learning/integration target; these
artifacts are not evidence that a hosted R2/S3 policy has been applied.
