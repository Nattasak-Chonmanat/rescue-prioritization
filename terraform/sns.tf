resource "aws_sns_topic" "rescue_prioritization_events" {
  name              = var.sns_topic_created
  kms_master_key_id = "alias/aws/sns"

  tags = {
    Name = "rescue-prioritization-events"
  }
}

resource "aws_sns_topic" "rescue_request_updated" {
  name              = var.sns_topic_updated
  kms_master_key_id = "alias/aws/sns"

  tags = {
    Name = "rescue-request-updated"
  }
}

# Dead letter queue for failed SNS messages
resource "aws_sqs_queue" "sns_dlq" {
  name                      = "rescue-request-sns-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = {
    Name = "rescue-request-sns-dlq"
  }
}

# Redrive policy for SNS to SQS
resource "aws_sns_topic_subscription" "prioritization_events_dlq" {
  topic_arn            = aws_sns_topic.rescue_prioritization_events.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.sns_dlq.arn
  redrive_policy       = jsonencode({ deadLetterTargetArn = aws_sqs_queue.sns_dlq.arn })
  raw_message_delivery = true
}
