import json
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("prioritization_records")

ALLOWED_UPDATE_TYPES = {"NOTE", "LOCATION_DETAILS", "PEOPLE_COUNT", "SPECIAL_NEEDS"}


def build_update_expression(update_type, update_payload, now):
    """สร้าง UpdateExpression ตาม updateType ที่รับมา"""

    expression_parts = ["updated_at = :updated_at"]
    attr_values = {":updated_at": now}
    attr_names = {}

    if update_type == "NOTE":
        note = update_payload.get("note")
        if not note:
            raise ValueError("updatePayload.note is required for NOTE update")
        expression_parts.append("#desc = :description")
        attr_values[":description"] = note
        attr_names["#desc"] = "description"

    elif update_type == "LOCATION":
        location = update_payload.get("location")
        if not location:
            raise ValueError("updatePayload.location is required for LOCATION update")
        expression_parts.append("#loc = :location")
        attr_values[":location"] = location
        attr_names["#loc"] = "location"

    elif update_type == "PEOPLE_COUNT":
        people_count = update_payload.get("peopleCount")
        if people_count is None:
            raise ValueError("updatePayload.peopleCount is required for PEOPLE_COUNT update")
        expression_parts.append("people_count = :people_count")
        attr_values[":people_count"] = people_count

    elif update_type == "SPECIAL_NEEDS":
        special_needs = update_payload.get("specialNeeds")
        if special_needs is None:
            raise ValueError("updatePayload.specialNeeds is required for SPECIAL_NEEDS update")
        expression_parts.append("special_needs = :special_needs")
        attr_values[":special_needs"] = special_needs


    return "SET " + ", ".join(expression_parts), attr_values, attr_names


def lambda_handler(event, context):

    print("EVENT:", json.dumps(event))

    # if "Message" in body:
    #     body = json.loads(body["Message"])

    header = event["header"]
    payload = event["body"]

    request_id = payload["requestId"]
    incident_id = payload["incidentId"]
    update_type = payload.get("updateType")
    update_payload = payload.get("updatePayload", {})

    # validate updateType
    if not update_type:
        raise ValueError("updateType is required")
    if update_type not in ALLOWED_UPDATE_TYPES:
        raise ValueError(f"Invalid updateType: {update_type}, must be one of {ALLOWED_UPDATE_TYPES}")

    now = datetime.now(timezone.utc).isoformat()

    try:
        update_expression, attr_values, attr_names = build_update_expression(
            update_type, update_payload, now
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
        print(f"Updated request_id: {request_id}, updateType: {update_type}")

    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        print(f"request_id not found: {request_id}")
        raise ValueError(f"Record not found for request_id: {request_id}")
    except Exception as e:
        print(f"DynamoDB update_item failed: {e}")
        raise

    # return ต่อให้ EvaluateWorker ทํางานต่อ
    return {
        "requestId": request_id,
        "incidentId": incident_id,
        "header": header,
        "duplicate": False,
        "eventType": "UPDATE"
    }