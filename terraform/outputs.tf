output "dynamodb_table_name" {
  value       = aws_dynamodb_table.prioritization_records.name
  description = "Name of the DynamoDB table"
}

output "dynamodb_table_arn" {
  value       = aws_dynamodb_table.prioritization_records.arn
  description = "ARN of the DynamoDB table"
}

output "sqs_queue_url" {
  value       = aws_sqs_queue.rescue_request_queue.url
  description = "URL of the SQS queue"
}

output "sqs_dlq_url" {
  value       = aws_sqs_queue.rescue_request_dlq.url
  description = "URL of the SQS dead letter queue"
}

output "sns_topic_created_arn" {
  value       = aws_sns_topic.rescue_prioritization_events.arn
  description = "ARN of the SNS topic for created events"
}

output "sns_topic_updated_arn" {
  value       = aws_sns_topic.rescue_request_updated.arn
  description = "ARN of the SNS topic for updated events"
}

output "step_functions_state_machine_arn" {
  value       = aws_sfn_state_machine.prioritization_pipeline.arn
  description = "ARN of the Step Functions state machine"
}

output "api_gateway_endpoint" {
  value       = aws_api_gateway_deployment.prioritization_api.invoke_url
  description = "API Gateway endpoint URL"
}
