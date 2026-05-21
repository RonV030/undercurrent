"""Download Google Trends CSVs from S3 and load them into DuckDB as raw.google_trends."""

import io
import os

import duckdb
import pandas as pd

from ingestion.google_trends.upload import assume_ingestor_role

DEFAULT_BUCKET = "undercurrent-raw-data"
DEFAULT_PREFIX = "google_trends/"


def list_csvs(s3_client, bucket: str, prefix: str) -> list[str]:
    """Return all CSV object keys found under prefix in the bucket.

    Args:
        s3_client: Authenticated boto3 S3 client.
        bucket: S3 bucket name.
        prefix: Key prefix to filter on (e.g. 'google_trends/').

    Returns:
        List of full S3 object keys ending in .csv.
    """
    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [
        obj["Key"]
        for obj in response.get("Contents", [])
        if obj["Key"].endswith(".csv")
    ]


def download_csv(s3_client, bucket: str, key: str) -> pd.DataFrame:
    """Download a single CSV from S3 and return it as a DataFrame.

    Args:
        s3_client: Authenticated boto3 S3 client.
        bucket: S3 bucket name.
        key: Full S3 object key.

    Returns:
        DataFrame containing the CSV contents.
    """
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return pd.read_csv(io.BytesIO(response["Body"].read()))


def load_to_duckdb(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> None:
    """Write a DataFrame into DuckDB as raw.google_trends, replacing any existing data.

    Args:
        conn: Open DuckDB connection.
        df: Combined DataFrame of all Google Trends rows.
    """
    # Register the DataFrame so DuckDB can reference it by name in SQL.
    conn.register("google_trends_df", df)
    conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
    conn.execute(
        "CREATE OR REPLACE TABLE raw.google_trends AS SELECT * FROM google_trends_df"
    )
    conn.unregister("google_trends_df")


def main() -> None:
    """Download all Google Trends CSVs from S3 and load them into DuckDB.

    Environment variables:
        INGESTOR_ROLE_ARN (required): IAM role ARN to assume for S3 access.
        S3_BUCKET (optional): Source bucket. Defaults to undercurrent-raw-data.
        DUCKDB_PATH (optional): Path to the DuckDB file. Defaults to undercurrent.duckdb.
    """
    role_arn = os.environ["INGESTOR_ROLE_ARN"]
    bucket = os.environ.get("S3_BUCKET", DEFAULT_BUCKET)
    db_path = os.environ.get("DUCKDB_PATH", "undercurrent.duckdb")

    session = assume_ingestor_role(role_arn)
    s3 = session.client("s3")

    print(f"Listing CSVs in s3://{bucket}/{DEFAULT_PREFIX}...")
    keys = list_csvs(s3, bucket, DEFAULT_PREFIX)
    print(f"Found {len(keys)} file(s).")

    frames = [download_csv(s3, bucket, key) for key in keys]
    combined = pd.concat(frames, ignore_index=True)
    print(f"Combined {len(combined)} total rows.")

    print(f"Loading into raw.google_trends in {db_path}...")
    conn = duckdb.connect(db_path)
    load_to_duckdb(conn, combined)
    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()
