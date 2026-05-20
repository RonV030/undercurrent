"""Upload data to S3 using temporary credentials from STS AssumeRole."""

import boto3


def assume_ingestor_role(
    role_arn: str,
    session_name: str = "google-trends-ingestor",
) -> boto3.Session:
    """Assume the ingestor IAM role and return a boto3 Session with temporary credentials.

    Uses the caller's default AWS credentials (read by boto3 from ~/.aws/credentials)
    to call sts:AssumeRole. The returned session is authorised only by the role's
    attached policies and the credentials expire automatically after one hour.

    Args:
        role_arn: ARN of the IAM role to assume.
        session_name: Label shown in CloudTrail logs for this session.

    Returns:
        A boto3 Session pre-configured with the temporary credentials.
    """
    sts = boto3.client("sts")
    response = sts.assume_role(RoleArn=role_arn, RoleSessionName=session_name)
    credentials = response["Credentials"]

    return boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )


def upload_csv(
    session: boto3.Session,
    bucket: str,
    key: str,
    csv_data: str,
) -> None:
    """Upload a CSV string to S3 at the given bucket and key.

    Args:
        session: boto3 Session whose credentials can write to the bucket.
        bucket: Destination S3 bucket name.
        key: Object key (path inside the bucket).
        csv_data: CSV content as a string; encoded as UTF-8 before upload.
    """
    s3 = session.client("s3")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=csv_data.encode("utf-8"),
        ContentType="text/csv",
    )
