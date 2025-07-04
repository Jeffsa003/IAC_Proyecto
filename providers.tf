terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  /*
  backend "s3" {
    bucket         = "elearningproject-terraform-state-471112539322" # Reemplazar con el nombre del bucket creado
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "elearningproject-terraform-locks"
    encrypt        = true
  }
*/
}

provider "aws" {
  region  = var.aws_region
}
