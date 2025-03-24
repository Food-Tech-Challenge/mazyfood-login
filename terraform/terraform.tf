terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.92.0"
    }
  }

  required_version = ">= 1.11"

  backend "s3" {
    key = "mazyfood-login/terraform.tfstate"
  }
}