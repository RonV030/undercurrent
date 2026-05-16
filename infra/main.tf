terraform {
  # Minimum Terraform version — 1.5+ is stable and widely supported
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # ~> means "5.x but not 6.x" — allows patch updates, blocks breaking changes
    }
  }
}

provider "aws" {
  region = var.aws_region
  # No credentials here — Terraform reads them from ~/.aws/credentials or the environment.
  # Never hardcode AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY in .tf files.
}

# Free tier: 5 GB storage, 20,000 GET requests, 2,000 PUT/COPY/POST/LIST requests per month.
# Free tier applies for 12 months from AWS account creation date.
resource "aws_s3_bucket" "raw_data" {
  bucket = var.bucket_name

  tags = {
    Project     = "undercurrent"
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

# Versioning keeps the previous version of a file when it is overwritten.
# Useful when an ingestor re-uploads the same date's data with corrections —
# you can always roll back to what was there before.
resource "aws_s3_bucket_versioning" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encrypt all stored objects with AES-256 (server-side encryption).
# This is free and has no effect on how you read or write files —
# AWS handles encryption/decryption transparently.
resource "aws_s3_bucket_server_side_encryption_configuration" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block all four paths that could make bucket contents public.
# Raw ingestion data must never be publicly accessible.
resource "aws_s3_bucket_public_access_block" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id

  block_public_acls       = true  # reject requests that include a public ACL
  block_public_policy     = true  # reject bucket policies that grant public access
  ignore_public_acls      = true  # ignore any public ACLs already on the bucket
  restrict_public_buckets = true  # restrict access to AWS services and authorized users only
}
