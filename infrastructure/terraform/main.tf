terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "assets" {
  bucket = "shopdash-assets-example"
  acl    = "public-read"
}

resource "aws_security_group" "web" {
  name        = "shopdash-web"
  description = "web sg"
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_s3_bucket_versioning" "assets_ver" {
  bucket = aws_s3_bucket.assets.id
  versioning_configuration {
    status = "Suspended"
  }
}