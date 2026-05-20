"""Orchestrate fetching Google Trends data and uploading it to S3."""

import datetime
import os

from ingestion.google_trends.fetch import fetch_trends
from ingestion.google_trends.upload import assume_ingestor_role, upload_csv


DEFAULT_KEYWORDS = ["depression", "angst", "burnout", "therapie", "psychologe"]
DEFAULT_BUCKET = "undercurrent-raw-data"


def main() -> None:
    """Fetch today's Google Trends data for German mental health keywords and upload to S3.

    Environment variables:
        INGESTOR_ROLE_ARN (required): IAM role ARN the script will assume.
        S3_BUCKET (optional): Destination bucket. Defaults to undercurrent-raw-data.
        KEYWORDS (optional): Comma separated keyword list. Defaults to the built in set.
    """
    role_arn = os.environ["INGESTOR_ROLE_ARN"]
    bucket = os.environ.get("S3_BUCKET", DEFAULT_BUCKET)
    keywords_env = os.environ.get("KEYWORDS")
    keywords = keywords_env.split(",") if keywords_env else DEFAULT_KEYWORDS

    print(f"Fetching Google Trends data for {keywords} (geo=DE, past 12 months)...")
    df = fetch_trends(keywords)
    print(f"Fetched {len(df)} rows.")

    today = datetime.date.today().isoformat()
    key = f"google_trends/{today}.csv"

    print(f"Assuming role and uploading to s3://{bucket}/{key}...")
    session = assume_ingestor_role(role_arn)
    upload_csv(session, bucket, key, df.to_csv())

    print("Done.")


if __name__ == "__main__":
    main()
