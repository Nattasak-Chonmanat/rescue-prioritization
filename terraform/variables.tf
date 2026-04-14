variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "rescue-prioritization"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "dynamodb_table_name" {
  type    = string
  default = "prioritization_records"
}

variable "sqs_queue_name" {
  type    = string
  default = "rescue-request-created"
}

variable "sqs_dlq_name" {
  type    = string
  default = "rescue-request-created-dlq"
}

variable "sns_topic_created" {
  type    = string
  default = "rescue-prioritization-events-v1"
}

variable "sns_topic_updated" {
  type    = string
  default = "rescue-request-updated-v1"
}

variable "lambda_timeout" {
  type    = number
  default = 60
}

variable "lambda_memory_size" {
  type    = number
  default = 256
}

variable "gemini_api_key" {
  type        = string
  sensitive   = true
  description = "Google Gemini API key for AI-based prioritization"
}
