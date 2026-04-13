import json
import logging
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("prioritization_records")


def log(level, event_name, trace_id, **kwargs):
    """Structured JSON logging"""
    entry = {
        "level": level,
        "event": event_name,
        "traceId": trace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs
    }
    log_fn = getattr(logger, level.lower(), logger.info)
    log_fn(json.dumps(entry, default=str))


def convert_numbers(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, int):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: convert_numbers(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_numbers(v) for v in obj]
    return obj


def lambda_handler(event, context):

    trace_id = event.get("header", {}).get("traceId", "unknown")

    log("INFO", "CREATE_EVENT_HANDLER_STARTED", trace_id,
        requestId=event.get("header", {}).get("correlationId"),
        messageId=event.get("header", {}).get("messageId"),
        lambdaRequestId=context.aws_request_id
    )

    header = event["header"]
    payload = event["body"]
    request_id = payload["requestId"]

    now = datetime.now(timezone.utc).isoformat()

    item = {
        "request_id": request_id,
        "incident_id": payload["incidentId"],
        "request_type": payload["requestType"],
        "people_count": Decimal(str(payload["peopleCount"])),
        "special_needs": payload.get("specialNeeds", []),
        "description": payload.get("description"),
        "location": convert_numbers(payload["location"]),
        "submitted_at": payload["submittedAt"],
        "created_at": now,
        "status": "PENDING",
        "idemp_key": header["messageId"]
    }

    try:
        table.put_item(
            Item=item,
            ConditionExpression=Attr("request_id").not_exists()
        )
        log("INFO", "RECORD_CREATED", trace_id,
            requestId=request_id,
            incidentId=payload["incidentId"],
            status="PENDING"
        )

    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        log("WARN", "DUPLICATE_REQUEST", trace_id,
            requestId=request_id,
            message="request_id already exists, skipping"
        )
        return {"duplicate": True}

    except Exception as e:
        log("ERROR", "DYNAMODB_PUT_FAILED", trace_id,
            requestId=request_id,
            error=str(e)
        )
        raise

    result = {
        "requestId": request_id,
        "incidentId": payload["incidentId"],
        "header": header,
        "payload": {
            "submittedAt": payload["submittedAt"],
            "description": payload.get("description"),
            "location": payload["location"],
            "peopleCount": payload["peopleCount"],
            "specialNeeds": payload.get("specialNeeds", []),
            "requestType": payload["requestType"]
        },
        "duplicate": False,
        "eventType": "CREATE"
    }

    log("INFO", "CREATE_EVENT_HANDLER_COMPLETED", trace_id,
        requestId=request_id,
        incidentId=payload["incidentId"],
        eventType="CREATE"
    )

    return result