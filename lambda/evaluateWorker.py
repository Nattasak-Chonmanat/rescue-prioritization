import json
import logging
import os
# import random
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import boto3
from boto3.dynamodb.conditions import Key
from google import genai
from google.genai import types

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("prioritization_records")

PRIORITY_LEVELS = ["LOW", "NORMAL", "HIGH", "CRITICAL"]

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(
        timeout=10_000  # 10 seconds 
    )
)

def log(level, event_name, trace_id, **kwargs):
    entry = {
        "level": level,
        "event": event_name,
        "traceId": trace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs
    }
    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(json.dumps(entry, default=str))


def evaluate_with_ai(payload, trace_id):
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

    log("INFO", "AI_EVALUATION_STARTED", trace_id,
        model="gemma-3-27b-it"
    )

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
        log("ERROR", "AI_INVALID_PRIORITY_LEVEL", trace_id,
            priorityLevel=result["priority_level"]
        )
        raise ValueError(f"Invalid priority_level from model: {result['priority_level']}")

    try:
        Decimal(str(result["priority_score"]))
    except InvalidOperation:
        log("ERROR", "AI_INVALID_PRIORITY_SCORE", trace_id,
            priorityScore=result["priority_score"]
        )
        raise ValueError(f"Invalid priority_score from model: {result['priority_score']}")

    log("INFO", "AI_EVALUATION_COMPLETED", trace_id,
        priorityLevel=result["priority_level"],
        priorityScore=result["priority_score"]
    )

    return result, "gemma-3-27b-it"


def evaluate_with_fallback(payload, trace_id):
    """
    Rule-based fallback evaluation อิงจากหลักการ Triage และ Disaster Response
    อ้างอิง:
    - START Triage System (Simple Triage and Rapid Treatment)
    - SALT Triage (Sort, Assess, Lifesaving Interventions, Treatment/Transport)
    - WHO Emergency Triage Assessment and Treatment (ETAT)
    - FEMA Incident Command System Priority Guidelines
    """

    log("WARN", "AI_EVALUATION_FALLBACK", trace_id,
        message="AI failed, using rule-based fallback"
    )

    score = 0.0
    reasons = []

    people_count = int(payload.get("people_count") or payload.get("peopleCount") or 1)
    special_needs = payload.get("special_needs") or payload.get("specialNeeds") or []
    description = (payload.get("description") or "").lower()
    request_type = (payload.get("request_type") or payload.get("requestType") or "").lower()


    if people_count >= 10:
        score += 0.30
        reasons.append(f"Large group ({people_count} people)")
    elif people_count >= 5:
        score += 0.20
        reasons.append(f"Medium group ({people_count} people)")
    elif people_count >= 2:
        score += 0.10
        reasons.append(f"Small group ({people_count} people)")
    else:
        score += 0.05
        reasons.append("Individual")


    special_needs_lower = [s.lower() for s in special_needs]
    special_needs_score = 0.0

    if "bedridden" in special_needs_lower:
        special_needs_score = max(special_needs_score, 0.30)
        reasons.append("Bedridden patient (immobile, high risk)")
    if "infant" in special_needs_lower or "newborn" in special_needs_lower:
        special_needs_score = max(special_needs_score, 0.30)
        reasons.append("Infant/Newborn (critical vulnerability)")
    if "children" in special_needs_lower:
        special_needs_score = max(special_needs_score, 0.20)
        reasons.append("Children present")
    if "elderly" in special_needs_lower:
        special_needs_score = max(special_needs_score, 0.20)
        reasons.append("Elderly person (high risk)")
    if "pregnant" in special_needs_lower:
        special_needs_score = max(special_needs_score, 0.25)
        reasons.append("Pregnant person (high risk)")
    if "disability" in special_needs_lower:
        special_needs_score = max(special_needs_score, 0.15)
        reasons.append("Person with disability")
    if "medical_equipment" in special_needs_lower:
        special_needs_score = max(special_needs_score, 0.25)
        reasons.append("Requires medical equipment (life-dependent)")

    score += special_needs_score


    life_threatening_keywords = [
        "จม", "drown",
        "ไฟ", "fire", "เพลิง",
        "หมดสติ", "unconscious", "ไม่รู้สึกตัว",
        "หายใจไม่ออก", "breathing",
        "เลือดออก", "bleeding",
        "บาดเจ็บ", "injury", "injured",
        "ติดอยู่", "trapped", "stuck",
        "ถูกกด", "crushed", "ถูกทับ",
        "น้ำท่วมเร็ว", "rising water", "น้ำขึ้นสูง"
    ]
    urgent_keywords = [
        "ช่วยด่วน", "urgent", "emergency",
        "อันตราย", "danger",
        "วิกฤต", "critical",
        "ไม่มีอาหาร", "no food", "หิว",
        "ไม่มีน้ำ", "no water"
    ]

    if any(kw in description for kw in life_threatening_keywords):
        score += 0.25
        reasons.append("Life-threatening situation detected in description")
    elif any(kw in description for kw in urgent_keywords):
        score += 0.10
        reasons.append("Urgent situation detected in description")


    request_type_scores = {
        "flood_rescue":     0.15,
        "fire_rescue":      0.15,
        "collapse_rescue":  0.15,
        "medical":          0.12,
        "evacuation":       0.10,
        "supply":           0.05,
        "other":            0.05,
    }
    type_score = request_type_scores.get(request_type, 0.05)
    score += type_score
    reasons.append(f"Request type: {request_type}")

    score = min(round(score, 4), 1.0)


    if score >= 0.75:
        priority_level = "CRITICAL"
    elif score >= 0.50:
        priority_level = "HIGH"
    elif score >= 0.25:
        priority_level = "NORMAL"
    else:
        priority_level = "LOW"

    reason = f"[Rule-based fallback] {'; '.join(reasons)}. Score: {score}"

    log("INFO", "FALLBACK_EVALUATION_COMPLETED", trace_id,
        priorityLevel=priority_level,
        priorityScore=score,
        reason=reason
    )

    return {
        "priority_score": score,
        "priority_level": priority_level,
        "reason": reason
    }, "rule-based-fallback"


def get_record(request_id, incident_id, trace_id):
    try:
        response = table.get_item(
            Key={
                "request_id": request_id,
                "incident_id": incident_id
            }
        )
        item = response.get("Item")
        if not item:
            log("ERROR", "RECORD_NOT_FOUND", trace_id,
                requestId=request_id,
                incidentId=incident_id
            )
            raise ValueError(f"Record not found for request_id: {request_id}")
        return item
    except Exception as e:
        log("ERROR", "DYNAMODB_GET_FAILED", trace_id,
            requestId=request_id,
            error=str(e)
        )
        raise


def update_status_to_re_evaluate(request_id, incident_id, trace_id):
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
        log("INFO", "STATUS_UPDATED_RE_EVALUATE", trace_id,
            requestId=request_id,
            incidentId=incident_id
        )
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        log("ERROR", "RECORD_NOT_FOUND", trace_id,
            requestId=request_id,
            message="ConditionalCheckFailed on RE_EVALUATE update"
        )
        raise ValueError(f"Record not found for request_id: {request_id}")
    except Exception as e:
        log("ERROR", "DYNAMODB_UPDATE_RE_EVALUATE_FAILED", trace_id,
            requestId=request_id,
            error=str(e)
        )
        raise
    
def update_status_to_failed(request_id, incident_id, trace_id, error_reason=""):
    try:
        table.update_item(
            Key={
                "request_id": request_id,
                "incident_id": incident_id
            },
            UpdateExpression="SET #s = :status, failed_reason = :reason",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":status": "FAILED",
                ":reason": error_reason
            }
        )
        log("INFO", "STATUS_UPDATED_FAILED", trace_id,
            requestId=request_id,
            incidentId=incident_id,
            failedReason=error_reason
        )
    except Exception as e:
        log("ERROR", "DYNAMODB_UPDATE_FAILED_STATUS_FAILED", trace_id,
            requestId=request_id,
            error=str(e)
        )
        raise


def lambda_handler(event, context):

    trace_id = event.get("header", {}).get("traceId", "unknown")

    request_id = event["requestId"]
    incident_id = event["incidentId"]
    event_type = event.get("eventType", "CREATE")

    log("INFO", "EVALUATE_WORKER_STARTED", trace_id,
        requestId=request_id,
        incidentId=incident_id,
        eventType=event_type,
        lambdaRequestId=context.aws_request_id
    )

    evaluate_id = str(uuid.uuid4())

    if event_type == "UPDATE":
        messageType = "RescueRequestReEvaluateEvent"
        update_status_to_re_evaluate(request_id, incident_id, trace_id)
        record = get_record(request_id, incident_id, trace_id)
        payload = record
        header = event.get("header", {})
    else:
        messageType = "RescueRequestEvaluateEvent"
        payload = event["payload"]
        header = event["header"]

    # try:
    #     evaluation, model_id = evaluate_with_ai(payload, trace_id)
    # except Exception as e:
    #     log("WARN", "AI_EVALUATION_FAILED", trace_id,
    #         requestId=request_id,
    #         error=str(e)
    #     )
    #     evaluation, model_id = evaluate_with_fallback(payload, trace_id)
        
    try:
        evaluation, model_id = evaluate_with_ai(payload, trace_id)
    except Exception as e:
        log("WARN", "AI_EVALUATION_FAILED", trace_id,
            requestId=request_id,
            error=str(e)
        )
        try:
            evaluation, model_id = evaluate_with_fallback(payload, trace_id)
        except Exception as fallback_error:
            log("ERROR", "FALLBACK_EVALUATION_FAILED", trace_id,
                requestId=request_id,
                error=str(fallback_error)
            )
            update_status_to_failed(
                request_id, incident_id, trace_id,
                error_reason=f"AI failed: {str(e)} | Fallback failed: {str(fallback_error)}"
            )
            raise

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
        log("INFO", "RECORD_EVALUATED", trace_id,
            requestId=request_id,
            incidentId=incident_id,
            evaluateId=evaluate_id,
            priorityLevel=priority_level,
            priorityScore=float(priority_score),
            modelId=model_id
        )
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        log("ERROR", "RECORD_NOT_FOUND", trace_id,
            requestId=request_id,
            message="ConditionalCheckFailed on EVALUATED update"
        )
        raise ValueError(f"Record not found for request_id: {request_id}")
    except Exception as e:
        log("ERROR", "DYNAMODB_UPDATE_FAILED", trace_id,
            requestId=request_id,
            error=str(e)
        )
        raise

    correlation_id = header.get("messageId") if header else event.get("correlationId")
    sns_header = {
        "messageType": messageType,
        "traceId": trace_id,
        "correlationId": correlation_id,
        "sentAt": now,
        "version": 1
    }
    
    body = {
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
    }

    result = {
        "body": body,
        "header": sns_header
    }

    log("INFO", "EVALUATE_WORKER_COMPLETED", trace_id,
        requestId=request_id,
        incidentId=incident_id,
        evaluateId=evaluate_id,
        priorityLevel=priority_level,
        priorityScore=float(priority_score),
        eventType=event_type
    )

    return result