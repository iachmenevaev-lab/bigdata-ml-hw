#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5433}"
export MINIO_ENDPOINT="${MINIO_ENDPOINT:-localhost:9000}"

echo "==> Waiting for PostgreSQL..."
python3 - <<'PY'
import os, time
from sqlalchemy import create_engine, text
url = f"postgresql+psycopg2://{os.getenv('POSTGRES_USER','oiluser')}:{os.getenv('POSTGRES_PASSWORD','oilpass')}@{os.getenv('POSTGRES_HOST','localhost')}:{os.getenv('POSTGRES_PORT','5433')}/{os.getenv('POSTGRES_DB','oilfield')}"
for _ in range(60):
    try:
        with create_engine(url).connect() as conn:
            conn.execute(text("SELECT 1"))
        break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit("PostgreSQL not ready")
PY

pip install -q -r etl/requirements.txt

echo "==> ETL: PostgreSQL -> MinIO"
python etl/export_to_minio.py

echo "==> Processing marts"
python etl/process_marts.py

echo "==> Training ML models"
python ml/train_models.py

echo "==> Pipeline complete"
