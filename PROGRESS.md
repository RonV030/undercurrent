# Progress Log

---

## 2026-05-16

### What I did
First working session. Created the project skeleton and provisioned the S3 bucket with Terraform.

**Project structure:**
* Created folder skeleton: `/ingestion`, `/dbt`, `/ai`, `/app`, `/infra`, `/monitoring`
* Added `.gitignore` covering `.env`, Terraform state files, Python cache, and virtual environments

**AWS setup (manual, in the Console):**
* Created AWS account and enabled MFA on the root account
* Created a dedicated Terraform IAM user with S3 and IAM permissions
* Generated access keys and configured them locally with `aws configure`
* Set up a zero spend billing alert

**Terraform (`/infra`):**
* `main.tf` — provisions S3 bucket `undercurrent-raw-data` in `eu-central-1` with versioning, AES-256 encryption, and all public access blocked
* `variables.tf` — declares `aws_region` and `bucket_name` as inputs with defaults
* `outputs.tf` — prints bucket name and bucket ARN after apply
* `.terraform.lock.hcl` — locks the AWS provider at v5.100.0

**State after `terraform apply`:**
* S3 bucket `undercurrent-raw-data` is live in `eu-central-1`, empty

---

## 2026-05-20

### What I did
Second working session. Added the IAM role the Python ingestor will use to authenticate to S3.

**Terraform (`/infra`):**
* `iam.tf` — creates the `undercurrent-ingestor` IAM role with a trust policy allowing the Terraform user to assume it; creates a policy granting `s3:PutObject`, `s3:GetObject`, `s3:ListBucket` on `undercurrent-raw-data` only; attaches the policy to the role
* `outputs.tf` — added `ingestor_role_arn` output

**State after `terraform apply`:**
* IAM role `undercurrent-ingestor` is live with permissions scoped to the raw data bucket
* Run `terraform output ingestor_role_arn` in `/infra` to retrieve the role ARN

### What is next (Phase 1 remaining)
* [ ] Google Trends ingestion script (`/ingestion`) — fetches data and uploads to S3
* [ ] GitHub Actions workflow — runs the ingestor on push
* [ ] dbt model (`/dbt`) — transforms raw S3 data (staging to mart)
* [ ] Streamlit chart (`/app`) — reads from dbt output and displays a trend chart
