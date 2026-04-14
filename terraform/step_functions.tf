# Reference existing LabRole from AWS Learner Lab
data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

# IAM Policy for Step Functions to invoke Lambda
resource "aws_iam_role_policy" "step_functions_lambda_policy" {
  name = "step-functions-lambda-policy"
  role = data.aws_iam_role.lab_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          "${aws_lambda_function.create_event_handler.arn}:*",
          "${aws_lambda_function.update_event_handler.arn}:*",
          "${aws_lambda_function.evaluate_worker.arn}:*",
          aws_lambda_function.create_event_handler.arn,
          aws_lambda_function.update_event_handler.arn,
          aws_lambda_function.evaluate_worker.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [
          aws_sns_topic.rescue_prioritization_events.arn,
          aws_sns_topic.rescue_request_updated.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.rescue_request_dlq.arn
      }
    ]
  })
}

# Read the state definition from file
locals {
  state_machine_definition = file("${path.module}/stateDef.json")
}

resource "aws_sfn_state_machine" "prioritization_pipeline" {
  name       = "rescue-prioritization-pipeline"
  role_arn   = data.aws_iam_role.lab_role.arn
  definition = local.state_machine_definition

  tags = {
    Name = "prioritization-pipeline"
  }

  depends_on = [
    aws_iam_role_policy.step_functions_lambda_policy,
    aws_lambda_function.create_event_handler,
    aws_lambda_function.update_event_handler,
    aws_lambda_function.evaluate_worker,
    aws_sns_topic.rescue_prioritization_events,
    aws_sns_topic.rescue_request_updated,
    aws_sqs_queue.rescue_request_dlq
  ]
}
