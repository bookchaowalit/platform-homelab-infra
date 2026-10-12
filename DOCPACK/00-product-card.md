---
title: solo-homelab — Product Card
doc_id: CARD-solo-homelab
doc_type: product-card
verdict: showcase
version: 0.1
date: 2026-10-11
status: ร่างเพื่อพิจารณา
owner: Product owner (Book Dev)
---

# solo-homelab — Product Card

## 1. สรุปคุณค่าในหนึ่งประโยค

ชุด self-hosted สำหรับ lab ที่รวม Traefik, Prometheus, Grafana, Loki, Tempo, Alertmanager, Gatus, Gitea, MinIO, Homer, CoreDNS และ Frappe/ERPNext ไว้ที่เดียว

## 2. ปัญหาและผู้ใช้เป้าหมาย

ต้องมี observability และเครื่องมือทดลองที่รันเองได้โดยไม่เสียค่าคลาวด์ ผู้ใช้คือเจ้าของ

## 3. สิ่งที่ทำได้จริงตอนนี้

- Compose stack ใน `infra/self-hosted-stack/` และ custom app `solo_empire_fx_guard` ใน `frappe/`
- เทสต์ offline (compose validation, Frappe reader/fx guard, MinIO policy) ตาม README; 5 ไฟล์ และ 1 CI workflow

## 4. หลักฐานสถานะ

| รายการ | ค่า |
|---|---|
| Stack | Docker Compose, Frappe/ERPNext |
| Commit | 31 ครั้ง (2026-07-09 ถึง 2026-10-11) |
| ซอร์สโค้ด | 13 ไฟล์ / 1108 บรรทัด |
| เทสต์ | 5 ไฟล์ (ไม่ได้รันในงานนี้) |
| CI | 1 workflow |
| Deploy config | Docker Compose (local); ทะเบียนระบุ exception |
| Live URL | ไม่มี |

## 5. คุณค่าและจุดต่าง

- รันเองได้ ไม่มีค่าบริการ
- **[สมมติฐาน]** ไม่มีมูลค่าขาย

## 6. ช่องว่างสำคัญ

- ข้อมูลรันจริงอยู่ในเครื่อง ไม่ยืนยันว่า stack ทั้งหมดขึ้นอยู่ **[ต้องยืนยัน]**
- โครงสร้าง `infra/...` คงเดิม

## 7. คำตัดสิน

**`showcase`** — หลักฐานทักษะ DevOps/homelab ที่ดี แต่ไม่ใช่ธุรกิจ จะเปลี่ยนเป็น `archive` หากเลิกใช้ lab

## 8. ขั้นต่อไป

1. รัน validation tests ตาม README แล้วบันทึกผล

## การอนุมัติ

| บทบาท | สถานะ | วันที่ | ลงนาม |
|---|---|---|---|
| Product owner (Book Dev) | รอพิจารณา | — | ________ |

## แหล่งข้อมูล

- `README.md`
- `infra/self-hosted-stack/`, `frappe/`
