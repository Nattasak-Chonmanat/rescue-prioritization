# Service Overview

**ภาพรวมของบริการ (Service Overview)**  
Rescue Prioritization Service

1. **Service Owner**

นายณัฐศักดิ์ ชนมนัส รหัสนักศึกษา 6609611931 ภาคปกติ  
**Github**: [https://github.com/Nattasak-Chonmanat/recue-prioritization.git](https://github.com/Nattasak-Chonmanat/recue-prioritization.git)

2. **Service Purpose**

Rescue Request Prioritization Service เป็นบริการที่รับผิดชอบการวิเคราะห์และจัดลำดับความสำคัญของคำขอความช่วยเหลือ (Rescue Requests) ระหว่างเหตุการณ์ภัยพิบัติ โดยทำหน้าที่เป็น decision engine สำหรับกำหนดระดับความเร่งด่วนของแต่ละคำขอ เพื่อสนับสนุนการตัดสินใจของระบบจัดสรรหน่วยกู้ภัย 

3. **Pain Point ที่แก้ไข**

ในสถานการณ์ภัยพิบัติที่ คำขอความช่วยเหลือจำนวนมากเข้ามาพร้อมกัน การประเมินความเร่งด่วนด้วยมนุษย์ใช้เวลานาน อาจเกิด bias หรือความไม่สม่ำเสมอในการตัดสินใจ บริการนี้จึงถูกออกแบบมาเพื่อวิเคราะห์และให้คะแนนความเร่งด่วนแบบอัตโนมัติ ลดเวลาตัดสินใจ เพิ่มความสม่ำเสมอและความโปร่งใสในการจัดลำดับความสำคัญและรองรับปริมาณคำขอจำนวนมาก 

**4\. Target Users**

* Dispatcher (ช่วยจัดลําดับความสําคัญคําขอความช่วยเหลือให้อัตโนมัติ)

**5\. Service Boundary**

* In-scope Responsibilities (สิ่งที่บริการนี้รับผิดชอบ)  
  * ประมวลผลลำดับความสำคัญโดยใช้ AI Model  
  * จัดเก็บข้อมูลการจัดลําดับความสําคัญ (Prioritization Records)  
  * ส่งผลลัพธ์ไปยัง service อื่นแบบ asynchronous

* Out-of-scope / Not Responsible For (ไม่รับผิดชอบ)  
  * การจัดการข้อมูลเหตุการณ์ (Incident Master Data)  
  * การจัดสรรหน่วยกู้ภัย  
  * การตัดสินใจเส้นทางการเดินทาง  
  * การสื่อสารกับผู้ประสบภัยโดยตรง

**6\. Autonomy / Decision Logic**  
บริการมีความเป็นอิสระในการตัดสินใจเกี่ยวกับ:

* การกำหนดระดับ priority ของคำขอ  
* การคำนวณ priority\_score ตาม model  
* การ re-prioritize ในกรณีข้อมูล incident เปลี่ยน

การตัดสินใจอิงจาก:

* จำนวนผู้ได้รับผลกระทบ (people\_count)  
* ประเภทเหตุการณ์ (incident\_type)  
* ความเสี่ยงต่อชีวิต (life-threatening indicator)  
* สถานะของ incident

บริการสามารถตัดสินใจได้เองภายใต้ business rules ที่กำหนด โดยไม่ต้องรอการอนุมัติจากมนุษย์ในกรณีปกติ

**7\. Owned Data**

* Prioritization Records (Master data)  
  ข้อมูลผลลัพธ์การจัดลำดับความสำคัญของแต่ละคำขอ  ควรอยู่ภายใต้บริการนี้เพราะเป็นข้อมูลแกนหลักของ domain และบริการนี้เป็นผู้ใช้ข้อมูลดังกล่าวโดยตรงในการให้บริการและเป็นผลลัพธ์โดยตรงของ decision logic   
* Model Metadata  
  ข้อมูลเกี่ยวกับโมเดลที่ใช้ในการตัดสินใจ ควรอยู่ภายใต้บริการนี้ เพราะโมเดลเป็นส่วนหนึ่งของ decision engine การเปลี่ยนเวอร์ชันโมเดลมีผลต่อผลลัพธ์ จำเป็นต่อ audit และ explainability

**8\. Linked Data (Reference Only)**

* อ้างอิงจาก Incident Service เพื่อระบุว่าคำร้องนี้อยู่ภายใต้เหตุการณ์ภัยพิบัติใด   
* บริการนี้ไม่เก็บสำเนาข้อมูล incident อย่างถาวร

**9\. Non-Functional Requirements**

* ใช้รูปแบบ message delivery แบบ at-least-once  
* ต้องมีการตรวจสอบ messageId เพื่อป้องกันการประมวลผลซ้ำ (idempotency)  
* ห้ามสร้าง prioritization record ซ้ำ  
* ห้ามส่ง downstream event ซ้ำ  
* Model retry การประมวลผลไม่เกิน 3 ครั้ง  
* หากเกินจำนวน retry ส่ง message ไปยัง **Dead Letter Queue (DLQ)** บันทึกสถานะเป็น `FAILED`  
* ต้องรับประกันว่า 1 incident → 1 final prioritization result  
  


# Sync Contract

**Synchronous Function Contract**  
**Base URL:** *http://TBD.com*

# **API Contract \#1: List Prioritizations By incident\_id**

### **ข้อมูลทั่วไป**

* **Name:** Get prioritization result by incident  
* **Method:** GET  
* **Path:** /v1/prioritizations/{incident\_id}  
* **Type:** Synchronous

### **คำอธิบาย**

ใช้ค้นหาและกรองผลการจัดลำดับความสำคัญเพื่อให้บริการอื่น (เช่น Dispatch Service หรือ Dashboard) ดึงรายการตามเงื่อนไขที่ต้องการ

### **Request**

	Path Param

* incident\_id (uuid, required)

  **Query Params**

* priority\_level (string , optional, LOW / NORMAL/ HIGH / CRITICAL)  
* status (string, optional, PENDING / EVALUATED / RE\_EVALUATE / FAILED)  
* limit (integer, optional, default=20)  
* offset (integer, optional, default=0)  
* min\_score (decimal, optional, กรองคะแนนตํ่าสุด)  
* max\_score (decimal, optional, กรองคะแนนสูงสุด)  
* sortBy (string, optional, priorityScore / priorityLevel)  
* sortOrder (string, optional, asc / desc) 

  **Headers**

* Accept: application/json

  **Body:** ไม่มี


  **Validation**

* priority\_level ∈ {LOW, NORMAL, HIGH , CRITICAL}  
* status ∈ {PENDING, EVALUATED, RE\_EVALUATE, FAILED}  
* min\_score, max\_score เป็น decimal  
* sortBy ∈ {priorityScore, priorityLevel}  
* sortOrder ∈ {asc, desc}  
  **Body:** ไม่มี

### **Response**

**Success: 200**  
**{**  
  **"total": 125,**  
  **"limit": 20,**  
  **"offset": 0,**  
  **"items": \[**  
    **{**  
      **"incident\_id": "uuid-1",**  
      **"evaluate\_id": "uuid-2",**  
        **"request\_id": "uuid-3",**  
      **"priority\_score": 0.95,**  
      **"priority\_level": "CRITICAL",**  
      **"status": "EVALUATED",**  
      **"last\_evaluated\_at": "2026-03-03T10:15:00Z",**  
      **"description": "String",**  
      **"factors": { … },**  
      **"location": {**  
        **"lat": 123.0,**  
        **"lng": 123.0**  
      **}**  
    **},**  
    **{**  
      **"incident\_id": "uuid-4",**  
      **"evaluate\_id": "uuid-5",**  
      **"request\_id": "uuid-6",**  
      **"priority\_score": 0.82,**  
      **"priority\_level": "HIGH",**  
      **"status": "EVALUATED",**  
      **"last\_evaluated\_at": "2026-03-03T09:50:00Z",**  
      **"description": "String",**  
      **"factors": { … },**  
      **"location": {**  
        **"lat": 123.0,**  
        **"lng": 123.0**  
      **}**  
    **},**  
    **{**  
        **...**  
    **},**  
    **...**  
  **\]**  
**}**

**Error: 500**

{  
  "error": {  
    "code": "INTERNAL\_SERVER\_ERROR",  
    "message": "some thing went wrong",  
    "traceId": "uuid"  
  }  
}

### **Dependency / Reliability**

* ไม่เรียก service อื่น  
* Read-only  
* Idempotent (GET)  
* Timeout: 10s  
* รองรับ pagination

# **API Contract \#2: Get Prioritization By request\_id**

### **ข้อมูลทั่วไป**

* **Name:**  Search prioritization results  
* **Method:** GET  
* **Path:** /v1/prioritization/request/{request\_id}  
* **Type:** Synchronous

### **คำอธิบาย**

ใช้ค้นหาผลลัพธ์การ evaluate ของแต่ละ request

### **Request**

	Path Param

* request\_id (string, required)

  **Query Params:** ไม่มี

  **Headers**

* Accept: application/json


  **Body:** ไม่มี

### **Response**

**Success: 200**

**{**  
    **"evaluate\_id": "uuid",**  
    **"incident\_id": "uuid",**  
    **"request\_id": "uuid",**  
    **"priority\_score": 0.87,**  
    **"priority\_level": "HIGH",**  
    **"model\_id": "uuid",**  
    **"status": "EVALUATED",**  
    **"last\_evaluated\_at": "2026-03-03T10:15:00Z",**  
    **"desciption": "String",**  
    **"factors": { … },**  
    **"location": {**  
        **"lat": 123.0,**  
        **"lng": 123.0**  
    **}**  
**}**

**Error: 404**{

  "error": {  
    "code": "NOT\_FOUND",  
    "message": "prioritization not found",  
    "traceId": "uuid"  
  }  
}

**Error: 500**  
{  
  "error": {  
    "code": "INTERNAL\_SERVER\_ERROR",  
    "message": "some thing went wrong",  
    "traceId": "uuid"  
  }  
}

### **Dependency / Reliability**

* ไม่เรียก service อื่น  
* Read-only  
* Idempotent (GET)  
* Timeout: 5s


  

# Async Contract

**Asynchronous Function Contract**

## **Message Contract \#1: Rescue Request Prioritize Command**

### **ข้อมูลทั่วไป** 

* **Message Name:** RescueRequestPrioritizeCommand  
* **Interaction Style:** Event (Pub/Sub)  
* **Producer:** RescueRequest Service  
* **Consumer:** Rescue request prioritization service  
* **Channel/Queue:** rescue.prioritization.commands.v1  
* **Version:** v1

### **คำอธิบาย**

Message นี้ถูก publish โดย Rescue Request Service ผ่าน SNS และถูกส่งต่อไปยัง SQS ของ Prioritization Service ใช้เพื่อสั่งให้ระบบ Prioritization คำนวณลำดับความสำคัญของ rescue request เป็น asynchronous command และต้องรองรับ idempotency

### **Request** 

### **Message Headers (required unless stated)**

* `messageType: RescueRequestPrioritizeCommand`  
* `messageId: <UUID>`  (ใช้เป็น idempotency key)  
* `sentAt: ISO-8601 datetime`  
* `traceId: <UUID> (ใช้สำหรับ tracing)`  
* `version: 1 (schema version)`

  **Message Body**

`{`  
`"requestId": "REQ-8812-9901",`  
`"incidentId": "8b9b6d5b-2e6b-4b6e-9b1c-1f8a0c4c2d11",`  
`"payload": {`  
  `"location": { "lat": 18.7883, "lng": 98.9853 },`  
  `"peopleCount": 4,`  
  `"specialNeeds": ["bedridden"],`  
`},`  
`"contact": {`  
  `"phonePrimary": "0812345678"`  
`},`  
`"submittedAt": "2026-02-21T10:30:00Z"`  
`}`  
Credit: Rescue request service

**Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| requestId | String | Y | รหัสคําร้อง |
| incidentId | UUID | Y | รหัสเหตุการณ์ |
| payload | Object | Y | ข้อมูลเนื้อหา |
| payload.location | Object | Y | พิกัดภูมิศาสตร์ |
| submittedAt | Object | Y | เวลาที่ส่งคำขอ |

Credit: Rescue request service

**Validation Rules**

1. incident\_id ต้องไม่ว่าง และต้องเป็น UUID format ที่ถูกต้อง  
2. payload ต้องไม่ว่าง  
3. submittedAt ต้องเป็น ISO-8601 datetime  
4. messageId ต้อง unique (ใช้ทำ idempotency)  
5. payload.location ต้องมี lat และ lng

**Response**

	**Message Headers (required unless stated)**

- **None เนื่องจากเป็น Asynchronous Command ผ่าน SNS \-\> SQS**

  **Success Message Body**

- **None**  
  


  **Reject/Error Message Body**

- **None**


## **Message Contract \#2: Rescue Request Evaluated Event**

### **ข้อมูลทั่วไป** 

* **Message Name:** RescueRequestEvaluatedEvent  
* **Interaction Style:** Event (Pub/Sub)  
* **Producer:** Rescue request prioritization service  
* **Consumer:** Dispatch Service (และ service อื่นที่ subscribe)  
* **Channel/Queue:** rescue.prioritization.events.v1  
* **Version:** v1

### **คำอธิบาย**

Event นี้ถูก publish หลังจาก Prioritization Service ทําการประเมินลำดับความสำคัญของ rescue request เสร็จแล้วใช้แจ้งผลลัพธ์ให้ Dispatch Service หรือ service อื่นนำไปประมวลผลต่อ เป็น asynchronous event แบบ fan-out ผ่าน SNS

NOTE: การอัพเดทการประเมินจะใช้ topic ในการ publish ด้วย consumer ต้อง handle duplicate เอง

### **Request** 

### **Message Headers (required unless stated)**

* `messageType: RescueRequestEvaluatedEvent`  
* `messageId: <UUID>  (UUID ของ event)`  
* `correlationId: <messageId ของ Command ที่รับมา>`  
* `sentAt: ISO-8601 datetime`  
* `traceId: <UUID> (ใช้สำหรับ tracing)`  
* `version: 1 (schema version)`

  **Message Body**

`{`  
`"evaluateId": "1f2c7c8e-7d4a-4c77-8c2a-0d5e7f1b9a33",`  
`"requestId": "8c91c9d4-3f4a-4a0b-b7e1-6b6b3a2e1123",`  
`"incidentId": "8b9b6d5b-2e6b-4b6e-9b1c-1f8a0c4c2d11",`  
`"priorityScore": 0.92,`  
`"priorityLevel": "CRITICAL",`  
`"modelId": "a73d2e55-9b1c-4b6e-8c2a-3f1d9e7b6c44",`  
`"lastEvaluatedAt": "2026-02-21T10:31:10Z",`  
`"submittedAt": "2026-02-21T10:30:00Z",`  
`"factors": {`  
`"peopleCountWeight": 0.4,`  
`"severityWeight": 0.35,`  
`"distanceWeight": 0.25`  
`},`  
`“description”: “STRING”,`  
`“location”: {lat : 123.0, lng: 123.0}`  
`}`

**Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| evaluateId | UUID | Y | รหัส evaluation (PK) |
| requestId | String | Y | รหัสคําร้อง |
| incidentId | UUID | Y | รหัสเหตุการณ์ |
| priorityScore | Decimal | Y | คะแนนความสําคัญ (0 \- 1\) |
| priorityLevel | enum (LOW, NORMAL, HIGH, CRITICAL) | Y | ระดับความสําคัญ |
| modelId | UUID | Y | รหัสของ model version ที่ใช้ |
| submittedAt | datetime | Y  | เวลาที่ request ถูกส่งเข้ามา |
| lastEvaluatedAt | datetime | Y | เวลาที่ evaluate เสร็จ |
| factors | Object | Y | ปัจจัยที่ใช้คํานวณ |
| description | String | N | คําอธิบายของ request |
| location | Object | Y | {lat: 123.0, lng: 123.0} |

**Validation Rules**

1. incident\_id ต้องไม่ว่าง และต้องเป็น UUID format ที่ถูกต้อง  
2. evaluateId ต้องเป็น UUID format  
3. incidentId ต้องเป็น UUID format  
4. priorityScore ต้องอยู่ในช่วง 0 – 1  
5. priorityLevel ต้องเป็น {LOW, NORMAL, HIGH, CRITICAL}  
6. correlationId ต้องตรงกับ messageId ของ RescueRequestPrioritizeCommand  
7. factors ต้องไม่ว่าง  
8. location ต้องไม่ว่าง

**Response**

	**Message Headers (required unless stated)**

- **None เนื่องจากเป็น Event แบบ Pub/Sub ผ่าน SNS**  
- **Producer จะไม่ได้รับ response ใด ๆ**

  **Success Message Body**

- **None**  
  


  **Reject/Error Message Body**

- **None**

## **Message Contract \#3: Rescue Request UpdateEvent**

### **ข้อมูลทั่วไป** 

* **Message Name:** rescue-request.citizen-updated  
* **Interaction Style:** Event (Pub/Sub)  
* **Producer:** Rescue request service  
* **Consumer:** Rescue request prioritization service  
* **Channel/Queue:** rescue.request.updated.v1  
* **Version:** v1

### **คำอธิบาย**

Message นี้ถูก publish โดย Rescue Request Service ผ่าน SNS และถูกส่งต่อไปยัง SQS ของ Prioritization Service เมื่อมีการ update ข้อมูลของ request และจะทำการประเมินลำดับความสำคัญของ request ใหม่ เช่น กรณีจำนวนผู้ประสบภัยเพิ่มขึ้น หรือข้อมูล location เปลี่ยน

### **Request** 

### **Message Headers (required unless stated)**

* `messageType: RescueRequestReEvaluateCommand`  
* `messageId: <UUID>  (UUID ของ event)`  
* `correlationId: <messageId ของ Command ที่รับมา>`  
* `sentAt: ISO-8601 datetime`  
* `traceId: <UUID> (ใช้สำหรับ tracing)`  
* `version: 1 (schema version)`

  **Message Body**

`{`  
`"requestId": "8c91c9d4-3f4a-4a0b-b7e1-6b6b3a2e1123",`  
`"incidentId": "8b9b6d5b-2e6b-4b6e-9b1c-1f8a0c4c2d11",`  
`"updateType": “NOTE”`  
`“updatePayload”: { NOTE: “STRING” }`  
`}`

**Field Definition:**

| Field | Type | Required | Description |
| ----- | ----- | ----- | ----- |
| requestId | String | Y | รหัสคําร้อง |
| incidentId | UUID | Y | รหัสเหตุการณ์ |
| updateType | String | Y | NOTE |
| updatePayload | Object | Y | {    NOTE: “STRING” } |

**Validation Rules**

1. updateType ต้องไม่ว่าง  
2. updatePayload ต้องไม่ว่าง

**Response**

	**Message Headers (required unless stated)**

- **None เนื่องจากเป็น Event แบบ Pub/Sub ผ่าน SNS**  
- **Producer จะไม่ได้รับ response ใด ๆ**

  **Success Message Body**

- **None**  
  


  **Reject/Error Message Body**

- **None**

# Service Data

# **Service Data**

# **1\) Prioritization Records Master Data (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| evaluate\_id | UUID | Y (Primary Key) | รหัส evaluation | 0317b548-0cc1-497f-a3b5-fea068ea31ea |
| incident\_id | UUID | Y | อ้างอิง Incident | 52b627a9-1059-470a-aef6-8567e7d6d6e2 |
| request\_id | String | Y | อ้างอิง Rescue request service | REQ-123 |
| priority\_score | Decimal | Y | คะแนนความสําคัญ (0 \- 1\) | 0.97 |
| priority\_level | enum | Y | LOW / NORMAL / HIGH / CRITICAL | HIGH |
| description | String  | N | คําอธิบายของ request | นํ้าท่วม ติดอยู่บนหลังคา |
| model\_id | UUID | Y | อ้างอิง version ของ model ที่ใช้ (FK) | ffbada01-6111-4205-93a7-d2fe9bb6bf92 |
| last\_evaluated\_at | datetime | Y | เวลาที่ evaluate เสร็จครั้งล่าสุด | 2026-02-14T10:00:00Z |
| submitted\_at | datetime | Y | เวลาที่ request เข้ามา | 2026-02-14T10:20:00Z |
| idemp\_key | UUID  | Y | ใช้กัน command ซ้ำ | b66edf20-08f0-48ae-8b78-0940c733c9c3 |
| created\_at | datetime | Y | เวลาที่ข้อมูลนี้เข้ามาใน service | 2026-02-14T10:20:00Z |
| status  | enum | Y | PENDING, EVALUTED, RE\_EVALUATE, FAILED | EVALUATED |
| location | Object | Y | พิกัด latitude และ longitude | {    “lat”: 123.0,    “lng”: 123.0 } |

# **2\) Model metadata (Owned by this service)**

| Field Name | Type | Required | Description | Example |
| ----- | ----- | ----- | ----- | ----- |
| model\_id | UUID | Y (PK) | รหัสของ AI Model | 20736831-d39b-486e-8f68-0dba3c5362bb |
| model\_name | String | Y | ชื่อของ AI Model | test-model-123v1 |
| version | String | Y | Version ของ model | ed\_1.0.3 |
| is\_active | boolean | Y | ใช้งานอยู่หรือไม่ | true |
| created\_at | datatime | Y | วันที่สร้าง | 2026-02-14T10:25:00Z |

# Service Architecture

**Service Architecture**  
![][image1]  
**Components**

* User (Dispatcher / Other Service)  
  * ดึงผลการประเมินลำดับความสำคัญ (GET /prioritizations/{incidentId})


* API Gateway: จุดรับคำขอแบบ synchronous (เช่น GET /prioritizations/{incidentId})  
* Lambda REST API Handler  
  * รับคำขอจาก API Gateway  
  * ดึงข้อมูลผลการประเมินจาก DynamoDB  
  * ส่งผลลัพธ์กลับทันที  
      
* DynamoDB: จัดเก็บข้อมูลที่ Rescue Request Prioritization Service เป็นเจ้าของ   
* Amazon SQS (rescue.prioritization.commands.v1):  Event ที่มาจาก SNS topic ของ Rescue Request Service  
* Lambda Async Worker: poll message จาก SQS ทำ decision logic, อัปเดตข้อมูลและ Publish event: RescueRequestEvaluatedEvent  
* Amazon SNS: ช่องทางประกาศผลลัพธ์การ evaluate เพื่อให้ service อื่นนําไปใช้ต่อ


  
**Explanation**

สถาปัตยกรรมของ Rescue Request Prioritization Service ประกอบด้วยการทำงานสองรูปแบบหลัก คือ synchronous และ asynchronous เพื่อรองรับทั้งการเรียกดูผลลัพธ์แบบทันทีและการประมวลผลเชิงวิเคราะห์ที่ใช้เวลา ในส่วนของ synchronous ผู้ใช้งานหรือบริการอื่นสามารถเรียกดูผลการประเมินลำดับความสำคัญผ่าน REST API โดยคำขอจะเข้าที่ Amazon API Gateway และถูกส่งต่อไปยัง AWS Lambda เพื่อดึงข้อมูลจาก Amazon DynamoDB แล้วตอบกลับทันที เหมาะสำหรับการอ่านข้อมูลหรือเช็กสถานะแบบ real-time

ในส่วนของ asynchronous เมื่อมีเหตุการณ์ใหม่จาก Rescue Request Service ระบบจะรับ event ผ่าน SNS แล้วส่งต่อเข้า Amazon SQS จากนั้น Lambda ที่ทำหน้าที่เป็น async worker จะดึงข้อความจากคิวมาโหลดโมเดลจาก Amazon S3 เพื่อคำนวณ priorityScore บันทึกผลลง DynamoDB และประกาศผลลัพธ์กลับผ่าน SNS อีกครั้ง แนวทางนี้ช่วยลดการ block ผู้เรียก เพิ่มความทนทาน และรองรับโหลดสูงได้ดี เหมาะกับระบบที่ต้องประมวลผลเหตุการณ์จำนวนมากในช่วงวิกฤต

# Service Interaction

**Service Interaction**  
![][image2]

## **Upstream Services (บริการต้นทางที่เรียกใช้งาน ShelterCapacity Service)**

* **Manage Dispatch Service**  
   เรียกใช้งาน GET /prioritization แบบ synchronous เพื่อดึงข้อมูลการ evaluate คําขอความช่วยเหลือกู้ภัยทั้งหมด

**Downstream Services (บริการปลายทางที่ ShelterCapacity Service เรียกหรือส่งข้อมูลไป)**

* **Incident Service**  
   ถูกเรียกใช้งานแบบ synchronous ผ่าน GET /incidents/{incidentId}/status เพื่อยืนยันความถูกต้องและสถานะของ incident ก่อนทำการ evaluate request  
* **Other Services (channel: rescue.prioritization.events.v1)**  
   รับ event ที่ถูกส่งออกโดย Rescue Request Prioritization Service เพื่อแจ้งผลลัพธ์การ evaluate ความสําคัญของ request (อาจเป็น Service ใหม่ในอนาคตที่ต้องการใช้ข้อมูลนี้)

 

# Dependency Mapping

**Dependency Mapping – ShelterCapacity Service**

### **1\. Rescue Request Service**

* Type: Service  
* Interaction Style: Asynchronous (Event via SNS → SQS)  
* Purpose: ส่งเหตุการณ์ `rescue.request.created.v1` และ `rescue.request.updated.v1` เพื่อให้ Prioritization Service ทำการประเมินลำดับความสำคัญ  
* Criticality: Critical  
* Failure Handling:  
  * หากไม่ได้รับ event ระบบจะไม่สามารถ evaluate incident ใหม่ได้  
  * ใช้ความสามารถของ Amazon SNS ในการ retry การส่ง message  
  * ใช้ Amazon SQS เป็น buffer ป้องกัน message loss  
  * หากเกิด failure ในการรับ message จะถูก retry ตาม policy ของ SQS และ Lambda

### **2\. Amazon SQS (rescue.prioritization.events.v1)**

* Type: Queue  
* Interaction Style: Asynchronous (Command Queue)  
* Purpose: รับ event/command จาก Rescue Request Service เพื่อเข้าสู่กระบวนการ evaluate  
* Criticality: Critical  
* Failure Handling:  
  * ใช้ retry policy ของ AWS Lambda เมื่อประมวลผลล้มเหลว  
  * หาก retry เกินกำหนด message จะถูกส่งไปยัง Dead Letter Queue (DLQ)  
  * รองรับ at-least-once delivery ดังนั้น consumer ต้องรองรับ idempotency

### **3\.  Amazon SNS (rescue.prioritization.events.v1)**

* Type: Topic  
* Interaction Style: Asynchronous (Event Notification / Fan-out)  
* Purpose:  กระจาย `RescueRequestEvaluatedEvent` ให้ Dispatch Service และบริการอื่น  
* Criticality: Critical  
* Failure Handling:  
  * หาก publish ไม่สำเร็จ Lambda จะ retry ตาม policy  
  * Subscriber แต่ละตัวควรมี DLQ ของตนเองเพื่อรองรับ failure downstream

### **4\. Amazon DynamoDB**

* Type: Database  
* Interaction Style: Internal Data Access  
* Purpose: จัดเก็บผลการประเมิน เช่น priorityScore, priorityLevel, status, modelId  
* Criticality: Critical  
* Failure Handling:  
  * หาก write ล้มเหลว จะไม่ publish `RescueRequestEvaluatedEvent`  
  * ใช้ retry mechanism ของ Lambda SDK  
  * หากยังล้มเหลว จะ throw error เพื่อให้ SQS retry message  
  * ป้องกัน data inconsistency โดย publish event หลัง write สำเร็จเท่านั้น

### **5\. Amazon S3 (Model Storage)**

* Type: Object Storage  
* Interaction Style: Synchronous (Internal access by Lambda)  
* Purpose: จัดเก็บ Machine Learning model ที่ใช้คำนวณ priorityScore  
* Criticality: High  
* Failure Handling:  
  * หากโหลด model ไม่สำเร็จ จะไม่ทำการ evaluate และ log error  
  * Lambda จะ retry ตาม execution policy  
  * หากไม่สามารถโหลด model ได้ต่อเนื่อง ระบบจะไม่ publish event ผลลัพธ์  
    

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnAAAAC4CAIAAADsVUYEAAAd50lEQVR4Xu3dDYwcZ33H8Q2JHftCzsRGvEjc8aLwolj4FCERIxktaYkQoPoCRnlRYVVRjJpwkgE5kZFNJGKJHIkVEgIKFBIlRCSRIYp1pMhQQYzb0gROchBUushqA404jAI1+ISqSm2mf54f+89zz+ze3fpmd2fmvh+NTrPPPPPMzN7M/PbZl5lGBgAAVq2RFgAAgN4RqAAAFIBABQCgAAQqAAAFIFABACgAgQoAQAEIVAAACkCgAgBQAAIVAIACEKgAABSAQAUAoAAEKgAABSBQAQAoAIEKAEABCFQAAApAoKK8Wq1Ws9lMS1FZIyMjaRFQIwQqztL09PT4+Hha2iNrYX5+Pi1tWzZQbR1mZ2fT0upYOmA01bZRT5E9XGJjrY7+HTZiz1s6uRyW3t5YmbcC6IZALSM7m9hptNFo6JzSCDTJTkk2PjMzY+N2erVxnWf9VKUEshZsUhJ4VscatJazkGRWwcNM7di8CwsLcVP2UFPzK6BCLxc1a1NtlVTHC7Uy1qbmsqnaxsbizdSmWYmNj42NeaDGZ1jfLi1I44WwlrVWWXsdNK6n2ldPT4KeeV9hrWryxGpeq6PW7PnUP0v/CH+q4wXFU+OnyP/RKrFxn+rLNcePH9cTZctqhJXUIsYDVY75tvi4NsQa+cY3vqGH+ldqZ9B+oocayULqa+latC/Ld9R4Kb4P+Dr4CyMfscYJVFROenShDBSHGleqKTl0Ds3CecfjSpP8vGn1/aGdknQSFCv0E5zaUeNWzZao82M+ULutwHSuh+pTp6amZkMCxYVamcnJSVXWUsbbPVRfipfrbzPqoXplX8N+BKpWWxueLX569SJgJvBJGlegJk+s2tRTYdX0mkCtaa7436R581OnO/VQ9fxoWZrRe6j6h8brr9YaIea1CDUST022RauqrbBmVaLFafWmQ977ojVJU31Z/nAkvDJQue9R2uU0l7fg/25thcaBqiBQyyg+Q/kpxkYOHz6sU14WpWPW7gF4tfHQzcoWt6NZVOhBqJr+UGe6uCk/L+thvALxjBI/9LOzF/rKqHei3IoDVdXsNHrzzTerUOd0latOfGbP+hOoajx+LdJs98PEn58s2kytavLEJnWydih6C0oanys/NesUqJ6CKmyETmQSqPFTpydZUzvuEl5NI96CngEf0f6gWXyjfERrosiMn4ckbue7vJerZpN1WFQDKD0CtYw6Bqo8/fTTypWRFQRqQnXiQBV/GJ8x/WG3Feg1UCU+1epvEqhZFCFxKmTR26EedYMJVFkI76DqmffCboEaKzxQVT/5pw83UL0dVY7/y0mgZmEd9GRqu3zGxx9/3J8oAhVVRKCWURKoOp1NTU2pUFOn2x/12TnIY0+n0fhUO9P+qDKLzp6zi9861rwaSZrSw44rMNN+z9keqo6WpZrxCde3JZ5FI432x2y+FKvvJ1P1vTTiLcSh1b9A9echizZcU7XtWfuZj1c1eWL11wv1nOQjUyGkavmpM4Ee2lRfK8/I5D+lVfL199mTQPW09m3xf1mr/Zav/iMrCVT/p+R7qFqWVdM/Xf9fb9Yq6OFCiFjNpYcEKiqHQMULPNVQIM8eAPVGoOIFBGo/EKjAGkGgAgBQAAIVAIACEKgAABSAQAUAoAAEKgAABVhpoO7cufOSSy45ceJEOqHEnn/++SNHjmzatOnOO+9Mp60Bf/zNiacfurycw7Pf/0S6ugBQcSsK1A0bNqRFVXPdddelRXVHoALAIC0fqPfee29aVEFHjx5Ni+qOQK0B+ycOcUjXBsCSlg/U9evXp0XVdOONN6ZFtfZHArX68k/dwAYCFejV8oF66aWXpkXVtHPnzrSo1gjUGsg/dQMbCFSgV8sH6jve8Y60qJoK2ZBW+6bT8Y0yzMTEhJc0m81Tp07FV5vTlcH94WAQqDWQf+oGNhCoQK8I1N74HTA8NS0pLS8tUKempnQjDp+k9M1CoPrUgSFQayD/1OWHfP3nfnpPvvDkI3+VL1xiIFCBXhGovfEequ6T5YE6NjambqhusKVA1f2zshCoukL6IC89T6DWQP6pyw/5+gQqMBQEam/iezQqUBWWClSJ3/L1Opa1BKoPBOoK5Z+6/JCvT6ACQ0Gg9iYJVHvoN4XWracXwo2d/S3fhXDj6KEE6rNzx757+2XlHH54/9+kq4tO8jmXH/L1CVRgKFYVqIoKGxkfH1/lHR+th2d/LXWsqXTaik1MTKRFkSU2pJYsUL98w7ZyDkfuuiZdXXSSz7n8kK9PoAJDUWSgqvdmfTV9fKjOmY3YQ3Xj1EuzEs3oHzFmuUC1pqymNaVZ7KH38KwpVfBlWeHk5ORs+GaQN5i3xIYA5ZSE3H98+6/zyZev/9xPv5ov7Biozz6+N9+gBgIV6FUBgToTvpiThVjVF3Zs3GJPI1aoqXGgamr84xMFqiobTTXKS59XgRpXsLnsr1KWQI3xGWoNJM/bL7/7d//z+2eSwnz9lfdQz/zy+6d+cnvSoAYCFehVAYGa5XqoFm/+8aEmWcnx48eVpt5DVR01le+hzoYPJq1ErSlQ1aAq+LJshB5qngL1tz+7r2zD0wRqd8mn7EnIWaBa4R9//ZO4MF+/p0D904Pn/y9Z0NMEKtC7YgLVUs1yzs4F6izqiznqPioXlYJWsn//fr3Ta+Pxx6UKVDVl2anZFZY2u+Wl+rJWODU1lYXfevqyvKai2ttMLLEhtfHa177WxxWo0cRS0FoRqN288Y1v3LJliz9MQk6BGsr/wgu9stfvOVCz7D//cSpZFoEK9GpVgTows0VcaagMG9Jvr3vd6+zlxcUXX/zAAw8QqBX15je/2f6JeomZhJwHajzphTlfCNSv5Qs7B+ov/hyoXuIDgQr0qhqBWoiXvOQlFw7D5s2bN2zYcG6wcePG0dHRiy666OUvf7mdMS3/3vSmN23duvXSSy9961vfumPHDutkX3HFFe95z3uuvPLKq6666tprr221Wh/5yEeuv/76PXv2fPKTn9y3b99NN9108ODBz33uc4cOHfrCF75w991333PPPffdd9+DDz74vve9z87FmzZteuUrX1nmQP23R//2yRJ7YrF/XexHkX9Z7J8X+6fI8cV+GDm22K5du+yfaPuJ/buTkHuhh/rwX3ph/PSq5Cx6qM/+IF0WgQr0ag0Fam02ZAmW3LfddpvGyxyo9FC7sZdE9k/82tf+3MVMQk6BatEYF8azq6TXQH3up19NFvQ0gQr0bkCBqu/lLvsbU31rKS0tSCEbUnL6gFn4UlIV3Xrrrf6SKOsUqP/73/+VFEZzn02g/v7f/yFpUAOBCvRqQIHqX+KdCdd/8K8pWbmN79ixIwtfKfJAbYQfzKhQX25avUI2pEIUqOUcCNQVSp63XxzdnX8y8/Wfe+rv84UdA/U3s3fkG9RAoAK9Wj6risqhRpCFbuh8uIi8fiSjlNU3e/13NZrFf3uqcF2lojakKrhSUg3kcy4/5OuvvIe6xECgAr0aUKDqZ6OKRmWkypvhgko2sn///tlwjYgkUJf4GUyvCtmQCrFAfeLbtwx4ePKxaQ35ScmQri46yedcfsjXJ1CBoRhQoOozVL8h6EiQRYGqd4AVqPppKW/5Avmcyw/5+gQqMBTLZ1Vtcqg2G7JCfIZaA/mnLj/k6xOowFAQqLVFoNZA/qnLD/n6BCowFARqbfE71BrI59zABgIV6BWBWlsEag3kc25gA4EK9IpArS0CtQa+c+iyYQ3Pzh1L1wbAkgjU2iJQa+DuG948rIFABXq1fKCuX78+LaqmG2+8MS2qNY+usg0E6so9+oWrhzUQqECvlg/Ue++9Ny2qoKNHj6ZFdce3fAFgkJYP1CzcwyQtqprrrrsuLao7Lj0IAIO0okA1O3fuvOSSS06cqNIX/55//vkjR45s2rTpzjvvTKcBAFColQaqefzxx7du3apr3FfCOeec8653vcuvGwwAGIq5ubkDBw6Mjo6mp+kSs7W1dU63ZEk9BCoAAL3avn376dOn09KK2L17t61/WtoFgQoA6Jc9e/akRRW0wq0gUAEA/bJ37960qIJWuBUEKgCgX6r7Zm9shVtBoAIAUAACFQCAAhCoAAAUgEAFAKAABCoAAAUgUAEAQ9BsNhuNxvz8vI3Pzs7ayMTERFppBRYWFmZmZtLSHC3CFppOaLNGtDJnjUAFAAza9PS0j7RarfHAAtUidmRkJAvxZuMLwbZt2xSZNq4YzkIe20Ob3f7u37/fCtWmjViDNmLpqMAeGxuzxo8ePapAtUJ7qBbUlLGF2lwEKgCgSpSLGreOo+Wouo+WfFmIUq9gf0+dOpWkr8bjQFUFm6R5vVnVVLNahKLUxk+cOKHK9leT9FeznB0CFQAwaElGxm/5Kuc8OPPv6Cr8FKhWzWPVQ9pG4kDVSByo1qAFqpWoAoEKAKgqiy5l6sjIyGyQBKq6leqheqBafNpc84FmtIBUlNq4zaI2JycnPTttUhyoeo9Xaa0g1+KU6wQqAADDR6ACAFAAAhUAgAIQqACAavOvIw0XgQoAQAEIVABASem3MfrW7szMTKvVshL9ctS/l6uf0MQ/v9EPUkdGRvQNXps9bbc/CFQAQElZTOoSSLpwkq6jpJjUz2z0AxgL1PHxcf26Rr+NkSxcOMl/89pvBCoAoKSUl95DtWhUcOpySDaiT0/tbyvQT1o1YtHrP0td1GjfEKgAABSAQAUAoAAEKgAABSBQAQAoAIEKAEABCFQAAApAoAIA+uX06dNpUQWtcCsIVABAv+zduzctqqAVbgWBCgDolz179qRFFbTCrSBQAQB9tH379hW+ZVpCu3fvtvVPS7sgUAEA/TU3N3fgwIHR0VG/ym752draOqdbsiQCFQBQYbt27UqLhoRABQBU1ZkzZ6w3aX/TCcNAoAIAqur888+3QLW/6YRhIFABAJVkHdOLLrrIAtX+lqGTSqACACqsEW4kXgZlWQ8AAM7COeeckxYNCYEKAKgwAhUAgAIQqAAAFIBABQCgAC960YvSoiEhUAEAFUagAgBQAAIVAIACnHvuuWnRkBCoAIAKI1ABACgAgQoAQAEIVAAACnDeeeelRUNCoAIAKoxABQCgAAQqAAAFWLduXVo0JAQqAPTF9PT07OxsWtqmqfZ3fn7eH6aVIuPj48lI/9gq2fqkpd01m820aIAIVADAn3JUgbqsAeSo6ylQG0FaOkAEKgAMmuWEn/qtU7WwsDAzMzMbKD/0V3U0aWRkxOv7w1arZfOq3FihVbbGlXl66C14Zc2bTPVA1UM1aCU2l0eaZvRAVXfQO4VaW/vrS1d5PNUqq0Ety+rE22JT/ZmxRqzEA7UZqJq3qQXZRvk6JAsdsPXr16dFQ0KgAlgr4o6Xh4GNHD58WCFnLGni8ThQLUg0e9KB8zpJBuuhB2HHqR0D1VPfKqv/Z+nVLVDVgk1VO3FH1rdFy7VGPCx9E3xef0kRP1S+eoPia+7LIlCFQAWwVsRBqKAylkwnT57UuFVYOlB9ro6BqnmXCNT81HygzofuaRY6hVqK+rhLBKqW0jFQfYUb7Q6oFjQfuqSuW6DaolXBn5Os/TQ2Q69XJQSqEKgA1oo4UOPgcQpXz4kkUOMIiXkdpWO3DmvHqUmgxvV9pGOg+kOfmg/UeHvFKquCeqte3i1QXRKZY2NjzfCeecepA0agAuiXQ4cO3XHHHRrfuHHj4olrWpIT6nspxjSucsu2RvsjSfXkrEQx5h07yxJrSrOMtN+YVTcuiUxf0LJT4w7lSPiYU+OKTC3ayrUmVqKpaiQJVKumvIwbyaLur8Y1qRk+Q40DVe1oWapji5sNnwdr3unoO8mq0Fjcax+k888/Py0aEgIVqKHzzjtP57h9+/al01C04fbPQKAC6CPL0XVBOgGoHQIVQB+dOXPm/CCdANTOhg0b0qIhIVCBejoTpKVA7RCoyxgdHT127Njp06fTCSVma7t37949e/akE4AubG+xfcZ29XRCudkK2xGalgJDQqAu5eDBg2lRpWzfvj0tAnKqvp/YcVr1TRiYpx+6vLRDuq4VVJ6vspcrUOfm5mrwyte6qjXYCvSV7erVegOmI9sE25C0FDn5GCvPkK5rBRGonR04cGDv3r1paQXVYyvQP7arp0XVVJsN6at8jJVnSNe1ggjUzqxjV4OX7Vl45Z4WAZHavIdRmw3pq3yMlWdI17WCCNTOGkO9B1Bd6Qf+usSJX9JlfHzcr4HSCJdBUeX4ip1OV2ZJ6EKjarbbFVJmwyVDbfaOzRal29LLrDa7em02pK/yMVaeIV3XCirPhTXKdTBwcBbOL+xpkWapOTY2Fk+1wItLrMLk5KSu9qmrnSl0Fageva1wvWwFaiNcb0zXIfMK4+Ea4mpHyT0T+Oy2FI1ruWrQF5G1L4qmGScmJrJ2qHtNvzicX/6tWqq4zh0NeEO0AzTCxdzjcu0k0gzi13A2Nak/YPkYK8+QrmsFEaidDfjgXAv8+pw6B3kPVT3LJFDV4/ROpwI1C2co5XEW3c5JgeqV1YIeip3F4h6qmtLsrZDWfsrTXKqQRVcTTQLV+Oaoca+vkQqpza4+4A3xHUz7w0y4C6ntCbY/NMJ1buNJrfbLL5s6NTU1xNNuPsbKM6TrWkFD/M8mBnowLGvAB+da4CcgZdvSPVSrrNNQlgtUPczCualboHodZbau7p0EqmZXzXygeth7iCaB6hVmw0051CaBOkQD3hDfn1vhttgeqDql+k7ru9xCuKS7TdW+6m+KDFg+xsozpOtaQQRqZwM+ONcCnVM0smygqnIr3ILY+ohxoM6GGz1qasdA1aktC+/WKimTQB1p399YM+YDVYW664XOfY1wCw7N2Ayhrq2YDj1UjWhGtVMhtdnVB7whHqhZ+/WW91CzsO/ZeDOwSdPtjwO0t2gH9tkHKR9j5RnSda2gCy64IC0akoEeDMvqdnDqZJqFD/mSSDgL8Rk/ndaFgqHbw5qJz1nDpdNiWloL3Xb1LOxds+0bcqXTeqSDRS+P0mkrFn88mbfEhvRDEqh6cdath6qXZYrb4Qbql2/YVtohXdcKIlA763Zw2uGhz8y876J8tfOFF+oQmg93+5MsRKafTZrtj+g8UJWLNn7y5Em1o6NxPvTkZtu9t2bon1mhOlU6gLUC3ibQk267epYLVN+TZ6L3MLXjaVf0qNCM8T6ZBGorvKXvs7TCWxFqU/uzKmhZC+EbarPtzl83S2wI3JG7rintkK5rBRGonXU7OJvhpagd5PoOqpcrZWfDu5F+HlG+6ixgf22SziZ+XugWqFnoAaudeCkeqPqrGVWfQMXZ6barZ9EdoW1Pjl8Oxju578y+DysU9ZrP+2Ej7e+gqSlNmgl8f/ZA9QpaljdCoKLkXvziF6dFQ1Kug6HbwdkMvUbFql5WKxEVqHrYbH9xJh+oSez57MkJyHuoWfv85eeyfKBqJGkZWKFuu3q2+OWa7WZJnmmPTQLV9/y4ZtbuobbC+zfagVWeD1QdVl5BdBQQqKuX/+SyPEO6rhVEoHbW7eBUbulFtPqOet3tUafUnA8/Xrz77rt9XOcCveT3k4UmNcIXXrL2DzTVmgJVkzRur/H1AYyF63z42YmNEKg4C/HN1Lrt6lkUqNrhtXP6qz3NqF1aL/hsZP/+/XpR6IXiXzhQUz57Fjqvk5OTOqCscGpqKgv7sy9LIypMgja2xIbA5WOsPEO6rhVEoHZW4MGpU8MSJ4KOvIcKFM4ybMOGDYrVAnf1s+avC1ejDBtSQq9//esvuOCCRx55RA/LGV2//dl9JVyrs3DhhRemRUNSroOhTgdnA+hi/fr1jbrs6rYhF5bM6Ojo5s2bX/rSl77iFa941ate9ZrXvObiiy9+wxvesHXr1omJibe85S2XXXbZ2972tre//e2XX375FVdc8e53v/u9732v9dd37dp19dVXX3vttR/60Ic+/OEPf/SjH73++uut7/7xj3987969+/btO3DgwE033XTzzTd/9rOfvfXWW2+//fY77rjji1/84le+8pV77rnn/vvvf+CBBx566KFvfvObjz766Ktf/Wp7cjZt2nT48OEyB+qT1bfy32v0W7mO6tqcZYC8LVu22B5unVQ7L9dmV7cNOVMyf/jDH373u98999xzv/71r5999tlnnnnm5MmTc3NzP//5z5966inrlz/xxBM/+tGPjh8//oMf/OB73/ved77znccee+zIkSPf+ta3Hn744QcffPDrX/+6BaTF5Je+9KW77rrr85///G233XbLLbccPHjwM5/5zKc//elPfepTN9xwwyc+8Yk9e/Z87GMfs+i1AG61Wh/84AevueaaD3zgA1deeeXLXvYyvX666qqryhyob62+97///em2DUm5jupCzjL6vLORu9pnHu/uYpDWrVt3pv0xqu/q+gizsfizz457pr4ooO8QdKyQRVc2SCfk6AvA/lXejlbyCUghx2z9WL6ee+6573znO/WwzIGalmIVynUwFHJw6iekWftnfDpx6ItLNr5jxw594Wg6XHYna5/RsvbHrvqmEtBXcaAqI23HO3Xq1LZt2xrtuxHoG3C+6x4+fFi7qHZd/0nMQnQ3ApVrdn1xSbNPhEvd+lcK9C3frP2tpZn2fQvUvnWg9V1i69ipqfEgblPtZAUds/Xz4x//OH4YfwmobEO8nlilch0MRR2cOkHMBDr49fsZnVzs1KBMbQZKUE1ayUtyYPXiQFUuNqMLLDSjX2pZ5vmu28z1UPUwCzuwvo6uHups+4IMml1x6JWz8L1fRay/stThkIWOqQp1OPh3l7yd+Ic0RR2z9ZaPsfIM6bpiFcp1MBRycPpZo7n49+k+3gq3D1MF1cna75X9uQmgz+JA9T1W/cKsU6BqUjMKVA9CZe3SgaqaviD/xarVmW5fkDmLcnoi3MMgH6hewRVyzNZe/oJ/5RnSdcUqlOtgKOTgVAc0a193UOPeK82i84JOT61w6xKjkfJ8YQw1tmygzrdvEtBsvy5MAlXvBmftQLXK2uEVqPOdLrHkC9IOn4XjQpmtmqrmcylQvf2TJ0+qTf2VQo7Z2svHWHmGdF2xCuU6GOp3cJ45c2bdunUbNmxIJ2Btq82uXpsNAVavXAdDnQ5Oi1LLUduiLVu2pNOw5tVmV6/NhvRV/pPL8gzpumIVynUw1Ong9EDdvHlzOg1rXm129dpsSF8pun77s/vKNhCoxSrXwVC/g9Nidf369Rs3bkwnYG2rza5emw3pq3L2BQnUwpXrYKjlwWmZeujQobQUa1ttdvXabEhfEahrRLkOBg5OrBG12dVrsyF9RaCuEeU6GLZv337s2LG0tILqsRXoH9vV06Jqqs2G9BWBukaUK1Dn5uZGR0fT0qo5ffp0DbYCfWW7uu0naWnV2CbYhqSlyFGglnNI1xWrUK5AlYMHD6ZFlcJrdqxE1fcTO06rvgkD8+RXd5R2SNcVq1DGQLWjtLov3nfv3v2rX/0qLQVybD+xvSUtrQg7Qu04ZVdfofz1icozpOuKVShjoGbhDTE7XEdHRxvVYWt74MCBdEuGZybcIUBXiZufn9dKjoyMtNpXY29Etw2ZnZ31ix47q+kXfY01w4Vks+jyyHm6yl3H2RGzfcZ2df+PVIKtMO/09uSJb9/Sp+HJx6Z9yE9dyZCuK1ahpIGKVfKLGOvirv7QxZdjzUL+WYXJyclGSFmFrgLVIrPRvnXP2NiYrviqqTPhDl86yVqDqqm4bYS7jPnsjfBd0OQmYrqKrC4nq+XqWsq6nPLU1JSWkrXvrKdZ4nFvzRcBAMPCOaie1HdU5MyEW5Eocvzq50mg6mLo6rDqTiNZu4eqWVTBr7ee9FCb4VZf3pTmzUIPVQ8Xwh3BkpuIxZdoz8JytRRN9RZ0XXi1oFlmwq1DfVt8hA4xgCEiUOvJu6RKo6V7qIpeD1Sb1C1QfTwOVG/Kp2reLBeo8aQsBKqW6IkoatbXIQlUbUuc38nsADAUBGpt6Y1TC6FlA9VTSnVagUamwx3ELL2stY6Bevz4cfUyVZ61f+nvgeqJOBverfVJWRSoflMw66Qq2vVwfvE9yNQ91aqePHlS9/vUStoi5sP9ztQyAAwegYo/i7t9ZUA6AqgWAhUAgAIQqAAAFIBABQCgAAQqAAAFIFABACgAgQoAQAEIVAAACkCgAgBQAAIVAIACEKgAABSAQAUAoAAEKgAABSBQAQAoAIEKAEABCFQAAApAoAIAUAACFQCAAvw/ip79tfsNT80AAAAASUVORK5CYII=>