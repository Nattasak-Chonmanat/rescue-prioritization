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


def detect_producer(event: dict) -> str:
    """
    Detect message producer from header.
    - 'rescue-request-service'  → original schema
    - anything else / missing   → resource-request-service schema
    """
    return event.get("header", {}).get("producer", "resource-request-service")


def normalize_rescue_request(event: dict) -> tuple[dict, dict, list]:
    """Parse rescue-request-service schema. Returns (header, data, items)."""
    header = event["header"]
    data = event["body"]["data"]

    location = {
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "locationDetails": data.get("locationDetails"),
        "province": data.get("province"),
        "district": data.get("district"),
        "subdistrict": data.get("subdistrict"),
        "addressLine": data.get("addressLine"),
    }

    normalized = {
        "requestId": data["requestId"],
        "incidentId": data["incidentId"],
        "incidentType": data.get("incidentType"),
        "requestType": data["requestType"],
        "description": data.get("description"),
        "peopleCount": data["peopleCount"],
        "specialNeeds": data.get("specialNeeds", ""),
        "location": location,
        "submittedAt": data["submittedAt"],
        "messageId": header["messageId"],
        "correlationId": header.get("correlationId"),
    }

    return header, normalized, []  


def normalize_resource_request(event: dict) -> tuple[dict, dict, list]:
    """Parse resource-request-service schema. Returns (header, data, items)."""
    header = event["header"]
    body = event["body"]

    loc_obj = body.get("location", {})
    location = {
        "latitude": loc_obj.get("latitude"),
        "longitude": loc_obj.get("longitude"),
        "locationDetails": loc_obj.get("locationDetails"),
        "province": loc_obj.get("province"),
        "district": loc_obj.get("district"),
        "subdistrict": loc_obj.get("subdistrict"),
        "addressLine": loc_obj.get("addressLine"),
    }

    special_needs_raw = body.get("specialNeeds", [])
    if isinstance(special_needs_raw, list):
        special_needs = ",".join(special_needs_raw)
    else:
        special_needs = str(special_needs_raw)

    normalized = {
        "requestId": body["requestId"],
        "incidentId": body["incidentId"],
        "incidentType": body.get("incidentType"),
        "requestType": body["requestType"],
        "description": body.get("description"),
        "peopleCount": body["peopleCount"],
        "specialNeeds": special_needs,
        "location": location,
        "submittedAt": body["submittedAt"],
        "messageId": header["messageId"],
        "correlationId": header.get("correlationId"),
    }

    items = body.get("items", [])

    return header, normalized, items


def lambda_handler(event, context):
    trace_id = event.get("header", {}).get("traceId", "unknown")
    producer = detect_producer(event)

    log("INFO", "CREATE_EVENT_HANDLER_STARTED", trace_id,
        requestId=event.get("header", {}).get("correlationId"),
        messageId=event.get("header", {}).get("messageId"),
        lambdaRequestId=context.aws_request_id,
        producer=producer
    )

    if producer == "rescue-request-service":
        header, data, items = normalize_rescue_request(event)
    else:
        header, data, items = normalize_resource_request(event)

    request_id = data["requestId"]
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "request_id": request_id,
        "incident_id": data["incidentId"],
        "request_type": data["requestType"],
        "people_count": Decimal(str(data["peopleCount"])),
        "special_needs": data["specialNeeds"],
        "description": data.get("description"),
        "location": convert_numbers(data["location"]),
        "submitted_at": data["submittedAt"],
        "created_at": now,
        "status": "PENDING",
        "idemp_key": data["messageId"],
        "producer": producer,
    }

    try:
        table.put_item(
            Item=item,
            ConditionExpression=Attr("request_id").not_exists()
        )
        log("INFO", "RECORD_CREATED", trace_id,
            requestId=request_id,
            incidentId=data["incidentId"],
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
        "incidentId": data["incidentId"],
        "incidentType": data.get("incidentType"),
        "header": header,
        "payload": {
            "submittedAt": data["submittedAt"],
            "description": data.get("description"),
            "location": data["location"],
            "peopleCount": data["peopleCount"],
            "specialNeeds": data["specialNeeds"],
            "requestType": data["requestType"],
        },
        "duplicate": False,
        "eventType": "CREATE",
    }

    if producer != "rescue-request-service":
        result["payload"]["items"] = items

    log("INFO", "CREATE_EVENT_HANDLER_COMPLETED", trace_id,
        requestId=request_id,
        incidentId=data["incidentId"],
        eventType="CREATE",
        producer=producer
    )

    return result