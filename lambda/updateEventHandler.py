import json
import logging
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("prioritization_records")

ALLOWED_UPDATE_TYPES = {"NOTE", "LOCATION_DETAILS", "PEOPLE_COUNT", "SPECIAL_NEEDS"}


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


def build_update_expression(update_type, update_payload, now, trace_id):
    expression_parts = ["updated_at = :updated_at"]
    attr_values = {":updated_at": now}
    attr_names = {}

    if update_type == "NOTE":
        note = update_payload.get("note")
        if not note:
            log("ERROR", "VALIDATION_FAILED", trace_id,
                updateType=update_type,
                message="updatePayload.note is required"
            )
            raise ValueError("updatePayload.note is required for NOTE update")
        expression_parts.append("#desc = :description")
        attr_values[":description"] = note
        attr_names["#desc"] = "description"

    elif update_type == "LOCATION":
        location = update_payload.get("location")
        if not location:
            log("ERROR", "VALIDATION_FAILED", trace_id,
                updateType=update_type,
                message="updatePayload.location is required"
            )
            raise ValueError("updatePayload.location is required for LOCATION update")
        expression_parts.append("#loc = :location")
        attr_values[":location"] = location
        attr_names["#loc"] = "location"

    elif update_type == "PEOPLE_COUNT":
        people_count = update_payload.get("peopleCount")
        if people_count is None:
            log("ERROR", "VALIDATION_FAILED", trace_id,
                updateType=update_type,
                message="updatePayload.peopleCount is required"
            )
            raise ValueError("updatePayload.peopleCount is required for PEOPLE_COUNT update")
        expression_parts.append("people_count = :people_count")
        attr_values[":people_count"] = people_count

    elif update_type == "SPECIAL_NEEDS":
        special_needs = update_payload.get("specialNeeds")
        if special_needs is None:
            log("ERROR", "VALIDATION_FAILED", trace_id,
                updateType=update_type,
                message="updatePayload.specialNeeds is required"
            )
            raise ValueError("updatePayload.specialNeeds is required for SPECIAL_NEEDS update")
        expression_parts.append("special_needs = :special_needs")
        attr_values[":special_needs"] = special_needs

    return "SET " + ", ".join(expression_parts), attr_values, attr_names


def lambda_handler(event, context):

    trace_id = event.get("header", {}).get("traceId", "unknown")

    header = event["header"]
    payload = event["body"]

    request_id = payload["requestId"]
    incident_id = payload["incidentId"]
    update_type = payload.get("updateType")
    update_payload = payload.get("updatePayload", {})

    log("INFO", "UPDATE_EVENT_HANDLER_STARTED", trace_id,
        requestId=request_id,
        incidentId=incident_id,
        updateType=update_type,
        lambdaRequestId=context.aws_request_id
    )

    if not update_type:
        log("ERROR", "VALIDATION_FAILED", trace_id,
            requestId=request_id,
            message="updateType is required"
        )
        raise ValueError("updateType is required")

    if update_type not in ALLOWED_UPDATE_TYPES:
        log("ERROR", "VALIDATION_FAILED", trace_id,
            requestId=request_id,
            updateType=update_type,
            message=f"Invalid updateType, must be one of {ALLOWED_UPDATE_TYPES}"
        )
        raise ValueError(f"Invalid updateType: {update_type}, must be one of {ALLOWED_UPDATE_TYPES}")

    now = datetime.now(timezone.utc).isoformat()

    try:
        update_expression, attr_values, attr_names = build_update_expression(
            update_type, update_payload, now, trace_id
        )

        kwargs = {
            "Key": {
                "request_id": request_id,
                "incident_id": incident_id
            },
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": attr_values,
            "ConditionExpression": Attr("request_id").exists()
        }

        if attr_names:
            kwargs["ExpressionAttributeNames"] = attr_names

        table.update_item(**kwargs)

        log("INFO", "RECORD_UPDATED", trace_id,
            requestId=request_id,
            incidentId=incident_id,
            updateType=update_type
        )

    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        log("ERROR", "RECORD_NOT_FOUND", trace_id,
            requestId=request_id,
            incidentId=incident_id,
            message="ConditionalCheckFailed on update"
        )
        raise ValueError(f"Record not found for request_id: {request_id}")
    except Exception as e:
        log("ERROR", "DYNAMODB_UPDATE_FAILED", trace_id,
            requestId=request_id,
            error=str(e)
        )
        raise

    log("INFO", "UPDATE_EVENT_HANDLER_COMPLETED", trace_id,
        requestId=request_id,
        incidentId=incident_id,
        updateType=update_type,
        eventType="UPDATE"
    )

    return {
        "requestId": request_id,
        "incidentId": incident_id,
        "header": header,
        "duplicate": False,
        "eventType": "UPDATE"
    }