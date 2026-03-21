import json
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("prioritization_records")


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

    print("EVENT:", json.dumps(event))

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
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        print(f"Duplicate request_id: {request_id}, skipping.")
        return {"duplicate": True}
    except Exception as e:
        print(f"DynamoDB put_item failed: {e}")
        raise

    return {
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