resource "aws_api_gateway_rest_api" "auth_api" {
  name        = "${var.project}_auth_api"
  description = "API Gateway to authenticate"
}

resource "aws_api_gateway_resource" "auth_resource" {
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
  parent_id   = aws_api_gateway_rest_api.auth_api.root_resource_id
  path_part   = "auth"
}

resource "aws_api_gateway_method" "auth_post" {
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  resource_id   = aws_api_gateway_resource.auth_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "auth_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.auth_api.id
  resource_id             = aws_api_gateway_resource.auth_resource.id
  http_method             = aws_api_gateway_method.auth_post.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.auth_lambda.invoke_arn
}

resource "aws_lambda_permission" "auth_api_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auth_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.auth_api.execution_arn}/*/*"
}

resource "aws_api_gateway_deployment" "auth_deployment" {
  depends_on  = [aws_api_gateway_integration.auth_lambda]
  rest_api_id = aws_api_gateway_rest_api.auth_api.id
}

resource "aws_api_gateway_stage" "auth_v1" {
  deployment_id = aws_api_gateway_deployment.auth_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.auth_api.id
  stage_name    = "v1"

  depends_on = [
    aws_api_gateway_integration.auth_lambda,
    aws_api_gateway_method.auth_post
  ]
}

output "auth_api_invoke_url" {
  value = aws_api_gateway_deployment.auth_deployment.invoke_url
}