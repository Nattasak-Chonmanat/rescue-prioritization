# Rescue Request Prioritization Pipeline - Terraform Configuration
# 
# This Terraform configuration deploys the complete infrastructure for the rescue prioritization system:
#
# Resources implemented:
# - DynamoDB table for storing prioritization records (dynamodb.tf)
# - Lambda functions for handling creation, updates, and AI-based prioritization (lambda.tf)
# - SQS queues and dead letter queue for processing decoupling (sqs.tf)
# - SNS topics for event notifications (sns.tf)
# - API Gateway endpoint for submitting synchronous requests (api_gateway.tf)
# - Step Functions state machine for orchestrating the prioritization workflow (step_functions.tf)
#
# Configuration:
# - provider.tf: AWS provider and default settings
# - variables.tf: All configurable variables
# - outputs.tf: Important resource identifiers for reference
