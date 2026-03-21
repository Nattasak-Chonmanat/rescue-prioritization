import json
import os
import random
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import boto3
from boto3.dynamodb.conditions import Key
from google import genai

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("prioritization_records")

PRIORITY_LEVELS = ["LOW", "NORMAL", "HIGH", "CRITICAL"]

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def evaluate_with_ai(payload):
    prompt = f"""
    You are an emergency rescue prioritization system.
    You MUST return valid JSON only. No markdown, no explanation outside JSON.

    Return exactly this format:
    {{
      "priority_score": <float 0.0-1.0>,
      "priority_level": <"LOW" | "NORMAL" | "HIGH" | "CRITICAL">,
      "reason": <brief explanation in English>
    }}

    Request details:
    - People count: {payload.get("people_count")}
    - Special needs: {payload.get("special_needs", [])}
    - Description: {payload.get("description")}
    - Location: {payload.get("location")}
    - Request Type: {payload.get("request_type")}
    """

    response = client.models.generate_content(
        model="gemma-3-27b-it",
        contents=prompt
    )
    text = response.text.strip()

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    result = json.loads(text)

    if result["priority_level"] not in PRIORITY_LEVELS:
        print(f"Invalid priority_level from model: {result['priority_level']}")
        raise ValueError(f"Invalid priority_level from model: {result['priority_level']}")
    try:
        Decimal(str(result["priority_score"]))
    except InvalidOperation:
        print(f"Invalid priority_score from model: {result['priority_score']}")
        raise ValueError(f"Invalid priority_score from model: {result['priority_score']}")

    return result, "gemma-3-27b-it"


def evaluate_with_fallback(payload):
    print("Using fallback random evaluation")
    return {
        "priority_score": round(random.uniform(0, 1), 4),
        "priority_level": random.choice(PRIORITY_LEVELS),
        "reason": "fallback"
    }, "fallback"


def get_record(request_id, incident_id):
    """Query record จาก DynamoDB ด้วย request_id + incident_id"""
    try:
        response = table.get_item(
            Key={
                "request_id": request_id,
                "incident_id": incident_id
            }
        )
        item = response.get("Item")
        if not item:
            raise ValueError(f"Record not found for request_id: {request_id}")
        return item
    except Exception as e:
        print(f"DynamoDB get_item failed: {e}")
        raise


def update_status_to_re_evaluate(request_id, incident_id):
    try:
        table.update_item(
            Key={
                "request_id": request_id,
                "incident_id": incident_id
            },
            UpdateExpression="SET #s = :status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":status": "RE_EVALUATE"},
            ConditionExpression="attribute_exists(request_id)"
        )
        print(f"Status updated to RE_EVALUATE for request_id: {request_id}")
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        raise ValueError(f"Record not found for request_id: {request_id}")
    except Exception as e:
        print(f"Failed to update status to RE_EVALUATE: {e}")
        raise


def lambda_handler(event, context):

    print("EVENT:", json.dumps(event))

    request_id = event["requestId"]
    incident_id = event["incidentId"]
    event_type = event.get("eventType", "CREATE")

    print(f"eventType: {event_type}")

    evaluate_id = str(uuid.uuid4())

    # ถ้าเป็น UPDATE ให้ query record จาก DynamoDB แล้วอัปเดต status เป็น RE_EVALUATE
    if event_type == "UPDATE":
        update_status_to_re_evaluate(request_id, incident_id)
        record = get_record(request_id, incident_id)
        payload = record  # ใช้ข้อมูลจาก DynamoDB ทั้งหมด (snake_case)
        header = event.get("header", {})
    else:
        # CREATE — ใช้ payload ที่ส่งมาจาก createEventHandler ตามเดิม
        payload = event["payload"]
        header = event["header"]

    print("PAYLOAD:", json.dumps(payload, default=str))

    try:
        evaluation, model_id = evaluate_with_ai(payload)
        print(evaluation)
    except Exception as e:
        print(f"AI evaluation failed: {e}")
        evaluation, model_id = evaluate_with_fallback(payload)

    priority_score = Decimal(str(evaluation["priority_score"]))
    priority_level = evaluation["priority_level"]
    reason = evaluation.get("reason", "")

    now = datetime.now(timezone.utc).isoformat()

    try:
        table.update_item(
            Key={
                "request_id": request_id,
                "incident_id": incident_id
            },
            UpdateExpression="""
                SET priority_score = :ps,
                    priority_level = :pl,
                    evaluate_id = :eid,
                    model_id = :mid,
                    evaluate_reason = :reason,
                    last_evaluated_at = :t,
                    #s = :status
            """,
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":ps": priority_score,
                ":pl": priority_level,
                ":eid": evaluate_id,
                ":mid": model_id,
                ":reason": reason,
                ":t": now,
                ":status": "EVALUATED"
            },
            ConditionExpression="attribute_exists(request_id)"
        )
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        print(f"request_id not found in DynamoDB: {request_id}")
        raise ValueError(f"Record not found for request_id: {request_id}")
    except Exception as e:
        print(f"DynamoDB update_item failed: {e}")
        raise

    # สร้าง header สำหรับ publish event
    correlation_id = header.get("messageId") if header else event.get("correlationId")
    sns_header = {
        "messageType": "RescueRequestEvaluatedEvent",
        "correlationId": correlation_id,
        "sentAt": now,
        "version": 1
    }

    print(f"Payload before return: {payload}")

    result = {
        "requestId": request_id,
        "incidentId": incident_id,
        "evaluateId": evaluate_id,
        "requestType": payload.get("request_type") or payload.get("requestType"),
        "priorityScore": float(priority_score),
        "priorityLevel": priority_level,
        "evaluateReason": reason,
        "lastEvaluatedAt": now,
        "description": payload.get("description"),
        "location": payload.get("location"),
        "peopleCount": payload.get("people_count") or payload.get("peopleCount"),
        "specialNeeds": payload.get("special_needs") or payload.get("specialNeeds", []),
        "header": sns_header
    }

    print("RESULT:", json.dumps(result, default=str))

    return result