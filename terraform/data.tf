data "archive_file" "python_lambda_package" {
  type        = "zip"
  source_file = "${path.module}/../src/lambda_function.py"
  output_path = "lambda_function.zip"
}

data "aws_iam_role" "lab_role" {
  name = "LabRole"
}

data "aws_vpc" "selected_vpc" {
  filter {
    name   = "tag:Name"
    values = ["mazyfood-vpc"]
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected_vpc.id]
  }

  filter {
    name   = "map-public-ip-on-launch"
    values = ["false"]
  }
}

data "aws_security_group" "selected_security_group" {
  filter {
    name   = "tag:Name"
    values = ["mazyfood-security-group-db"]
  }
}