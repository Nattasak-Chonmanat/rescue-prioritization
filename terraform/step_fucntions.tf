# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------
resource "aws_api_gateway_rest_api" "prioritization_api" {
  name = "prioritization-api"

  tags = {
    Name = "prioritization-api"
  }
}

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

# /prioritizations
resource "aws_api_gateway_resource" "prioritizations" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  parent_id   = aws_api_gateway_rest_api.prioritization_api.root_resource_id
  path_part   = "prioritizations"
}

# /v1/prioritizations/incident
resource "aws_api_gateway_resource" "incident" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  parent_id   = aws_api_gateway_resource.prioritizations.id
  path_part   = "incident"
}

# /v1/prioritizations/incident/{incident_id}
resource "aws_api_gateway_resource" "incident_id" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  parent_id   = aws_api_gateway_resource.incident.id
  path_part   = "{incident_id}"
}

# /v1/prioritizations/request
resource "aws_api_gateway_resource" "request" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  parent_id   = aws_api_gateway_resource.prioritizations.id
  path_part   = "request"
}

# /v1/prioritizations/request/{request_id}
resource "aws_api_gateway_resource" "request_id" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  parent_id   = aws_api_gateway_resource.request.id
  path_part   = "{request_id}"
}

# ---------------------------------------------------------------------------
# GET /v1/prioritizations/incident/{incident_id}
# ---------------------------------------------------------------------------
resource "aws_api_gateway_method" "get_by_incident_id" {
  rest_api_id   = aws_api_gateway_rest_api.prioritization_api.id
  resource_id   = aws_api_gateway_resource.incident_id.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_by_incident_id" {
  rest_api_id             = aws_api_gateway_rest_api.prioritization_api.id
  resource_id             = aws_api_gateway_resource.incident_id.id
  http_method             = aws_api_gateway_method.get_by_incident_id.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_prior_by_incident_id.invoke_arn
}

resource "aws_lambda_permission" "apigw_get_by_incident_id" {
  statement_id  = "AllowAPIGatewayInvokeGetByIncidentId"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_prior_by_incident_id.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.prioritization_api.execution_arn}/*/*"
}

# CORS — OPTIONS /v1/prioritizations/incident/{incident_id}
resource "aws_api_gateway_method" "options_incident_id" {
  rest_api_id   = aws_api_gateway_rest_api.prioritization_api.id
  resource_id   = aws_api_gateway_resource.incident_id.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_incident_id" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  resource_id = aws_api_gateway_resource.incident_id.id
  http_method = aws_api_gateway_method.options_incident_id.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_incident_id_200" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  resource_id = aws_api_gateway_resource.incident_id.id
  http_method = aws_api_gateway_method.options_incident_id.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "options_incident_id" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  resource_id = aws_api_gateway_resource.incident_id.id
  http_method = aws_api_gateway_method.options_incident_id.http_method
  status_code = "200"

  depends_on = [aws_api_gateway_method_response.options_incident_id_200]

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# ---------------------------------------------------------------------------
# GET /v1/prioritizations/request/{request_id}
# ---------------------------------------------------------------------------
resource "aws_api_gateway_method" "get_by_request_id" {
  rest_api_id   = aws_api_gateway_rest_api.prioritization_api.id
  resource_id   = aws_api_gateway_resource.request_id.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_by_request_id" {
  rest_api_id             = aws_api_gateway_rest_api.prioritization_api.id
  resource_id             = aws_api_gateway_resource.request_id.id
  http_method             = aws_api_gateway_method.get_by_request_id.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_prior_by_request_id.invoke_arn
}

resource "aws_lambda_permission" "apigw_get_by_request_id" {
  statement_id  = "AllowAPIGatewayInvokeGetByRequestId"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_prior_by_request_id.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.prioritization_api.execution_arn}/*/*"
}

# CORS — OPTIONS /v1/prioritizations/request/{request_id}
resource "aws_api_gateway_method" "options_request_id" {
  rest_api_id   = aws_api_gateway_rest_api.prioritization_api.id
  resource_id   = aws_api_gateway_resource.request_id.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_request_id" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  resource_id = aws_api_gateway_resource.request_id.id
  http_method = aws_api_gateway_method.options_request_id.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_request_id_200" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  resource_id = aws_api_gateway_resource.request_id.id
  http_method = aws_api_gateway_method.options_request_id.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "options_request_id" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  resource_id = aws_api_gateway_resource.request_id.id
  http_method = aws_api_gateway_method.options_request_id.http_method
  status_code = "200"

  depends_on = [aws_api_gateway_method_response.options_request_id_200]

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# ---------------------------------------------------------------------------
# Deployment & Stage
# ---------------------------------------------------------------------------
resource "aws_api_gateway_deployment" "prioritization_api" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id

  depends_on = [
    aws_api_gateway_integration.get_by_incident_id,
    aws_api_gateway_integration.get_by_request_id,
    aws_api_gateway_integration.options_incident_id,
    aws_api_gateway_integration.options_request_id,
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "v1" {
  rest_api_id   = aws_api_gateway_rest_api.prioritization_api.id
  deployment_id = aws_api_gateway_deployment.prioritization_api.id
  stage_name    = "v1"

  tags = {
    Name = "prioritization-api-v1"
  }
}

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
output "api_gateway_base_url" {
  value = "https://${aws_api_gateway_rest_api.prioritization_api.id}.execute-api.${data.aws_caller_identity.current.account_id}.amazonaws.com/${aws_api_gateway_stage.v1.stage_name}"
}
