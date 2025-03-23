resource "aws_lambda_function" "mazyfood_auth_lambda" {
  function_name = "mazyfood_auth_lambda_function"
  description   = "MazyFood Auth Lambda Function"
  architectures = ["x86_64"]
  filename = "lambda_function.zip"
  source_code_hash = data.archive_file.python_lambda_package.output_base64sha256
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  role          = data.aws_iam_role.lab_role.arn
  layers = [aws_lambda_layer_version.boto3_layer.arn, aws_lambda_layer_version.psycopg2_layer.arn]

  environment {
    variables = {
      RDS_HOST              = "your_rds_host"
      RDS_USER              = "your_rds_user"
      RDS_PASSWORD          = "your_rds_password"
      RDS_DATABASE          = "your_rds_database"
      COGNITO_USER_POOL_ID  = "your_cognito_user_pool_id"
    }
  }
}