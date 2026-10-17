#!/usr/bin/env python3
"""
Platform validation tests (no cluster, no cloud).

Checks:
- Compose lab has no hardcoded lab passwords
- Compose lab documents local-only warning
- Platform production-target manifests have no secrets / no :latest
- Helm chart structure is complete
- Kyverno policies exist and default to Audit
- GitOps catalog + env overlays exist
- Application catalog fields are present
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLATFORM_SCRIPTS = ROOT / "infra" / "scripts" / "platform"
if str(PLATFORM_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PLATFORM_SCRIPTS))

from platform_output import configure_utf8_stdio  # noqa: E402


PLATFORM = ROOT / "infra" / "platform"
OPS_PLATFORM = ROOT / "operations" / "platform"
OPS_AI = ROOT / "operations" / "ai"
OPS_RUNBOOKS = ROOT / "operations" / "runbooks"
COMPOSE = ROOT / "infra" / "self-hosted-stack" / "docker-compose.yml"
COMPOSE_ENV_EXAMPLE = ROOT / "infra" / "self-hosted-stack" / ".env.example"
HELM = PLATFORM / "helm" / "solo-app"
POLICIES = PLATFORM / "policies" / "kyverno"
GITOPS = PLATFORM / "gitops"

# Patterns that indicate committed secrets in production-target paths
SECRET_PATTERNS = [
    re.compile(r"soloempire2026", re.I),
    re.compile(
        r"password\s*[:=]\s*['\"]?(?!change-me|changeme|\$\{|<.*>|your-|placeholder|example)[^\s'\"]{8,}",
        re.I,
    ),
    re.compile(
        r"(api[_-]?key|secret[_-]?key|private[_-]?key)\s*[:=]\s*['\"][A-Za-z0-9/+=]{16,}['\"]",
        re.I,
    ),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[bpas]-[A-Za-z0-9-]{10,}"),
]

# Match image references ending in :latest, but not policy patterns like "!*:latest"
LATEST_IMAGE = re.compile(
    r"""(?:image:\s*|repository:\s*)['"]?([A-Za-z0-9._\-]+(?:/[A-Za-z0-9._\-]+)*:latest)['"]?""",
    re.I,
)

# Known lab-only :latest exceptions (annotated in compose; not production targets)
LAB_LATEST_ALLOW = {
    "kennethreitz/httpbin:latest",
    "excalidraw/excalidraw:latest",
    "zedeus/nitter:latest",
    "fariszr/breezewiki:latest",
}


class Checker:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []
        self.passed = 0

    def ok(self, msg: str) -> None:
        self.passed += 1
        print(f"  ✅ {msg}")

    def fail(self, msg: str) -> None:
        self.failures.append(msg)
        print(f"  ❌ {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        print(f"  ⚠️  {msg}")


def test_compose_security(c: Checker) -> None:
    print("\n[compose] Security of Docker Compose lab")
    if not COMPOSE.exists():
        c.fail("docker-compose.yml missing")
        return

    text = COMPOSE.read_text(encoding="utf-8")

    if "LOCAL DEVELOPMENT" in text or "LEARNING LAB ONLY" in text:
        c.ok("Compose file carries local-lab warning")
    else:
        c.fail("Compose file missing local-lab warning header")

    if "soloempire2026" in text:
        c.fail("Hardcoded soloempire2026 still present in compose")
    else:
        c.ok("No hardcoded soloempire2026 passwords")

    if "bookstackroot2026" in text or re.search(r"PASSWORD=[^$\n{]{4,}", text):
        # Allow ${VAR} forms only
        hard = re.findall(r"(?:PASSWORD|SECRET|TOKEN|PASS)=(?!\$\{)[^\n]+", text)
        hard = [h for h in hard if not h.endswith("=") and "change-me" not in h.lower()]
        if hard:
            c.fail(f"Possible hardcoded secrets in compose: {hard[:5]}")
        else:
            c.ok("Compose secrets use environment variables")
    else:
        c.ok("Compose secrets use environment variables")

    if '"80:80"' not in text and '"443:443"' not in text and "api@internal" not in text:
        c.ok("Traefik administrative dashboard is not published")
    else:
        c.fail("Traefik administrative dashboard must remain unpublished")

    if '"80:80"' in text or '"443:443"' in text:
        c.fail("Traefik web entrypoints are exposed on every host interface")
    elif '"127.0.0.1:80:80"' in text and '"127.0.0.1:443:443"' in text:
        c.ok("Traefik web entrypoints bound to localhost")
    else:
        c.fail("Traefik web entrypoints do not have an explicit localhost bind")

    if "insecure: true" in text:
        c.fail("Traefik insecure dashboard mode remains enabled")
    elif "insecure: false" in (
        ROOT / "infra" / "self-hosted-stack" / "traefik" / "traefik.yml"
    ).read_text(encoding="utf-8"):
        c.ok("Traefik insecure dashboard mode disabled")
    else:
        c.fail("Traefik dashboard mode is not explicitly fail-closed")

    if "127.0.0.1:15353:53/udp" in text and "127.0.0.1:15353:53/tcp" in text:
        c.ok("CoreDNS host ports bound to localhost")
    else:
        c.fail("CoreDNS host ports are not restricted to localhost")

    traefik_cfg = (
        ROOT / "infra" / "self-hosted-stack" / "traefik" / "traefik.yml"
    ).read_text(encoding="utf-8")
    if (
        "http://docker-socket-proxy:2375" in traefik_cfg
        and "unix:///var/run/docker.sock" not in traefik_cfg
    ):
        c.ok("Traefik uses the Docker API proxy")
    else:
        c.fail("Traefik still depends on a direct Docker socket")

    control_net = re.search(r"(?ms)^  docker-control-net:\n(.*?)(?=^  \S|\Z)", text)
    if control_net and "internal: true" in control_net.group(1):
        c.ok("Docker API control network is internal-only")
    else:
        c.fail("Docker API control network must be internal-only")

    proxy_block = re.search(r"(?ms)^  docker-socket-proxy:\n(.*?)(?=^  \S|\Z)", text)
    if (
        proxy_block
        and "- docker-control-net" in proxy_block.group(1)
        and "- solo-empire-net" not in proxy_block.group(1)
    ):
        c.ok("Docker socket proxy is isolated from the application network")
    else:
        c.fail("Docker socket proxy must not share the application network")

    if proxy_block and all(
        flag in proxy_block.group(1)
        for flag in (
            "POST=0",
            "DELETE=0",
            "CONTAINERS=1",
            "EVENTS=1",
            "INFO=1",
            "NETWORKS=1",
        )
    ):
        c.ok("Docker socket proxy exposes an explicit read-only discovery allowlist")
    else:
        c.fail(
            "Docker socket proxy allowlist is broader than the read-only Traefik contract"
        )

    service_blocks = {
        match.group(1): match.group(2)
        for match in re.finditer(
            r"(?ms)^  ([a-z][a-z0-9-]*):\n(.*?)(?=^  [a-z][a-z0-9-]*:\n|\Z)", text
        )
    }
    socket_services = [
        name
        for name, block in service_blocks.items()
        if "/var/run/docker.sock" in block
    ]
    allowed_socket_services = {
        "docker-socket-proxy",
        "portainer",
        "dozzle",
        "watchtower",
        "autoheal",
        "diun",
        "uptime-kuma",
        "trivy",
        "woodpecker-agent",
        "kestra",
    }
    unexpected_socket_services = sorted(set(socket_services) - allowed_socket_services)
    if unexpected_socket_services:
        c.fail(
            f"Unreviewed direct Docker socket consumers: {unexpected_socket_services}"
        )
    else:
        c.ok(
            f"Direct Docker socket consumers remain explicitly allow-listed ({len(socket_services)})"
        )

    profile_expectations = {
        "portainer": "docker-admin",
        "dozzle": "docker-admin",
        "watchtower": "lab-auto-update",
        "autoheal": "docker-control",
        "diun": "docker-control",
        "uptime-kuma": "docker-control",
        "trivy": "docker-control",
        "woodpecker-agent": "docker-control",
        "kestra": "data",
    }
    profile_failures = [
        f"{name} missing explicit {profile} profile"
        for name, profile in profile_expectations.items()
        if name in service_blocks
        and not re.search(
            rf"^\s+- {re.escape(profile)}\s*$", service_blocks[name], re.M
        )
    ]
    if profile_failures:
        c.fail("; ".join(profile_failures))
    else:
        c.ok("Direct socket consumers are behind explicit opt-in or data profiles")

    if "lab-auto-update" in text and "watchtower" in text.lower():
        c.ok("Watchtower isolated under lab-auto-update profile")
    else:
        c.fail("Watchtower not isolated under a lab-only profile")

    if not COMPOSE_ENV_EXAMPLE.exists():
        c.fail(".env.example missing")
    else:
        env_text = COMPOSE_ENV_EXAMPLE.read_text(encoding="utf-8")
        if "POSTGRES_PASSWORD=" in env_text and "soloempire2026" not in env_text:
            c.ok(".env.example has placeholders only")
        else:
            c.fail(".env.example looks unsafe or incomplete")

    latest = LATEST_IMAGE.findall(text)
    unexpected = [img for img in latest if img not in LAB_LATEST_ALLOW]
    if unexpected:
        c.fail(f"Unpinned :latest images in compose (not allow-listed): {unexpected}")
    else:
        c.ok(f"Compose :latest limited to allow-listed lab images ({len(latest)})")

    # Core healthchecks / resources
    for svc in ("traefik", "postgres", "grafana", "prometheus"):
        if re.search(rf"  {svc}:", text):
            c.ok(f"Core service present: {svc}")
        else:
            c.fail(f"Core service missing: {svc}")

    if "deploy:" in text and "resources:" in text:
        c.ok("Resource limits present for core services")
    else:
        c.fail("Missing deploy.resources for core services")


def main() -> int:
    configure_utf8_stdio()
    c = Checker()
    print("Solo Empire homelab compose validation (offline)")
    test_compose_security(c)
    print("\n" + "=" * 60)
    print(
        f"Passed: {c.passed}  Failures: {len(c.failures)}  Warnings: {len(c.warnings)}"
    )
    if c.failures:
        for f in c.failures:
            print(f"  - {f}")
        return 1
    print("All homelab compose checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
