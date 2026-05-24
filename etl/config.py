"""Shared connection settings for ETL / ML scripts."""
from __future__ import annotations

import os


def pg_url(host: str | None = None) -> str:
    user = os.getenv("POSTGRES_USER", "oiluser")
    password = os.getenv("POSTGRES_PASSWORD", "oilpass")
    db = os.getenv("POSTGRES_DB", "oilfield")
    host = host or os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def minio_settings() -> dict:
    return {
        "endpoint_url": f"http://{os.getenv('MINIO_ENDPOINT', 'localhost:9000')}",
        "aws_access_key_id": os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        "aws_secret_access_key": os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    }


def minio_bucket() -> str:
    return os.getenv("MINIO_BUCKET", "oilfield-data")
