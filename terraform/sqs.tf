resource "aws_sqs_queue" "rescue_request_dlq" {
  name                      = var.sqs_dlq_name
  message_retention_seconds = 1209600 # 14 days

  tags = {
    Name = "rescue-request-dlq"
  }
}

resource "aws_sqs_queue" "rescue_request_queue" {
  name                       = var.sqs_queue_name
  visibility_timeout_seconds = 300
  message_retention_seconds  = 345600 # 4 days
  receive_wait_time_seconds  = 20     # long polling

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.rescue_request_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "rescue-request-queue"
  }
}

output "sqs_queue_name" {
  value = aws_sqs_queue.rescue_request_queue.name
}

output "sqs_dlq_name" {
  value = aws_sqs_queue.rescue_request_dlq.name
}
