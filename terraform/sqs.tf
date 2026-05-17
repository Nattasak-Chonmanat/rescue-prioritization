resource "aws_sqs_queue" "rescue_request_created_dlq" {
  name                      = "rescue-request-created-queue-dlq"
  message_retention_seconds = 604800 # 7 days
}

resource "aws_sqs_queue" "rescue_request_created_queue" {
  name                       = "rescue-request-created-queue"
  visibility_timeout_seconds = 60      # 1 minute
  message_retention_seconds  = 604800  # 7 days
  delay_seconds              = 0       # default
  max_message_size           = 1048576  # 1 MiB (default)
  receive_wait_time_seconds  = 0       # default (short polling)

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.rescue_request_created_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "rescue-request-created-queue"
  }
}

resource "aws_sqs_queue_redrive_allow_policy" "rescue_request_created_queue_redrive_allow" {
  queue_url = aws_sqs_queue.rescue_request_created_dlq.url

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.rescue_request_created_queue.arn]
  })
}
