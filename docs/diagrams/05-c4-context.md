# 05 — C4 Context

ระบบ = "Homelab stack" (repo นี้) ซึ่งรันบนเครื่อง lab ของ owner เท่านั้น ระบบภายนอกคือสิ่งที่ config/script ติดต่อจริง

```mermaid
C4Context
    title Homelab stack - system context
    Person(owner, "Lab owner", "Runs compose profiles, scripts and Frappe on own machine")
    System(lab, "Homelab stack", "Docker Compose lab with 84 services in profiles, plus a separate Frappe/ERPNext project")
    System_Ext(registries, "Container registries", "Docker Hub, ghcr.io, quay.io, gcr.io, Redpanda registry")
    System_Ext(dns, "Public DNS resolvers", "CoreDNS forwards non-local names")
    System_Ext(github, "GitHub", "Repo, Actions CI, OAuth provider for oauth2-proxy")
    System_Ext(sharedci, "platform-ci-workflows", "Reusable CI and security workflows pinned by SHA")
    System_Ext(renovate, "Renovate", "Dependency update PRs")
    System_Ext(winhost, "Windows host", "hosts file, trust store, WARP split DNS")
    System_Ext(frappeup, "Frappe upstream repos", "Framework and app commits in APP-LOCK")
    Rel(owner, lab, "Starts, browses via HTTPS service.local")
    Rel(lab, registries, "Pulls images")
    Rel(lab, dns, "Forwards DNS queries")
    Rel(lab, github, "oauth2-proxy GitHub provider")
    Rel(owner, winhost, "Runs PowerShell setup as Administrator")
    Rel(github, sharedci, "ci.yml calls")
    Rel(renovate, github, "Opens PRs")
    Rel(lab, frappeup, "Image built from pinned app commits")
```

Sources: `infra/self-hosted-stack/docker-compose.yml` (images, `oauth2-proxy` env), `infra/self-hosted-stack/coredns/Corefile` (`forward`), `.github/workflows/ci.yml`, `renovate.json`, `infra/self-hosted-stack/one-time-setup.ps1`, `infra/self-hosted-stack/frappe/APP-LOCK.yaml`, `infra/self-hosted-stack/frappe/compose.yaml`, `PRODUCT.md`

## หมายเหตุ

- ไม่มี hosted runtime: ไม่มี Railway / Vercel / Cloudflare deploy และไม่มี Sentry (`PRODUCT.md` Sentry waiver)
- Homer dashboard (`homer/config.yml`) มีกลุ่มลิงก์ "Homelab K3s" ไปยัง services ภายนอก repo (NetBox, AI Doc Assistant, BooknBook, Platform Smoke) — เป็นแค่ลิงก์ ไม่มี dependency ระดับ runtime จึงไม่วาดเป็นระบบภายนอก (host ของลิงก์เป็น private address จึงไม่คัดลอกมา)
- `traefik.yml` ไม่มี ACME resolver; volume `traefik-certs:/letsencrypt` ถูก mount แต่ไม่มี config ที่ใช้ จึงไม่วาด Let's Encrypt

## Open questions

- K3s homelab ที่ Homer ลิงก์ไปถูกจัดการด้วย repo ไหน
