data "archive_file" "python_lambda_package" {
  type = "zip"
  source_file = "${path.module}/../src/lambda_function.py"
  output_path = "lambda_function.zip"
}

data "aws_iam_role" "lab_role" {
  name = "LabRole"
}