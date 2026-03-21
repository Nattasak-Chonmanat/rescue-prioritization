# Rescue Prioritization Service

## Service Overview

| | |
|---|---|
| **เจ้าของ** | นายณัฐศักดิ์ ชนมนัส รหัสนักศึกษา 6609611931 ภาคปกติ |
| **GitHub** | https://github.com/Nattasak-Chonmanat/recue-prioritization.git |

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

### Model Metadata
ข้อมูลเกี่ยวกับโมเดลที่ใช้ในการตัดสินใจ ควรอยู่ภายใต้บริการนี้เพราะ:
- โมเดลเป็นส่วนหนึ่งของ Decision Engine
- การเปลี่ยนเวอร์ชันโมเดลมีผลต่อผลลัพธ์
- จำเป็นต่อ Audit และ Explainability

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
  "total": 125,
  "limit": 20,
  "offset": 0,
  "items": [
    {
      "incident_id": "uuid-1",
      "evaluate_id": "uuid-2",
      "request_id": "uuid-3",
      "priority_score": 0.95,
      "priority_level": "CRITICAL",
      "status": "EVALUATED",
      "last_evaluated_at": "2026-03-03T10:15:00Z",
      "description": "String",
      "factors": { "...": "..." },
      "location": { "lat": 123.0, "lng": 123.0 }
    }
  ]
}
```

**500 Internal Server Error**
```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "some thing went wrong",
    "traceId": "uuid"
  }
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
  "evaluate_id": "uuid",
  "incident_id": "uuid",
  "request_id": "uuid",
  "priority_score": 0.87,
  "priority_level": "HIGH",
  "model_id": "uuid",
  "status": "EVALUATED",
  "last_evaluated_at": "2026-03-03T10:15:00Z",
  "description": "String",
  "factors": { "...": "..." },
  "location": { "lat": 123.0, "lng": 123.0 }
}
```

**404 Not Found**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "prioritization not found",
    "traceId": "uuid"
  }
}
```

**500 Internal Server Error**
```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "some thing went wrong",
    "traceId": "uuid"
  }
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
  "requestId": "REQ-8812-9901",
  "incidentId": "8b9b6d5b-2e6b-4b6e-9b1c-1f8a0c4c2d11",
  "payload": {
    "location": { "lat": 18.7883, "lng": 98.9853 },
    "peopleCount": 4,
    "specialNeeds": ["bedridden"]
  },
  "contact": {
    "phonePrimary": "0812345678"
  },
  "submittedAt": "2026-02-21T10:30:00Z"
}
```

#### Field Definition

| Field | Type | Required | คำอธิบาย |
|---|---|---|---|
| `requestId` | String | ✅ | รหัสคำร้อง |
| `incidentId` | UUID | ✅ | รหัสเหตุการณ์ |
| `payload` | Object | ✅ | ข้อมูลเนื้อหา |
| `payload.location` | Object | ✅ | พิกัดภูมิศาสตร์ |
| `submittedAt` | datetime | ✅ | เวลาที่ส่งคำขอ |

#### Validation Rules
1. `incident_id` ต้องไม่ว่าง และต้องเป็น UUID format ที่ถูกต้อง
2. `payload` ต้องไม่ว่าง
3. `submittedAt` ต้องเป็น ISO-8601 datetime
4. `messageId` ต้อง Unique (ใช้ทำ Idempotency)
5. `payload.location` ต้องมี `lat` และ `lng`

---

### Message #2 — Rescue Request Evaluated Event

| | |
|---|---|
| **Message Name** | `RescueRequestEvaluatedEvent` |
| **Style** | Event (Pub/Sub) |
| **Producer** | Rescue Request Prioritization Service |
| **Consumer** | Dispatch Service (และ Service อื่นที่ Subscribe) |
| **Channel** | `rescue.prioritization.events.v1` |
| **Version** | v1 |

**คำอธิบาย:** Event ถูก Publish หลังจาก Prioritization Service ทำการประเมินลำดับความสำคัญเสร็จ ใช้แจ้งผลลัพธ์ให้ Dispatch Service หรือ Service อื่นนำไปประมวลผลต่อ เป็น Asynchronous Event แบบ Fan-out ผ่าน SNS

> **Note:** การอัปเดตการประเมินจะใช้ Topic เดียวกันในการ Publish — Consumer ต้อง Handle Duplicate เอง

#### Message Headers

| Header | คำอธิบาย |
|---|---|
| `messageType` | `RescueRequestEvaluatedEvent` |
| `messageId` | UUID ของ Event |
| `correlationId` | `messageId` ของ Command ที่รับมา |
| `sentAt` | ISO-8601 datetime |
| `traceId` | UUID (สำหรับ Tracing) |
| `version` | `1` |

#### Message Body

```json
{
  "evaluateId": "1f2c7c8e-7d4a-4c77-8c2a-0d5e7f1b9a33",
  "requestId": "8c91c9d4-3f4a-4a0b-b7e1-6b6b3a2e1123",
  "incidentId": "8b9b6d5b-2e6b-4b6e-9b1c-1f8a0c4c2d11",
  "priorityScore": 0.92,
  "priorityLevel": "CRITICAL",
  "modelId": "a73d2e55-9b1c-4b6e-8c2a-3f1d9e7b6c44",
  "lastEvaluatedAt": "2026-02-21T10:31:10Z",
  "submittedAt": "2026-02-21T10:30:00Z",
  "factors": {
    "peopleCountWeight": 0.4,
    "severityWeight": 0.35,
    "distanceWeight": 0.25
  },
  "description": "STRING",
  "location": { "lat": 123.0, "lng": 123.0 }
}
```

#### Field Definition

| Field | Type | Required | คำอธิบาย |
|---|---|---|---|
| `evaluateId` | UUID | ✅ | รหัส Evaluation (PK) |
| `requestId` | String | ✅ | รหัสคำร้อง |
| `incidentId` | UUID | ✅ | รหัสเหตุการณ์ |
| `priorityScore` | Decimal | ✅ | คะแนนความสำคัญ (0–1) |
| `priorityLevel` | enum | ✅ | `LOW` / `NORMAL` / `HIGH` / `CRITICAL` |
| `modelId` | UUID | ✅ | รหัสของ Model version ที่ใช้ |
| `submittedAt` | datetime | ✅ | เวลาที่ Request ถูกส่งเข้ามา |
| `lastEvaluatedAt` | datetime | ✅ | เวลาที่ Evaluate เสร็จ |
| `factors` | Object | ✅ | ปัจจัยที่ใช้คำนวณ |
| `description` | String | ❌ | คำอธิบายของ Request |
| `location` | Object | ✅ | `{lat, lng}` |

#### Validation Rules
1. `incidentId` ต้องไม่ว่าง และต้องเป็น UUID format
2. `evaluateId` ต้องเป็น UUID format
3. `priorityScore` ต้องอยู่ในช่วง 0–1
4. `priorityLevel` ∈ `{LOW, NORMAL, HIGH, CRITICAL}`
5. `correlationId` ต้องตรงกับ `messageId` ของ `RescueRequestPrioritizeCommand`
6. `factors` ต้องไม่ว่าง
7. `location` ต้องไม่ว่าง

---

### Message #3 — Rescue Request Update Event

| | |
|---|---|
| **Message Name** | `rescue-request.citizen-updated` |
| **Style** | Event (Pub/Sub) |
| **Producer** | Rescue Request Service |
| **Consumer** | Rescue Request Prioritization Service |
| **Channel** | `rescue.request.updated.v1` |
| **Version** | v1 |

**คำอธิบาย:** Message ถูก Publish โดย Rescue Request Service เมื่อมีการ Update ข้อมูลของ Request และจะทำการประเมินลำดับความสำคัญใหม่ เช่น กรณีจำนวนผู้ประสบภัยเพิ่มขึ้น หรือข้อมูล Location เปลี่ยน

#### Message Headers

| Header | คำอธิบาย |
|---|---|
| `messageType` | `RescueRequestReEvaluateCommand` |
| `messageId` | UUID ของ Event |
| `correlationId` | `messageId` ของ Command ที่รับมา |
| `sentAt` | ISO-8601 datetime |
| `traceId` | UUID (สำหรับ Tracing) |
| `version` | `1` |

#### Message Body

```json
{
  "requestId": "8c91c9d4-3f4a-4a0b-b7e1-6b6b3a2e1123",
  "incidentId": "8b9b6d5b-2e6b-4b6e-9b1c-1f8a0c4c2d11",
  "updateType": "NOTE",
  "updatePayload": { "note": "STRING" }
}
```

#### Field Definition

| Field | Type | Required | คำอธิบาย |
|---|---|---|---|
| `requestId` | String | ✅ | รหัสคำร้อง |
| `incidentId` | UUID | ✅ | รหัสเหตุการณ์ |
| `updateType` | String | ✅ | `NOTE` |
| `updatePayload` | Object | ✅ | `{ note: "STRING" }` |

#### Validation Rules
1. `updateType` ต้องไม่ว่าง
2. `updatePayload` ต้องไม่ว่าง

---

## 11. Service Data

### Prioritization Records (Owned)

| Field | Type | Required | คำอธิบาย | ตัวอย่าง |
|---|---|---|---|---|
| `evaluate_id` | UUID | ✅ (PK) | รหัส Evaluation | `0317b548-...` |
| `incident_id` | UUID | ✅ | อ้างอิง Incident | `52b627a9-...` |
| `request_id` | String | ✅ | อ้างอิง Rescue Request Service | `REQ-123` |
| `priority_score` | Decimal | ✅ | คะแนนความสำคัญ (0–1) | `0.97` |
| `priority_level` | enum | ✅ | `LOW` / `NORMAL` / `HIGH` / `CRITICAL` | `HIGH` |
| `description` | String | ❌ | คำอธิบายของ Request | `น้ำท่วม ติดอยู่บนหลังคา` |
| `model_id` | UUID | ✅ | อ้างอิง Model version (FK) | `ffbada01-...` |
| `last_evaluated_at` | datetime | ✅ | เวลาที่ Evaluate เสร็จครั้งล่าสุด | `2026-02-14T10:00:00Z` |
| `submitted_at` | datetime | ✅ | เวลาที่ Request เข้ามา | `2026-02-14T10:20:00Z` |
| `idemp_key` | UUID | ✅ | ใช้กัน Command ซ้ำ | `b66edf20-...` |
| `created_at` | datetime | ✅ | เวลาที่ข้อมูลนี้เข้ามาใน Service | `2026-02-14T10:20:00Z` |
| `status` | enum | ✅ | `PENDING` / `EVALUATED` / `RE_EVALUATE` / `FAILED` | `EVALUATED` |
| `location` | Object | ✅ | พิกัด lat และ lng | `{ "lat": 123.0, "lng": 123.0 }` |

### Model Metadata (Owned)

| Field | Type | Required | คำอธิบาย | ตัวอย่าง |
|---|---|---|---|---|
| `model_id` | UUID | ✅ (PK) | รหัสของ AI Model | `20736831-...` |
| `model_name` | String | ✅ | ชื่อของ AI Model | `test-model-123v1` |
| `version` | String | ✅ | Version ของ Model | `ed_1.0.3` |
| `is_active` | boolean | ✅ | ใช้งานอยู่หรือไม่ | `true` |
| `created_at` | datetime | ✅ | วันที่สร้าง | `2026-02-14T10:25:00Z` |

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
| **Lambda Async Worker** | Poll Message จาก SQS → ทำ Decision Logic → อัปเดต DynamoDB → Publish Event |
| **Amazon SNS** | ช่องทางประกาศผลลัพธ์การ Evaluate ให้ Service อื่นนำไปใช้ต่อ |

### Explanation

สถาปัตยกรรมประกอบด้วยการทำงานสองรูปแบบหลัก:

**Synchronous** — ผู้ใช้งานสามารถเรียกดูผลการประเมินผ่าน REST API โดยคำขอเข้าที่ API Gateway → Lambda → DynamoDB แล้วตอบกลับทันที เหมาะสำหรับการอ่านข้อมูลหรือเช็กสถานะแบบ Real-time

**Asynchronous** — เมื่อมีเหตุการณ์ใหม่จาก Rescue Request Service ระบบรับ Event ผ่าน SNS → SQS → Lambda Async Worker คำนวณ Priority Score → บันทึกผลลง DynamoDB → ประกาศผลลัพธ์กลับผ่าน SNS อีกครั้ง แนวทางนี้ช่วยลดการ Block ผู้เรียก เพิ่มความทนทาน และรองรับโหลดสูงได้ดี

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
- หากไม่ได้รับ Event ระบบจะไม่สามารถ Evaluate Incident ใหม่ได้
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

### 3. Amazon SNS (`rescue.prioritization.events.v1`)

| | |
|---|---|
| **Type** | Topic |
| **Style** | Asynchronous (Event Notification / Fan-out) |
| **Purpose** | กระจาย `RescueRequestEvaluatedEvent` ให้ Dispatch Service และบริการอื่น |
| **Criticality** | 🔴 Critical |

**Failure Handling:**
- หาก Publish ไม่สำเร็จ Lambda จะ Retry ตาม Policy
- Subscriber แต่ละตัวควรมี DLQ ของตนเองเพื่อรองรับ Failure Downstream

---

### 4. Amazon DynamoDB

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

### 5. Amazon S3 (Model Storage)

| | |
|---|---|
| **Type** | Object Storage |
| **Style** | Synchronous (Internal access by Lambda) |
| **Purpose** | จัดเก็บ Machine Learning Model ที่ใช้คำนวณ `priorityScore` |
| **Criticality** | 🟡 High |

**Failure Handling:**
- หากโหลด Model ไม่สำเร็จ จะไม่ทำการ Evaluate และ Log Error
- Lambda จะ Retry ตาม Execution Policy
- หากไม่สามารถโหลด Model ได้ต่อเนื่อง ระบบจะไม่ Publish Event ผลลัพธ์
