variable "aws_region" {
  description = "AWS region to deploy into. eu-central-1 is Frankfurt — closest to Germany and the project's target audience."
  type        = string
  default     = "eu-central-1"
}

variable "bucket_name" {
  description = "Name of the S3 bucket for raw ingestion data. S3 bucket names are globally unique across ALL AWS accounts — if this name is taken, add a short suffix like '-dev-yourname'."
  type        = string
  default     = "undercurrent-raw-data"
}
