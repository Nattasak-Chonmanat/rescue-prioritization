import json
from decimal import Decimal, InvalidOperation
import logging
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("prioritization_records")


VALID_PRIORITY_LEVELS = {"LOW", "NORMAL", "HIGH", "CRITICAL"}
VALID_STATUSES = {"PENDING", "EVALUATED", "RE_EVALUATE", "FAILED"}
VALID_SORT_ORDERS = {"asc", "desc"}
VALID_SORT_BY = {"score"}

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


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str)
    }


def validate_params(params):
    errors = []

    priority_level = params.get("priority_level")
    if priority_level and priority_level not in VALID_PRIORITY_LEVELS:
        errors.append(f"priority_level must be one of {sorted(VALID_PRIORITY_LEVELS)}")

    status = params.get("status")
    if status and status not in VALID_STATUSES:
        errors.append(f"status must be one of {sorted(VALID_STATUSES)}")

    sort_order = params.get("sortOrder", "asc")
    if sort_order not in VALID_SORT_ORDERS:
        errors.append("sortOrder must be 'asc' or 'desc'")

    sort_by = params.get("sortBy")
    if sort_by and sort_by not in VALID_SORT_BY:
        errors.append(f"sortBy must be one of {sorted(VALID_SORT_BY)}")

    for field in ["min_score", "max_score"]:
        value = params.get(field)
        if value is not None:
            try:
                Decimal(str(value))
            except InvalidOperation:
                errors.append(f"{field} must be a valid decimal number")

    min_score = params.get("min_score")
    max_score = params.get("max_score")
    if min_score is not None and max_score is not None:
        if Decimal(str(min_score)) > Decimal(str(max_score)):
            errors.append("min_score must be less than or equal to max_score")

    for field in ["limit", "offset"]:
        value = params.get(field)
        if value is not None:
            try:
                int_value = int(value)
                if int_value < 0:
                    errors.append(f"{field} must be a non-negative integer")
            except (ValueError, TypeError):
                errors.append(f"{field} must be an integer")

    return errors


def lambda_handler(event, context):

    print("EVENT:", json.dumps(event))

    # --- Path Param ---
    incident_id = event.get("pathParameters", {}).get("incident_id")
    if not incident_id:
        return response(400, {"message": "incident_id is required"})

    # --- Query Params ---
    query_params = event.get("queryStringParameters") or {}

    errors = validate_params(query_params)
    if errors:
        return response(400, {"message": "Validation failed", "errors": errors})

    priority_level = query_params.get("priorityLevel")
    status = query_params.get("status")
    min_score = query_params.get("minScore")
    max_score = query_params.get("maxScore")
    sort_by = query_params.get("sortBy")
    sort_order = query_params.get("sortOrder", "asc")
    limit = int(query_params.get("limit", 20))
    offset = int(query_params.get("offset", 0))

    try:
        key_condition = Key("incident_id").eq(incident_id)

        filter_expressions = []

        if priority_level:
            filter_expressions.append(Attr("priority_level").eq(priority_level))
        if status:
            filter_expressions.append(Attr("status").eq(status))
        if min_score is not None:
            filter_expressions.append(Attr("priority_score").gte(Decimal(str(min_score))))
        if max_score is not None:
            filter_expressions.append(Attr("priority_score").lte(Decimal(str(max_score))))

        combined_filter = None
        for expr in filter_expressions:
            combined_filter = expr if combined_filter is None else combined_filter & expr

        query_kwargs = {
            "IndexName": "incident_id-index",  
            "KeyConditionExpression": key_condition,
        }
        if combined_filter:
            query_kwargs["FilterExpression"] = combined_filter

        items = []
        last_evaluated_key = None

        while True:
            if last_evaluated_key:
                query_kwargs["ExclusiveStartKey"] = last_evaluated_key

            result = table.query(**query_kwargs)
            items.extend(result.get("Items", []))
            last_evaluated_key = result.get("LastEvaluatedKey")

            if not last_evaluated_key:
                break

        # --- Sort ---
        if sort_by == "score":
            items.sort(
                key=lambda x: x.get("priority_score", Decimal("0")),
                reverse=(sort_order == "desc")
            )

        # --- Pagination ---
        total = len(items)
        paginated = items[offset: offset + limit]

        return response(200, {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": paginated
        })

    except Exception as e:
        print(f"Query failed: {e}")
        return response(500, {"message": "Internal server error"})