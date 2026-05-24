#!/usr/bin/env python3
"""Extract PostgreSQL tables and load partitioned Parquet files into MinIO."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import boto3
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import minio_bucket, minio_settings, pg_url

TABLES = [
    "wells",
    "production",
    "telemetry",
    "well_targets",
    "pump_sensors",
    "pump_failures",
    "deliveries",
]


def read_table(engine, table: str) -> pd.DataFrame:
    return pd.read_sql(text(f"SELECT * FROM raw.{table}"), engine)


def upload_parquet(df: pd.DataFrame, s3, bucket: str, key: str) -> None:
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    buf.seek(0)
    s3.put_object(Bucket=bucket, Key=key, Body=buf.getvalue())


def export_partitioned(df: pd.DataFrame, s3, bucket: str, prefix: str, date_col: str) -> None:
    if date_col not in df.columns:
        upload_parquet(df, s3, bucket, f"{prefix}/data.parquet")
        return
    series = pd.to_datetime(df[date_col])
    df = df.copy()
    df["_partition_date"] = series.dt.strftime("%Y-%m-%d")
    for part_date, chunk in df.groupby("_partition_date"):
        chunk = chunk.drop(columns=["_partition_date"])
        upload_parquet(chunk, s3, bucket, f"{prefix}/date={part_date}/data.parquet")


def main() -> None:
    engine = create_engine(pg_url())
    s3 = boto3.client("s3", **minio_settings())
    bucket = minio_bucket()

    date_columns = {
        "production": "prod_date",
        "telemetry": "ts",
        "well_targets": "target_date",
        "pump_sensors": "ts",
        "pump_failures": "failure_ts",
        "deliveries": "delivery_date",
    }

    for table in TABLES:
        print(f"Exporting raw.{table} ...")
        df = read_table(engine, table)
        export_partitioned(
            df, s3, bucket, f"raw/{table}", date_columns.get(table, "")
        )
        print(f"  rows={len(df)}")

    print("Done. Data exported to MinIO.")


if __name__ == "__main__":
    main()
