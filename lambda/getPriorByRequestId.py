import json
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("prioritization_records")


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str)
    }


def lambda_handler(event, context):

    print("EVENT:", json.dumps(event))

    # --- Path Param ---
    pathParams = event.get("pathParameters")
    request_id = pathParams.get("request_id") if pathParams else None
    if not request_id:
        return response(400, {"message": "request_id is required"})

    try:
        result = table.query(
            KeyConditionExpression=Key("request_id").eq(request_id)
        )

        items = result.get("Items", [])

        if not items:
            return response(404, {"message": f"No record found for request_id: {request_id}"})

        return response(200, items[0])

    except Exception as e:
        print(f"Query failed: {e}")
        return response(500, {"message": "Internal server error"})