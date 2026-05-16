output "bucket_name" {
  description = "The name of the S3 bucket as it was created."
  value       = aws_s3_bucket.raw_data.id
}

output "bucket_arn" {
  description = "The ARN (Amazon Resource Name) of the bucket. You will paste this into IAM policies to grant specific roles access to exactly this bucket."
  value       = aws_s3_bucket.raw_data.arn
}
