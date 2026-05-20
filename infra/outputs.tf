output "bucket_name" {
  description = "The name of the S3 bucket as it was created."
  value       = aws_s3_bucket.raw_data.id
}

output "bucket_arn" {
  description = "The ARN (Amazon Resource Name) of the bucket. You will paste this into IAM policies to grant specific roles access to exactly this bucket."
  value       = aws_s3_bucket.raw_data.arn
}

output "ingestor_role_arn" {
  description = "ARN of the ingestor IAM role. The Python ingestor passes this to sts:AssumeRole to get temporary S3 credentials."
  value       = aws_iam_role.ingestor.arn
}
