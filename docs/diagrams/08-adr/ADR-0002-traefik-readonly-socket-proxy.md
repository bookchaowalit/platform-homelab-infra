# ADR-0002 — Traefik ingress via a read-only Docker socket proxy, bound to localhost

- Status: accepted (retro-documented)
- Date: 2026-11-04

## Context

Traefik ใช้ Docker labels เพื่อสร้าง router ต่อ service การ mount host Docker socket ตรงเข้า Traefik ให้สิทธิ์ควบคุม host เต็ม

## Decision

- Traefik อ่าน Docker API ผ่าน `docker-socket-proxy` (tecnativa 0.2.0) ที่ `http://docker-socket-proxy:2375` บน network `solo-empire-docker-control` ที่ `internal: true`; proxy อนุญาตเฉพาะ `CONTAINERS`, `EVENTS`, `INFO`, `NETWORKS` และปิด `POST`, `DELETE`
- Traefik publish แค่ `127.0.0.1:80` และ `127.0.0.1:443`; entrypoint `web` redirect ไป `websecure`; `api.insecure: false`; dashboard ไม่มี router (`traefik.enable=false` บน Traefik เอง)
- `exposedByDefault: false` — service ต้อง opt-in ด้วย label
- services อื่นที่ยังต้องใช้ socket ตรงถูกจำกัดใน allow-list และอยู่หลัง opt-in profiles

## Evidence

- `infra/self-hosted-stack/traefik/traefik.yml`
- `docker-compose.yml` blocks `traefik`, `docker-socket-proxy`, `networks.docker-control-net`
- `infra/tests/platform/compose_validation_test.py` (`Traefik uses the Docker API proxy`, `Docker API control network is internal-only`, allow-list ของ socket consumers)

## Consequences

- ไม่มี auth middleware บน router ใดเลย (ค้น `middleware` ใน compose ไม่พบ) — ความปลอดภัยพึ่งการ bind localhost อย่างเดียว ดู [13-threat-model.md](../13-threat-model.md)
- `cadvisor` mount `/var/run` ทั้ง directory (มี docker.sock อยู่ข้างใน) แต่ไม่อยู่ใน regex ของ test เพราะ test หาเฉพาะ string `/var/run/docker.sock`
