import json


def lambda_handler(event, context):

    print("EVENT:", json.dumps(event))

    body = json.loads(event["body"])

    if "Message" in body:
        body = json.loads(body["Message"])

    print("PARSED BODY:", json.dumps(body))

    return body