resource "aws_lambda_layer_version" "boto3_layer" {
  layer_name = "boto3"
  filename = "../src/layers/boto3.zip"
  compatible_runtimes = ["python3.12"]
  compatible_architectures = ["x86_64"]
}

resource "aws_lambda_layer_version" "psycopg2_layer" {
  layer_name = "psycopg2"
  filename = "../src/layers/psycopg2-binary.zip"
  compatible_runtimes = ["python3.12"]
  compatible_architectures = ["x86_64"]
}