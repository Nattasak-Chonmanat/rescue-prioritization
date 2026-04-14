# Reference existing LabRole from AWS Learner Lab
data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

# IAM Policy for DynamoDB access
resource "aws_iam_role_policy" "lambda_dynamodb_policy" {
  name = "rescue-prioritization-dynamodb-policy"
  role = data.aws_iam_role.lab_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.prioritization_records.arn
      }
    ]
  })
}

# IAM Policy for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = data.aws_iam_role.lab_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda function for creating rescue requests
resource "aws_lambda_function" "create_event_handler" {
  filename      = "createEventHandler.zip"
  function_name = "createEventHandler"
  role          = data.aws_iam_role.lab_role.arn
  handler       = "createEventHandler.lambda_handler"
  runtime       = "python3.11"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  source_code_hash = filebase64sha256("createEventHandler.zip")

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
    }
  }

  depends_on = [aws_iam_role_policy.lambda_dynamodb_policy]

  tags = {
    Name = "create-event-handler"
  }
}

# Lambda function for updating rescue requests
resource "aws_lambda_function" "update_event_handler" {
  filename      = "updateEventHandler.zip"
  function_name = "updateEventHandler"
  role          = data.aws_iam_role.lab_role.arn
  handler       = "updateEventHandler.lambda_handler"
  runtime       = "python3.11"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  source_code_hash = filebase64sha256("updateEventHandler.zip")

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
    }
  }

  depends_on = [aws_iam_role_policy.lambda_dynamodb_policy]

  tags = {
    Name = "update-event-handler"
  }
}

# Lambda function for evaluating priority using AI
resource "aws_lambda_function" "evaluate_worker" {
  filename      = "evaluateWorker.zip"
  function_name = "evaluateWorker"
  role          = data.aws_iam_role.lab_role.arn
  handler       = "evaluateWorker.lambda_handler"
  runtime       = "python3.11"
  timeout       = 120
  memory_size   = 512

  source_code_hash = filebase64sha256("evaluateWorker.zip")

  environment {
    variables = {
      DYNAMODB_TABLE = var.dynamodb_table_name
      GEMINI_API_KEY = var.gemini_api_key
    }
  }

  depends_on = [aws_iam_role_policy.lambda_dynamodb_policy]

  tags = {
    Name = "evaluate-worker"
  }
}
