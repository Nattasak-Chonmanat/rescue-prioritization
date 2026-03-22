# Rescue Prioritization Service

## Service Overview

| | |
|---|---|
| **เจ้าของ** | นายณัฐศักดิ์ ชนมนัส รหัสนักศึกษา 6609611931 ภาคปกติ |
| **GitHub** | https://github.com/Nattasak-Chonmanat/rescue-prioritization.git |

---

## 1. วัตถุประสงค์

Rescue Request Prioritization Service รับผิดชอบการวิเคราะห์และจัดลำดับความสำคัญของคำขอความช่วยเหลือ (Rescue Requests) ระหว่างเหตุการณ์ภัยพิบัติ โดยทำหน้าที่เป็น **Decision Engine** สำหรับกำหนดระดับความเร่งด่วนของแต่ละคำขอ เพื่อสนับสนุนการตัดสินใจของระบบจัดสรรหน่วยกู้ภัย

---

## 2. Pain Point ที่แก้ไข

ในสถานการณ์ภัยพิบัติที่คำขอความช่วยเหลือจำนวนมากเข้ามาพร้อมกัน การประเมินความเร่งด่วนด้วยมนุษย์ใช้เวลานาน อาจเกิด Bias หรือความไม่สม่ำเสมอในการตัดสินใจ บริการนี้จึงถูกออกแบบมาเพื่อ:

- วิเคราะห์และให้คะแนนความเร่งด่วนแบบอัตโนมัติ
- ลดเวลาตัดสินใจ
- เพิ่มความสม่ำเสมอและความโปร่งใสในการจัดลำดับความสำคัญ
- รองรับปริมาณคำขอจำนวนมาก

---

## 3. Target Users

- **Dispatcher** — ใช้จัดลำดับความสำคัญคำขอความช่วยเหลือให้อัตโนมัติ

---

## 4. Service Boundary

### In-scope (รับผิดชอบ)
- ประมวลผลลำดับความสำคัญโดยใช้ AI Model
- จัดเก็บข้อมูลการจัดลำดับความสำคัญ (Prioritization Records)
- ส่งผลลัพธ์ไปยัง Service อื่นแบบ Asynchronous

### Out-of-scope (ไม่รับผิดชอบ)
- การจัดการข้อมูลเหตุการณ์ (Incident Master Data)
- การจัดสรรหน่วยกู้ภัย
- การตัดสินใจเส้นทางการเดินทาง
- การสื่อสารกับผู้ประสบภัยโดยตรง

---

## 5. Autonomy / Decision Logic

บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:
- การกำหนดระดับ Priority ของคำขอ
- การคำนวณ `priority_score` ตาม Model
- การ Re-prioritize ในกรณีข้อมูล Incident เปลี่ยน

การตัดสินใจอิงจาก:

| ปัจจัย | คำอธิบาย |
|---|---|
| `people_count` | จำนวนผู้ได้รับผลกระทบ |
| `incident_type` | ประเภทเหตุการณ์ |
| Life-threatening indicator | ความเสี่ยงต่อชีวิต |
| Incident status | สถานะของ Incident |

บริการสามารถตัดสินใจได้เองภายใต้ Business Rules ที่กำหนด โดยไม่ต้องรอการอนุมัติจากมนุษย์ในกรณีปกติ

---

## 6. Owned Data

### Prioritization Records (Master Data)
ข้อมูลผลลัพธ์การจัดลำดับความสำคัญของแต่ละคำขอ ควรอยู่ภายใต้บริการนี้เพราะ:
- เป็นข้อมูลแกนหลักของ Domain
- บริการนี้เป็นผู้ใช้ข้อมูลดังกล่าวโดยตรง
- เป็นผลลัพธ์โดยตรงของ Decision Logic

---

## 7. Linked Data (Reference Only)

- อ้างอิงจาก **Incident Service** เพื่อระบุว่าคำร้องนี้อยู่ภายใต้เหตุการณ์ภัยพิบัติใด
- บริการนี้**ไม่เก็บสำเนา**ข้อมูล Incident อย่างถาวร

---

## 8. Non-Functional Requirements

| Requirement | รายละเอียด |
|---|---|
| Message Delivery | At-least-once |
| Idempotency | ตรวจสอบ `messageId` เพื่อป้องกันการประมวลผลซ้ำ |
| Duplicate Record | ห้ามสร้าง Prioritization Record ซ้ำ |
| Duplicate Event | ห้ามส่ง Downstream Event ซ้ำ |
| Model Retry | ไม่เกิน 3 ครั้ง |
| Retry Exceeded | ส่ง Message ไปยัง DLQ และบันทึกสถานะเป็น `FAILED` |
| Result Guarantee | 1 Incident → 1 Final Prioritization Result |

---

## 9. Sync Contract

**Base URL:** `http://TBD.com`

---

### API #1 — List Prioritizations by Incident ID

| | |
|---|---|
| **Name** | Get prioritization result by incident |
| **Method** | `GET` |
| **Path** | `/v1/prioritizations/{incident_id}` |
| **Type** | Synchronous |

**คำอธิบาย:** ใช้ค้นหาและกรองผลการจัดลำดับความสำคัญเพื่อให้บริการอื่น (เช่น Dispatch Service หรือ Dashboard) ดึงรายการตามเงื่อนไขที่ต้องการ

#### Request

**Path Parameters**

| Parameter | Type | Required | คำอธิบาย |
|---|---|---|---|
| `incident_id` | UUID | ✅ | รหัสเหตุการณ์ |

**Query Parameters**

| Parameter | Type | Required | Default | คำอธิบาย |
|---|---|---|---|---|
| `priority_level` | string | ❌ | - | `LOW` / `NORMAL` / `HIGH` / `CRITICAL` |
| `status` | string | ❌ | - | `PENDING` / `EVALUATED` / `RE_EVALUATE` / `FAILED` |
| `limit` | integer | ❌ | 20 | จำนวนรายการต่อหน้า |
| `offset` | integer | ❌ | 0 | ตำแหน่งเริ่มต้น |
| `min_score` | decimal | ❌ | - | กรองคะแนนต่ำสุด |
| `max_score` | decimal | ❌ | - | กรองคะแนนสูงสุด |
| `sortBy` | string | ❌ | - | `priorityScore` / `priorityLevel` |
| `sortOrder` | string | ❌ | - | `asc` / `desc` |

**Headers**
```
Accept: application/json
```

**Validation Rules**
- `priority_level` ∈ `{LOW, NORMAL, HIGH, CRITICAL}`
- `status` ∈ `{PENDING, EVALUATED, RE_EVALUATE, FAILED}`
- `min_score`, `max_score` ต้องเป็น Decimal
- `sortBy` ∈ `{priorityScore, priorityLevel}`
- `sortOrder` ∈ `{asc, desc}`

#### Response

**200 OK**
```json
{
  "total": 3,
  "limit": 20,
  "offset": 0,
  "items": [
    {
      "status": "EVALUATED",
      "priority_score": "0.3",
      "request_id": "REQ-8812-1111",
      "idemp_key": "f3d2b2d6-3a9b-4cdb-8c8a-8d0d0a57d0a1",
      "model_id": "gemma-3-27b-it",
      "people_count": "1",
      "incident_id": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",
      "submitted_at": "2026-03-03T08:01:12Z",
      "evaluate_id": "ca6cc85e-0ba3-4d95-9304-690b0d5347c6",
      "description": "ไม่มีอาหารสํารอง",
      "created_at": "2026-03-22T06:51:20.971896+00:00",
      "special_needs": [
        "bedridden",
        "children"
      ],
      "priority_level": "NORMAL",
      "location": {
        "province": "เชียงใหม่",
        "addressLine": "123 ม.2 ถ.ห้วยแก้ว",
        "subdistrict": "test subdistrict",
        "latitude": "11.11",
        "longitude": "22.22",
        "district": "test district"
      },
      "evaluate_reason": "Lack of food reserves indicates a potential need for assistance, but no immediate life-threatening situation is apparent. Location is accessible.",
      "last_evaluated_at": "2026-03-22T06:51:24.145024+00:00",
      "request_type": "flood_rescue"
    },
    ...
```

**400 Bad Request Error**
```json
{
  "message": "Validation failed",
  "errors": [
    "sortOrder must be 'asc' or 'desc'"
  ]
}
```

#### Dependency / Reliability

- ไม่เรียก Service อื่น
- Read-only / Idempotent (GET)
- Timeout: 10s
- รองรับ Pagination

---

### API #2 — Get Prioritization by Request ID

| | |
|---|---|
| **Name** | Search prioritization results |
| **Method** | `GET` |
| **Path** | `/v1/prioritization/request/{request_id}` |
| **Type** | Synchronous |

**คำอธิบาย:** ใช้ค้นหาผลลัพธ์การ Evaluate ของแต่ละ Request

#### Request

**Path Parameters**

| Parameter | Type | Required | คำอธิบาย |
|---|---|---|---|
| `request_id` | string | ✅ | รหัสคำร้อง |

**Headers**
```
Accept: application/json
```

#### Response

**200 OK**
```json
{
  "created_at": "2026-03-22T06:51:20.971896+00:00",
  "description": "ไม่มีอาหารสํารอง",
  "evaluate_id": "ca6cc85e-0ba3-4d95-9304-690b0d5347c6",
  "evaluate_reason": "Lack of food reserves indicates a potential need for assistance, but no immediate life-threatening situation is apparent. Location is accessible.",
  "idemp_key": "f3d2b2d6-3a9b-4cdb-8c8a-8d0d0a57d0a1",
  "last_evaluated_at": "2026-03-22T06:51:24.145024+00:00",
  "location": {
    "province": "test province",
    "addressLine": "test address",
    "subdistrict": "test subdist",
    "latitude": "11.11",
    "longitude": "22.22",
    "district": "test dist"
  },
  "model_id": "gemma-3-27b-it",
  "people_count": "1",
  "priority_level": "NORMAL",
  "priority_score": "0.3",
  "request_id": "REQ-8812-1111",
  "request_type": "flood_rescue",
  "special_needs": [
    "bedridden",
    "children"
  ],
  "status": "EVALUATED",
  "submitted_at": "2026-03-03T08:01:12Z",
  "incident_id": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111"
}
```

**404 Not Found**
```json
{
  "message": "No record found for request_id: REQ-8812-111"
}
```

**500 Internal Server Error**
```json
{
  "message": "Internal server error"
}
```

#### Dependency / Reliability

- ไม่เรียก Service อื่น
- Read-only / Idempotent (GET)
- Timeout: 5s

---

## 10. Async Contract

---

### Message #1 — Rescue Request Prioritize Command

| | |
|---|---|
| **Message Name** | `RescueRequestPrioritizeCommand` |
| **Style** | Event (Pub/Sub) |
| **Producer** | Rescue Request Service |
| **Consumer** | Rescue Request Prioritization Service |
| **Channel** | `rescue.prioritization.commands.v1` |
| **Version** | v1 |

**คำอธิบาย:** Message ถูก Publish โดย Rescue Request Service ผ่าน SNS และส่งต่อไปยัง SQS ของ Prioritization Service เพื่อสั่งให้คำนวณลำดับความสำคัญของ Rescue Request แบบ Asynchronous

#### Message Headers

| Header | คำอธิบาย |
|---|---|
| `messageType` | `RescueRequestPrioritizeCommand` |
| `messageId` | UUID (ใช้เป็น Idempotency Key) |
| `sentAt` | ISO-8601 datetime |
| `traceId` | UUID (สำหรับ Tracing) |
| `version` | `1` |

#### Message Body

```json
{
    "requestId": "REQ-8812-1111",
    "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",
    "requestType": "flood_rescue",
    "description": "ไม่มีอาหารสํารอง",
    "peopleCount": 1,
    "specialNeeds": ["bedridden", "children"],
    "location": {
      "latitude": 11.11,
      "longitude": 22.22,
      "province": "test province",
      "district": "test dist",
      "subdistrict": "test subdist",
      "addressLine": "test address"
    },
    "submittedAt": "2026-03-03T08:01:12Z",
  }
```

#### Field Definition

| Field | Type | Required | คำอธิบาย |
|---|---|---|---|
| `requestId` | String | ✅ | รหัสคำร้อง |
| `incidentId` | UUID | ✅ | รหัสเหตุการณ์ |
| `requestType` | String | ✅ | ประเภทของคําขอ |
| `description` | String | ✅ | คําอธิบายของคําขอ |
| `peopleCount` | Integer | ✅ | จํานวนคนที่ต้องการความช่วยเหลือ |
| `specialNeeds` | String[ ] | ❌ | ความต้องการพิเศษ เช่น มีผู้ป่วยติดเตียง เด็กเล็ก |
| `location` | Object | ✅ | Location Object |
| `location.latitude` | Decimal | ✅ | พิกัดละติจูด |
| `location.longitude` | Decimal | ✅ | พิกัดลองจิจูด |
| `location.province` | String | ❌ | ชื่อจังหวัด |
| `location.district` | String | ❌ | ชื่ออำเภอ |
| `location.subdistrict` | String | ❌ | ชื่อตำบล |
| `location.addressLine` | String | ❌ | ที่อยู่แบบละเอียด |
| `submittedAt` | Datetime | ✅ | เวลาที่คําขอเข้ามาในระบบ |

#### Validation Rules
1. `incident_id` ต้องไม่ว่าง และต้องเป็น UUID format ที่ถูกต้อง
2. `submittedAt` ต้องเป็น ISO-8601 datetime
3. `messageId` ต้อง Unique (ใช้ทำ Idempotency)
4. `location` ต้องมี `lat` และ `lng`

---

### Message #2 — Rescue Request Evaluated Event

| | |
|---|---|
| **Message Name** | `RescueRequestEvaluatedEvent` |
| **Style** | Event (Pub/Sub) |
| **Producer** | Rescue Request Prioritization Service |
| **Consumer** | Dispatch Service (และ Service อื่นที่ Subscribe) |
| **Channel** | `rescue.prioritization.created.v1` |
| **Version** | v1 |

**คำอธิบาย:** Event ถูก Publish หลังจาก Prioritization Service ทำการประเมินลำดับความสำคัญเสร็จ ใช้แจ้งผลลัพธ์ให้ Dispatch Service หรือ Service อื่นนำไปประมวลผลต่อ เป็น Asynchronous Event แบบ Fan-out ผ่าน SNS

#### Message Headers

| Header | คำอธิบาย |
|---|---|
| `messageType` | `RescueRequestEvaluatedEvent` |
| `correlationId` | `messageId` ของ Command ที่รับมา |
| `sentAt` | ISO-8601 datetime |
| `version` | `1` |

#### Message Body

```json
{
  "requestId": "REQ-8812-4444",
  "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",
  "evaluateId": "b26c6606-c16f-4f25-bb4c-3cd1c9f7005f",
  "requestType": "flood_rescue",
  "priorityScore": 0.3,
  "priorityLevel": "NORMAL",
  "evaluateReason": "Lack of food reserves indicates a potential need for assistance, but no immediate life-threatening situation is apparent. Location is accessible.",
  "lastEvaluatedAt": "2026-03-22T07:18:39.670351+00:00",
  "description": "ไม่มีอาหารสํารอง",
  "location": {
    "latitude": 11.111,
    "longitude": 11.222,
    "province": "test province",
    "district": "test dist",
    "subdistrict": "test subdist",
    "addressLine": "test address"
  },
  "peopleCount": 1,
  "specialNeeds": ["bedridden", "children"]
}
```

#### Field Definition

| Field | Type | Required | คำอธิบาย |
|---|---|---|---|
| `evaluateId` | UUID | ✅ | รหัส Evaluation |
| `requestId` | String | ✅ | รหัสคำร้อง |
| `incidentId` | UUID | ✅ | รหัสเหตุการณ์ |
| `requestType` | String | ✅ | ประเภทของคำร้อง |
| `priorityScore` | Decimal | ✅ | คะแนนความสำคัญ (0–1) |
| `priorityLevel` | enum | ✅ | `LOW` / `NORMAL` / `HIGH` / `CRITICAL` |
| `evaluateReason` | String | ✅ | เหตุผลของการประเมิน |
| `submittedAt` | datetime | ✅ | เวลาที่ Request ถูกส่งเข้ามา |
| `lastEvaluatedAt` | datetime | ✅ | เวลาที่ Evaluate เสร็จ |
| `description` | String | ✅ | คำอธิบายของ Request |
| `location` | Object | ✅ | Location Object |
| `location.latitude` | Decimal | ✅ | พิกัดละติจูด |
| `location.longitude` | Decimal | ✅ | พิกัดลองจิจูด |
| `location.province` | String | ❌ | ชื่อจังหวัด |
| `location.district` | String | ❌ | ชื่ออำเภอ |
| `location.subdistrict` | String | ❌ | ชื่อตำบล |
| `location.addressLine` | String | ❌ | ที่อยู่แบบละเอียด |
| `submittedAt` | Datetime | ✅ | เวลาที่คําขอเข้ามาในระบบ |
| `peopleCount` | Integer | ✅ | จํานวนคนที่ต้องการความช่วยเหลือ |
| `specialNeeds` | String[ ] | ❌ | ความต้องการพิเศษ เช่น มีผู้ป่วยติดเตียง เด็กเล็ก |

#### Validation Rules
1. `incidentId` ต้องไม่ว่าง และต้องเป็น UUID format
2. `evaluateId` ต้องเป็น UUID format
3. `priorityScore` ต้องอยู่ในช่วง 0–1
4. `priorityLevel` ∈ `{LOW, NORMAL, HIGH, CRITICAL}`
5. `correlationId` ต้องตรงกับ `messageId` ของ `RescueRequestPrioritizeCommand`
7. `location` ต้องไม่ว่าง

---

### Message #3 — Rescue Request Update Event

| | |
|---|---|
| **Message Name** | `rescue-request.citizen-updated` |
| **Style** | Event (Pub/Sub) |
| **Producer** | Rescue Request Service |
| **Consumer** | Rescue Request Prioritization Service |
| **Channel** | `rescue.prioritization.updated.v1` |
| **Version** | v1 |

**คำอธิบาย:** Message ถูก Publish โดย Rescue Request Service เมื่อมีการ Update ข้อมูลของ Request และจะทำการประเมินลำดับความสำคัญใหม่ เช่น กรณีจำนวนผู้ประสบภัยเพิ่มขึ้น หรือข้อมูล Location เปลี่ยน

#### Message Headers

| Header | คำอธิบาย |
|---|---|
| `messageType` | `RescueRequestReEvaluateEvent` |
| `correlationId` | `messageId` ของ Command ที่รับมา |
| `sentAt` | ISO-8601 datetime |
| `version` | `1` |

#### Message Body

```json
{
  "requestId": "REQ-8812-8888",
  "incidentId": "8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111",
  "evaluateId": "812748a6-5a3a-43c5-8b4f-140034ece737",
  "requestType": "flood_rescue",
  "priorityScore": 0.3,
  "priorityLevel": "NORMAL",
  "evaluateReason": "Lack of food reserves indicates a potential need for assistance, but no immediate life-threatening situation is apparent. Location is accessible.",
  "lastEvaluatedAt": "2026-03-22T07:58:10.247935+00:00",
  "description": "ไม่มีอาหารสํารอง",
  "location": {
    "latitude": 11.111,
    "longitude": 22.222,
    "province": "test province",
    "district": "test dist",
    "subdistrict": "test subdist",
    "addressLine": "test address"
  },
  "peopleCount": 1,
  "specialNeeds": [
    "bedridden",
    "children"
  ]
}
```

#### Field Definition

| Field | Type | Required | คำอธิบาย |
|---|---|---|---|
| `requestId` | String | ✅ | รหัสคำร้อง |
| `incidentId` | UUID | ✅ | รหัสเหตุการณ์ |
| `evaluateId` | UUID | ✅ | รหัส Evaluation |
| `requestType` | String | ✅ | ประเภทของคำร้อง |
| `priorityScore` | Decimal | ✅ | คะแนนความสำคัญ (0–1) |
| `priorityLevel` | enum | ✅ | `LOW` / `NORMAL` / `HIGH` / `CRITICAL` |
| `evaluateReason` | String | ✅ | เหตุผลของการประเมิน |
| `lastEvaluatedAt` | datetime | ✅ | เวลาที่ Evaluate เสร็จ |
| `description` | String | ✅ | คำอธิบายของ Request |
| `location.latitude` | Decimal | ✅ | พิกัดละติจูด |
| `location.longitude` | Decimal | ✅ | พิกัดลองจิจูด |
| `location.province` | String | ❌ | ชื่อจังหวัด |
| `location.district` | String | ❌ | ชื่ออำเภอ |
| `location.subdistrict` | String | ❌ | ชื่อตำบล |
| `location.addressLine` | String | ❌ | ที่อยู่แบบละเอียด |
| `peopleCount` | Integer | ✅ | จำนวนผู้ประสบภัย |
| `specialNeeds` | Array | ❌ | ความต้องการพิเศษ เช่น `bedridden`, `children` |

---

## 11. Service Data

### Prioritization Records (Owned)

| Field | Type | Required | คำอธิบาย | ตัวอย่าง |
|---|---|---|---|---|
| `request_id` | String | ✅ (PK) | รหัสคำร้อง | `REQ-8812-8888` |
| `incident_id` | UUID | ✅ (SK) | อ้างอิง Incident | `8b9b6d5b-7d5e-4d0b-a7e2-2a0a6bd5c111` |
| `evaluate_id` | UUID | ✅ | รหัส Evaluation | `812748a6-5a3a-43c5-8b4f-140034ece737` |
| `request_type` | String | ✅ | ประเภทของคำร้อง | `flood_rescue` |
| `priority_score` | Decimal | ✅ | คะแนนความสำคัญ (0–1) | `0.3` |
| `priority_level` | enum | ✅ | `LOW` / `NORMAL` / `HIGH` / `CRITICAL` | `NORMAL` |
| `evaluate_reason` | String | ✅ | เหตุผลของการประเมิน | `Lack of food reserves...` |
| `description` | String | ❌ | คำอธิบายของ Request | `ไม่มีอาหารสำรอง` |
| `model_id` | String | ✅ | ชื่อ Model ที่ใช้ประเมิน | `gemma-3-27b-it` |
| `people_count` | Integer | ✅ | จำนวนผู้ประสบภัย | `1` |
| `special_needs` | Array | ❌ | ความต้องการพิเศษ | `["bedridden", "children"]` |
| `location.latitude` | Decimal | ✅ | พิกัดละติจูด | `18.7883` |
| `location.longitude` | Decimal | ✅ | พิกัดลองจิจูด | `98.9853` |
| `location.province` | String | ❌ | ชื่อจังหวัด | `เชียงใหม่` |
| `location.district` | String | ❌ | ชื่ออำเภอ | `เมืองเชียงใหม่` |
| `location.subdistrict` | String | ❌ | ชื่อตำบล | `สุเทพ` |
| `location.addressLine` | String | ❌ | ที่อยู่แบบละเอียด | `123 ม.2 ถ.ห้วยแก้ว` |
| `last_evaluated_at` | datetime | ✅ | เวลาที่ Evaluate เสร็จครั้งล่าสุด | `2026-03-22T07:58:10.247935+00:00` |
| `submitted_at` | datetime | ✅ | เวลาที่ Request เข้ามา | `2026-03-03T08:01:12Z` |
| `idemp_key` | UUID | ✅ | ใช้กัน Command ซ้ำ | `f3d2b2d6-3a9b-4cdb-8c8a-8d0d0a57d0a1` |
| `created_at` | datetime | ✅ | เวลาที่ข้อมูลนี้เข้ามาใน Service | `2026-03-22T07:58:07.613705+00:00` |
| `status` | enum | ✅ | `PENDING` / `EVALUATED` / `RE_EVALUATE` / `FAILED` | `EVALUATED` |

---

## 12. Service Architecture

### Components

| Component | บทบาท |
|---|---|
| **User** (Dispatcher / Other Service) | ดึงผลการประเมินลำดับความสำคัญ |
| **API Gateway** | จุดรับคำขอแบบ Synchronous |
| **Lambda REST API Handler** | รับคำขอจาก API Gateway → ดึงข้อมูลจาก DynamoDB → ตอบกลับทันที |
| **DynamoDB** | จัดเก็บข้อมูลที่ Service เป็นเจ้าของ |
| **Amazon SQS** | รับ Event จาก SNS Topic ของ Rescue Request Service |
| **Eventbridge Pipe** | Poll Message จาก SQS → Clean เอาเฉพาะ message ที่ระบบรองรับ (CREATE, UPDATE event) → ส่งต่อให้ Step Functions |
| **Step Functions** | ทำ Decision Logic → อัปเดต DynamoDB → Publish Event |
| **Amazon SNS** | ช่องทางประกาศผลลัพธ์การ Evaluate ให้ Service อื่นนำไปใช้ต่อ |

### Explanation

สถาปัตยกรรมประกอบด้วยการทำงานสองรูปแบบหลัก:

**Synchronous** — ผู้ใช้งานสามารถเรียกดูผลการประเมินผ่าน REST API โดยคำขอเข้าที่ API Gateway → Lambda → DynamoDB แล้วตอบกลับทันที เหมาะสำหรับการอ่านข้อมูลหรือเช็กสถานะแบบ Real-time

**Asynchronous** — เมื่อมีเหตุการณ์ใหม่จาก Rescue Request Service ระบบรับ Event ผ่าน SNS → SQS → Eventbridge Pipe → Step Functions คำนวณ Priority Score → บันทึกผลลง DynamoDB → ประกาศผลลัพธ์กลับผ่าน SNS อีกครั้ง แนวทางนี้ช่วยลดการ Block ผู้เรียก เพิ่มความทนทาน และรองรับโหลดสูงได้ดี

---

## 13. Service Interaction

### Upstream Services

| Service | Interaction | คำอธิบาย |
|---|---|---|
| **Manage Dispatch Service** | `GET /prioritization` (Synchronous) | ดึงข้อมูลการ Evaluate คำขอความช่วยเหลือกู้ภัยทั้งหมด |

### Downstream Services

| Service | Interaction | คำอธิบาย |
|---|---|---|
| **Incident Service** | `GET /incidents/{incidentId}/status` (Synchronous) | ยืนยันความถูกต้องและสถานะของ Incident ก่อนทำการ Evaluate |
| **Rescue Request Service** | `rescue.request.events.v1` (Async) | รับ Event และทําการ evaluate ต่อ |
| **Other Services** | Channel: `rescue.prioritization.events.v1` (Async) | รับ Event ผลลัพธ์การ Evaluate เพื่อนำไปประมวลผลต่อ |

---

## 14. Dependency Mapping

### 1. Rescue Request Service

| | |
|---|---|
| **Type** | Service |
| **Style** | Asynchronous (Event via SNS → SQS) |
| **Purpose** | ส่ง Event `rescue.request.created.v1` และ `rescue.request.updated.v1` |
| **Criticality** | 🔴 Critical |

**Failure Handling:**
- หากไม่ได้รับ Event ระบบจะไม่สามารถ Evaluate Request ใหม่ได้
- ใช้ความสามารถของ SNS ในการ Retry การส่ง Message
- ใช้ SQS เป็น Buffer ป้องกัน Message Loss

---

### 2. Amazon SQS (`rescue.prioritization.events.v1`)

| | |
|---|---|
| **Type** | Queue |
| **Style** | Asynchronous (Command Queue) |
| **Purpose** | รับ Event/Command จาก Rescue Request Service |
| **Criticality** | 🔴 Critical |

**Failure Handling:**
- ใช้ Retry Policy ของ Lambda เมื่อประมวลผลล้มเหลว
- หาก Retry เกินกำหนด Message จะถูกส่งไปยัง DLQ
- รองรับ At-least-once Delivery — Consumer ต้องรองรับ Idempotency

---

### 3. Amazon SNS (`rescue.prioritization.created.v1`)

| | |
|---|---|
| **Type** | Topic |
| **Style** | Asynchronous (Event Notification / Fan-out) |
| **Purpose** | กระจาย `RescueRequestEvaluateEvent` ให้ Dispatch Service และบริการอื่น |
| **Criticality** | 🔴 Critical |

**Failure Handling:**
- หาก Publish ไม่สำเร็จ Lambda จะ Retry ตาม Policy
- Subscriber แต่ละตัวควรมี DLQ ของตนเองเพื่อรองรับ Failure Downstream

---

### 4. Amazon SNS (`rescue.prioritization.updated-v1`)

| | |
|---|---|
| **Type** | Topic |
| **Style** | Asynchronous (Event Notification / Fan-out) |
| **Purpose** | กระจาย `RescueRequestReEvaluatedEvent` ให้ Dispatch Service และบริการอื่น |
| **Criticality** | 🔴 Critical |

**Failure Handling:**
- หาก Publish ไม่สำเร็จ Lambda จะ Retry ตาม Policy
- Subscriber แต่ละตัวควรมี DLQ ของตนเองเพื่อรองรับ Failure Downstream

---

### 5. Amazon DynamoDB

| | |
|---|---|
| **Type** | Database |
| **Style** | Internal Data Access |
| **Purpose** | จัดเก็บผลการประเมิน เช่น `priorityScore`, `priorityLevel`, `status`, `modelId` |
| **Criticality** | 🔴 Critical |

**Failure Handling:**
- หาก Write ล้มเหลว จะไม่ Publish `RescueRequestEvaluatedEvent`
- ใช้ Retry Mechanism ของ Lambda SDK
- หากยังล้มเหลว จะ Throw Error เพื่อให้ SQS Retry Message
- Publish Event หลัง Write สำเร็จเท่านั้น เพื่อป้องกัน Data Inconsistency

---

### 6. Gemini AI Model (Evaluation Model)

| | |
|---|---|
| **Type** | External AI API |
| **Style** | Synchronous (Internal access by Lambda) |
| **Purpose** | ประเมินและคำนวณ `priorityScore` ของแต่ละ Rescue Request โดยใช้ Gemma 3 27B |
| **Criticality** | 🟡 High |

**Failure Handling:**
- หาก Gemini API ตอบไม่สำเร็จหรือ Timeout จะ Fallback ไปใช้ Rule Based Evaluation แทน
- หาก Model ส่งค่า `priority_level` หรือ `priority_score` ไม่ถูกต้อง จะ Raise Error และ Fallback
- ระบบยังคง Publish Event ผลลัพธ์ได้แม้ใช้ Fallback เพื่อไม่ให้ Pipeline หยุดชะงัก
