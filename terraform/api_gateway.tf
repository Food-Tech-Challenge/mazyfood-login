resource "aws_apigatewayv2_api" "auth_api" {
  name          = "${var.project}_auth_api"
  protocol_type = "HTTP"
  description   = "API Gateway HTTP para autenticação"
}

resource "aws_apigatewayv2_route" "auth_post" {
  api_id    = aws_apigatewayv2_api.auth_api.id
  route_key = "GET /auth"
  target    = "integrations/${aws_apigatewayv2_integration.auth_lambda.id}"
}

resource "aws_apigatewayv2_integration" "auth_lambda" {
  api_id                 = aws_apigatewayv2_api.auth_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.auth_lambda.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_lambda_permission" "auth_api_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auth_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.auth_api.execution_arn}/*"
}

resource "aws_apigatewayv2_stage" "auth_v1" {
  api_id      = aws_apigatewayv2_api.auth_api.id
  name        = "v1"
  auto_deploy = true
}

output "auth_api_invoke_url" {
  value = aws_apigatewayv2_api.auth_api.api_endpoint
}
