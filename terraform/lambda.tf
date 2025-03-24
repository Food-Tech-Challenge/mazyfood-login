resource "aws_lambda_function" "auth_lambda" {
  function_name    = "${var.project}_auth"
  description      = "MAZYFood Auth Lambda Function"
  architectures    = ["x86_64"]
  filename         = "lambda_function.zip"
  source_code_hash = data.archive_file.python_lambda_package.output_base64sha256
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  role             = data.aws_iam_role.lab_role.arn
  layers           = [aws_lambda_layer_version.boto3.arn, aws_lambda_layer_version.psycopg2_binary.arn]

  vpc_config {
    subnet_ids         = toset(data.aws_subnets.private.ids)
    security_group_ids = [data.aws_security_group.selected_security_group.id]
  }
}