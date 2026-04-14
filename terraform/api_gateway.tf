resource "aws_api_gateway_rest_api" "prioritization_api" {
  name        = "rescue-prioritization-api"
  description = "API for submitting rescue prioritization requests"

  tags = {
    Name = "rescue-prioritization-api"
  }
}

resource "aws_api_gateway_resource" "requests" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  parent_id   = aws_api_gateway_rest_api.prioritization_api.root_resource_id
  path_part   = "requests"
}

resource "aws_api_gateway_method" "post_request" {
  rest_api_id      = aws_api_gateway_rest_api.prioritization_api.id
  resource_id      = aws_api_gateway_resource.requests.id
  http_method      = "POST"
  authorization    = "NONE"
  request_models = {
    "application/json" = aws_api_gateway_model.rescue_request.name
  }
}

resource "aws_api_gateway_model" "rescue_request" {
  rest_api_id  = aws_api_gateway_rest_api.prioritization_api.id
  name         = "RescueRequest"
  content_type = "application/json"

  schema = jsonencode({
    type = "object"
    properties = {
      requestId = {
        type = "string"
      }
      incidentId = {
        type = "string"
      }
      requestType = {
        type = "string"
        enum = ["RESCUE", "EVACUATION", "MEDICAL_AID"]
      }
      peopleCount = {
        type = "integer"
      }
      specialNeeds = {
        type  = "array"
        items = { type = "string" }
      }
      description = {
        type = "string"
      }
      location = {
        type = "object"
        properties = {
          latitude  = { type = "number" }
          longitude = { type = "number" }
          address   = { type = "string" }
        }
      }
    }
    required = ["requestId", "incidentId", "requestType", "peopleCount", "location"]
  })
}

resource "aws_api_gateway_integration" "post_request_integration" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  resource_id = aws_api_gateway_resource.requests.id
  http_method = aws_api_gateway_method.post_request.http_method
  type        = "AWS_PROXY"
  uri         = aws_lambda_function.create_event_handler.invoke_arn

  request_templates = {
    "application/json" = jsonencode({
      header = {
        messageId      = "$context.requestId"
        correlationId  = "$context.requestId"
        eventType      = "rescue-request.created"
        timestamp      = "$context.requestTime"
        traceId        = "$context.requestId"
      }
      body = "$input.json('$')"
    })
  }
}

resource "aws_api_gateway_integration_response" "post_request_response" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  resource_id = aws_api_gateway_resource.requests.id
  http_method = aws_api_gateway_method.post_request.http_method
  status_code = "200"

  depends_on = [aws_api_gateway_integration.post_request_integration]
}

resource "aws_api_gateway_method_response" "post_request_200" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
  resource_id = aws_api_gateway_resource.requests.id
  http_method = aws_api_gateway_method.post_request.http_method
  status_code = "200"
}

resource "aws_api_gateway_deployment" "prioritization_api" {
  rest_api_id = aws_api_gateway_rest_api.prioritization_api.id
#   stage_name  = var.environment

  depends_on = [
    aws_api_gateway_integration.post_request_integration,
    aws_api_gateway_integration_response.post_request_response
  ]
}

resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.create_event_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.prioritization_api.execution_arn}/*/*"
}
