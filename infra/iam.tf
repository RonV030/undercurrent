
# Looks up the AWS account ID of whoever is running Terraform.
# Used in the trust policy below so we don't hardcode a 12-digit account number.
data "aws_caller_identity" "current" {}

# The role the Python ingestor will assume at runtime.
# It has no permanent credentials — it issues short-lived tokens via STS.
resource "aws_iam_role" "ingestor" {
  name = "undercurrent-ingestor"

  # Trust policy: who is allowed to call sts:AssumeRole on this role.
  # Only the undercurrent-terraform IAM user can assume it.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/undercurrent-terraform"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Permissions the ingestor role gets when assumed.
# Scoped to this one bucket only — not account-wide S3 access.
resource "aws_iam_policy" "ingestor_s3" {
  name        = "undercurrent-ingestor-s3"
  description = "Allows the ingestor role to read and write objects in the raw data bucket."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",   # upload files
          "s3:GetObject",   # download files (needed for idempotency checks)
          "s3:ListBucket"   # list contents — required to check if a file already exists
        ]
        Resource = [
          aws_s3_bucket.raw_data.arn,         # the bucket itself (for ListBucket)
          "${aws_s3_bucket.raw_data.arn}/*"   # objects inside the bucket (for Put/Get)
        ]
      }
    ]
  })
}

# Attaches the policy to the role.
# Kept separate so the same policy could be attached to multiple roles if needed.
resource "aws_iam_role_policy_attachment" "ingestor_s3" {
  role       = aws_iam_role.ingestor.name
  policy_arn = aws_iam_policy.ingestor_s3.arn
}
