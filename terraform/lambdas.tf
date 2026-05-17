locals {
  lambda_role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/LabRole"
}

# ---------------------------------------------------------------------------
# createEventHandler
# ---------------------------------------------------------------------------
data "archive_file" "create_event_handler" {
  type        = "zip"
  source_file = "${path.module}/../lambda/createEventHandler.py"
  output_path = "${path.module}/../lambda/zip/createEventHandler.zip"
}

resource "aws_lambda_function" "create_event_handler" {
  function_name    = "createEventHandler"
  role             = local.lambda_role_arn
  runtime          = "python3.12"
  handler          = "createEventHandler.lambda_handler"
  filename         = data.archive_file.create_event_handler.output_path
  source_code_hash = data.archive_file.create_event_handler.output_base64sha256

  tags = {
    Name = "createEventHandler"
  }
}

# ---------------------------------------------------------------------------
# evaluateWorker
# ---------------------------------------------------------------------------
data "archive_file" "evaluate_worker" {
  type        = "zip"
  source_file = "${path.module}/../lambda/evaluateWorker.py"
  output_path = "${path.module}/../lambda/zip/evaluateWorker.zip"
}

resource "aws_lambda_layer_version" "evaluate_worker_layer" {
  layer_name          = "evaluateWorkerLayer"
  filename            = "${path.module}/../lambda/lambda-layer/python.zip"
  source_code_hash    = filebase64sha256("${path.module}/../lambda/lambda-layer/python.zip")
  compatible_runtimes = ["python3.12"]
}

resource "aws_lambda_function" "evaluate_worker" {
  function_name    = "evaluateWorker"
  role             = local.lambda_role_arn
  runtime          = "python3.12"
  handler          = "evaluateWorker.lambda_handler"
  filename         = data.archive_file.evaluate_worker.output_path
  source_code_hash = data.archive_file.evaluate_worker.output_base64sha256

  layers = [aws_lambda_layer_version.evaluate_worker_layer.arn]

  environment {
    variables = {
      GEMINI_API_KEY = "<API_KEY>"
    }
  }

  tags = {
    Name = "evaluateWorker"
  }
}

# ---------------------------------------------------------------------------
# getPriorByIncidentId
# ---------------------------------------------------------------------------
data "archive_file" "get_prior_by_incident_id" {
  type        = "zip"
  source_file = "${path.module}/../lambda/getPriorByIncidentId.py"
  output_path = "${path.module}/../lambda/zip/getPriorByIncidentId.zip"
}

resource "aws_lambda_function" "get_prior_by_incident_id" {
  function_name    = "getPriorByIncidentId"
  role             = local.lambda_role_arn
  runtime          = "python3.12"
  handler          = "getPriorByIncidentId.lambda_handler"
  filename         = data.archive_file.get_prior_by_incident_id.output_path
  source_code_hash = data.archive_file.get_prior_by_incident_id.output_base64sha256

  tags = {
    Name = "getPriorByIncidentId"
  }
}

# ---------------------------------------------------------------------------
# getPriorByRequestId
# ---------------------------------------------------------------------------
data "archive_file" "get_prior_by_request_id" {
  type        = "zip"
  source_file = "${path.module}/../lambda/getPriorByRequestId.py"
  output_path = "${path.module}/../lambda/zip/getPriorByRequestId.zip"
}

resource "aws_lambda_function" "get_prior_by_request_id" {
  function_name    = "getPriorByRequestId"
  role             = local.lambda_role_arn
  runtime          = "python3.12"
  handler          = "getPriorByRequestId.lambda_handler"
  filename         = data.archive_file.get_prior_by_request_id.output_path
  source_code_hash = data.archive_file.get_prior_by_request_id.output_base64sha256

  tags = {
    Name = "getPriorByRequestId"
  }
}

# ---------------------------------------------------------------------------
# updateEventHandler
# ---------------------------------------------------------------------------
data "archive_file" "update_event_handler" {
  type        = "zip"
  source_file = "${path.module}/../lambda/updateEventHandler.py"
  output_path = "${path.module}/../lambda/zip/updateEventHandler.zip"
}

resource "aws_lambda_function" "update_event_handler" {
  function_name    = "updateEventHandler"
  role             = local.lambda_role_arn
  runtime          = "python3.12"
  handler          = "updateEventHandler.lambda_handler"
  filename         = data.archive_file.update_event_handler.output_path
  source_code_hash = data.archive_file.update_event_handler.output_base64sha256

  tags = {
    Name = "updateEventHandler"
  }
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "createEventHandler" {
  value = aws_lambda_function.create_event_handler.arn
}

output "evaluateWorker" {
  value = aws_lambda_function.evaluate_worker.arn
}

output "getPriorByIncidentId" {
  value = aws_lambda_function.get_prior_by_incident_id.arn
}

output "getPriorByRequestId" {
  value = aws_lambda_function.get_prior_by_request_id.arn
}

output "updateEventHandler" {
  value = aws_lambda_function.update_event_handler.arn
}
