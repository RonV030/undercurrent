# Progress Log

---

## 16/05/2026

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

## 20/05/2026

### What I did
Second working session. Added the IAM ingestor role and built the full Google Trends ingestion pipeline.

**Terraform (`/infra`):**
* `iam.tf` — creates the `undercurrent-ingestor` IAM role with a trust policy allowing the Terraform user to assume it; creates a policy granting `s3:PutObject`, `s3:GetObject`, `s3:ListBucket` on `undercurrent-raw-data` only; attaches the policy to the role
* `outputs.tf` — added `ingestor_role_arn` output

**Google Trends ingestor (`/ingestion/google_trends`):**
* `fetch.py` — wraps pytrends to fetch weekly search interest for five German mental health keywords over the past 12 months; includes a custom browser User-Agent and retry/backoff logic to work around Google rate limiting
* `upload.py` — calls `sts:AssumeRole` to get temporary credentials scoped to the ingestor role, then uploads the CSV to S3
* `main.py` — orchestrator; reads `INGESTOR_ROLE_ARN` from environment, calls fetch then upload, writes to `google_trends/YYYY-MM-DD.csv` in the raw bucket
* `requirements.txt` — pins `urllib3<2.0` to resolve a pytrends incompatibility with urllib3 2.x

**Bugs hit and fixed:**
* `TypeError: Retry.__init__() got an unexpected keyword argument method_whitelist` — pytrends 4.9.x uses a urllib3 1.x API that was removed in urllib3 2.0; fixed by pinning `urllib3<2.0`
* `TooManyRequestsError (429)` — Google rate limits pytrends' default Python User-Agent on the first request; mitigated by passing a realistic Chrome User-Agent via `requests_args`

**Verified:**
* Script ran successfully and uploaded `google_trends/2026-05-20.csv` to S3
* 53 rows of weekly data, columns: `date, depression, angst, burnout, therapie, psychologe, isPartial`
* Values are relative search interest scaled 0 to 100, not absolute counts

### What is next (Phase 1 remaining)
* [x] Google Trends ingestion script (`/ingestion`)
* [ ] GitHub Actions workflow — runs the ingestor on push
* [ ] dbt model (`/dbt`) — transforms raw S3 data (staging to mart)
* [ ] Streamlit chart (`/app`) — reads from dbt output and displays a trend chart
