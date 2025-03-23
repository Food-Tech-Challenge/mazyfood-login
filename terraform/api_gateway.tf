resource "aws_api_gateway_rest_api" "mazy_food_api_gtw" {
  name        = "mazy_food_api_gtw"
  description = "API Gateway to authenticate"
}

resource "aws_api_gateway_resource" "my_resource" {
  rest_api_id = aws_api_gateway_rest_api.mazy_food_api_gtw.id
  parent_id   = aws_api_gateway_rest_api.mazy_food_api_gtw.root_resource_id
  path_part   = "auth"
}

resource "aws_api_gateway_method" "my_method" {
  rest_api_id   = aws_api_gateway_rest_api.mazy_food_api_gtw.id
  resource_id   = aws_api_gateway_resource.my_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.mazy_food_api_gtw.id
  resource_id = aws_api_gateway_resource.my_resource.id
  http_method = aws_api_gateway_method.my_method.http_method
  type        = "AWS_PROXY"
  integration_http_method = "POST"
  uri         = aws_lambda_function.mazyfood_auth_lambda.invoke_arn
}

resource "aws_lambda_permission" "api_gateway_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.mazyfood_auth_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.mazy_food_api_gtw.execution_arn}/*/*"
}

resource "aws_api_gateway_deployment" "my_deployment" {
  depends_on = [aws_api_gateway_integration.lambda_integration]
  rest_api_id = aws_api_gateway_rest_api.mazy_food_api_gtw.id
}

resource "aws_api_gateway_stage" "my_stage" {
  deployment_id = aws_api_gateway_deployment.my_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.mazy_food_api_gtw.id
  stage_name    = "v1"
}

output "api_gateway_invoke_url" {
  value = aws_api_gateway_deployment.my_deployment.invoke_url
}