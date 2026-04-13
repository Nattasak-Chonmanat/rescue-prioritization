import json
import logging
from datetime import datetime, timezone

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

def lambda_handler(event, context):
    
    log("INFO", "EVENT_HANDLER_STARTED", None,
        lambdaRequestId=context.aws_request_id,
        eventKeys=list(event.keys()) if isinstance(event, dict) else "invalid"
    )

    try:
        body = json.loads(event["body"])
        trace_id = body.get("header", {}).get("traceId", "unknown") if isinstance(body.get("header"), dict) else "unknown"
        log("INFO", "EVENT_BODY_PARSED", trace_id,
            bodyKeys=list(body.keys()) if isinstance(body, dict) else "invalid"
        )
    except json.JSONDecodeError as e:
        log("ERROR", "EVENT_BODY_PARSE_FAILED", trace_id,
            error=str(e),
            receivedBody=str(event.get("body", ""))[:200]
        )
        raise
    except KeyError as e:
        log("ERROR", "MISSING_EVENT_BODY", trace_id,
            missingKey=str(e)
        )
        raise

    if "Message" in body:
        try:
            body = json.loads(body["Message"])
            log("INFO", "EVENT_MESSAGE_UNWRAPPED", trace_id,
                extractedMessageKeys=list(body.keys()) if isinstance(body, dict) else "invalid"
            )
        except json.JSONDecodeError as e:
            log("ERROR", "EVENT_MESSAGE_PARSE_FAILED", trace_id,
                error=str(e)
            )
            raise

    log("INFO", "EVENT_HANDLER_COMPLETED", trace_id,
        parsedBodyKeys=list(body.keys()) if isinstance(body, dict) else "invalid"
    )

    return body