# Technical Decisions

Every significant technical choice made during the build, with the reasoning behind it.

---

## Infrastructure as Code: Terraform over manual AWS Console setup

**What I chose:** Define all AWS infrastructure in Terraform files and apply it via the CLI.

**Alternative:** Create resources by clicking through the AWS Console.

**Why:** Manual Console setup cannot be reproduced reliably. If a resource gets deleted or a new environment is needed, there is no record of every setting that was configured. With Terraform, running `terraform apply` recreates everything exactly as declared. The infrastructure is also version controlled, so every change is traceable and reversible. Starting with Terraform now also avoids a painful migration later when the project grows to include databases, compute, and networking.

---

## AWS Region: eu-central-1 (Frankfurt)

**What I chose:** Deploy all AWS resources to `eu-central-1`.

**Alternative:** `us-east-1` (Virginia, the AWS default) or `eu-west-1` (Ireland).

**Why:** This project tracks German mental health signals. Storing data in Frankfurt satisfies GDPR data residency expectations and minimises latency for any future users of the API or frontend. Frankfurt is the closest AWS region to Germany, which makes it the natural choice for a Germany-focused project.

---

## Folder structure: one folder per layer of the stack

**What I chose:** Organise the repository into `/ingestion`, `/dbt`, `/ai`, `/app`, `/infra`, and `/monitoring`, where each folder owns one concern.

**Alternative:** A flat structure with all scripts at the root, or grouping files by data source rather than by layer.

**Why:** Each folder corresponds to a distinct stage of the pipeline. Someone working on the dbt models does not need to look at the ingestion scripts, and vice versa. The structure also maps directly to how data engineering teams typically organise repositories, which means it is immediately readable to anyone familiar with the domain.

---

## S3 versioning: enabled

**What I chose:** Enable versioning on the raw data bucket.

**Alternative:** Leave versioning off, which is the default.

**Why:** The raw data bucket is the source of truth for the entire pipeline. Without versioning, uploading a corrected file silently overwrites the original and the previous version is gone permanently. With versioning enabled, both copies are retained and the previous state can always be recovered. At the data volumes this project handles, the storage cost is negligible.

---

## S3 encryption: AES-256 at rest

**What I chose:** Require AES-256 encryption for all objects stored in the bucket, declared explicitly in Terraform.

**Alternative:** Rely on AWS account-level default encryption, which was enabled globally by AWS in 2023.

**Why:** Mental health signals data is sensitive even in aggregated form. Declaring encryption explicitly in Terraform makes it a documented and enforced requirement rather than an implicit platform behaviour that could be overlooked during a security review. There is no cost and no performance impact.

---

## S3 public access: all four block settings enabled

**What I chose:** Enable all four public access block settings on the bucket.

**Alternative:** Leave the defaults, which keep the bucket private initially but do not prevent a future policy change from making it public.

**Why:** Raw ingestion data must never be publicly accessible. The four settings together make it structurally impossible to accidentally expose the bucket, not just unlikely. This is a hard guardrail enforced at the infrastructure level, independent of whatever policies are attached later.

---

## IAM: dedicated ingestor role rather than reusing the Terraform operator user

**What I chose:** Create a dedicated `undercurrent-ingestor` IAM role with permissions scoped to one bucket, used only by the Python ingestor at runtime.

**Alternative:** Use the Terraform operator user's access keys directly in the ingestor script.

**Why:** The Terraform user holds broad permissions necessary for managing infrastructure. Passing those credentials to application code violates the principle of least privilege. The ingestor role grants only `s3:PutObject`, `s3:GetObject`, and `s3:ListBucket` on `undercurrent-raw-data`. If those credentials were ever exposed in a log or error message, the impact is limited to that one bucket.

Roles also issue temporary credentials that expire automatically after one hour. The Terraform user's access keys are permanent until manually rotated. Temporary credentials are safer by design and require no rotation policy.

---

## IAM credential delivery: STS AssumeRole rather than a second IAM user

**What I chose:** The ingestor calls `sts:AssumeRole` at runtime to receive temporary credentials scoped to the ingestor role.

**Alternative:** Create a second IAM user for the ingestor with its own permanent access key stored in a `.env` file.

**Why:** Permanent keys stored in `.env` files have a well-documented failure mode: they get committed to version control, copied into CI/CD configuration, and forgotten. Temporary credentials from `AssumeRole` expire after one hour and are never written to disk. This pattern also transfers directly to GitHub Actions and EC2 without modification, because those environments receive credentials automatically from the AWS platform rather than from a file.

---

## Terraform AWS provider version constraint: `~> 5.0`

**What I chose:** Pin the AWS provider to any 5.x release using the `~> 5.0` constraint.

**Alternative:** No version pin, which always uses the latest available version, or an exact pin like `= 5.100.0`.

**Why:** No pin means a future `terraform init` could silently pull a 6.x provider with breaking changes. An exact pin requires a manual update for every patch release, which creates maintenance overhead with no benefit. The `~> 5.0` constraint permits automatic patch updates while blocking major version jumps. It is the standard Terraform recommendation for provider version management.
