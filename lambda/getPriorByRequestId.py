import json
import logging
import time
from decimal import Decimal
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("prioritization_records")


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str)
    }

def lambda_handler(event, context):

    start_time = time.time()
    trace_id = context.aws_request_id if context else "unknown"

    log("INFO", "LAMBDA_START", trace_id)

    try:

        log(
            "INFO",
            "REQUEST_RECEIVED",
            trace_id,
            pathParameters=event.get("pathParameters")
        )

        # -------- Path Param --------
        pathParams = event.get("pathParameters")
        request_id = pathParams.get("request_id") if pathParams else None

        if not request_id:
            log(
                "WARNING",
                "VALIDATION_FAILED",
                trace_id,
                reason="request_id is required"
            )

            return response(400, {"message": "request_id is required"})

        log(
            "INFO",
            "DYNAMODB_QUERY_START",
            trace_id,
            requestId=request_id
        )

        result = table.query(
            KeyConditionExpression=Key("request_id").eq(request_id)
        )

        items = result.get("Items", [])

        log(
            "INFO",
            "DYNAMODB_QUERY_COMPLETED",
            trace_id,
            requestId=request_id,
            itemsFound=len(items)
        )

        if not items:

            log(
                "WARNING",
                "RECORD_NOT_FOUND",
                trace_id,
                requestId=request_id
            )

            return response(
                404,
                {"message": f"No record found for request_id: {request_id}"}
            )

        duration_ms = int((time.time() - start_time) * 1000)

        log(
            "INFO",
            "RESPONSE_READY",
            trace_id,
            requestId=request_id,
            latencyMs=duration_ms
        )

        return response(200, items[0])

    except Exception as e:

        duration_ms = int((time.time() - start_time) * 1000)

        log(
            "ERROR",
            "LAMBDA_EXECUTION_FAILED",
            trace_id,
            error=str(e),
            latencyMs=duration_ms
        )

        return response(500, {"message": "Internal server error"})