#!/usr/bin/env python3
"""Train ML models: flow forecast, failure risk, logistics delay factors."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "etl"))
from config import pg_url

MODELS_DIR = Path(__file__).resolve().parent / "artifacts"
MODELS_DIR.mkdir(exist_ok=True)


def eval_regression(y_true, y_pred) -> dict:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
    }


def train_flow_model(df: pd.DataFrame) -> dict:
    features = ["avg_pressure", "avg_temperature", "avg_power", "downtime_min"]
    target = "daily_flow_tpd"
    data = df.dropna(subset=features + [target])
    X = data[features]
    y = data[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    pred = rf.predict(X_test)
    metrics = eval_regression(y_test, pred)
    joblib.dump(rf, MODELS_DIR / "flow_random_forest.joblib")

    lr = LinearRegression()
    lr.fit(X_train, y_train)
    pred_lr = lr.predict(X_test)
    metrics["linear_regression"] = eval_regression(y_test, pred_lr)
    joblib.dump(lr, MODELS_DIR / "flow_linear_regression.joblib")

    # Save predictions for Superset
    out = X_test.copy()
    out["actual"] = y_test.values
    out["predicted"] = pred
    out["error"] = out["actual"] - out["predicted"]
    out["model"] = "RandomForest"
    return metrics


def train_failure_model(engine) -> dict:
    pump = pd.read_sql("SELECT * FROM marts.mart_failures", engine)
    pump["failed_within_48h"] = (
        pump["hours_to_failure"].notna() & (pump["hours_to_failure"].between(0, 48))
    ).astype(int)
    features = ["vibration_mm_s", "temperature_c", "current_a", "rpm"]
    data = pump.dropna(subset=features)
    X = data[features]
    y = data["failed_within_48h"]

    iso = IsolationForest(contamination=0.05, random_state=42)
    data = data.copy()
    data["anomaly_score"] = iso.fit_predict(X)
    data["is_anomaly_iso"] = (data["anomaly_score"] == -1).astype(int)

    rf = RandomForestRegressor(n_estimators=50, random_state=42)
    rf.fit(X, y)
    data["risk_score"] = rf.predict(X)
    joblib.dump(rf, MODELS_DIR / "failure_risk.joblib")
    joblib.dump(iso, MODELS_DIR / "isolation_forest.joblib")

    data.to_sql("mart_failure_predictions", engine, schema="marts", if_exists="replace", index=False)
    return {"anomaly_rate": float(data["is_anomaly_iso"].mean()), "samples": len(data)}


def train_logistics_model(engine) -> dict:
    df = pd.read_sql("SELECT * FROM raw.deliveries", engine)
    cat = ["weather"]
    num = ["distance_km", "volume_m3"]
    y = df["delay_hours"]

    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
        ("num", "passthrough", num),
    ])
    pipe = Pipeline([
        ("pre", pre),
        ("model", RandomForestRegressor(n_estimators=50, random_state=42)),
    ])
    X = df[cat + num]
    pipe.fit(X, y)
    joblib.dump(pipe, MODELS_DIR / "logistics_delay.joblib")
    df["predicted_delay"] = pipe.predict(X)
    df.to_sql("mart_logistics_predictions", engine, schema="marts", if_exists="replace", index=False)
    return eval_regression(y, df["predicted_delay"])


def main() -> None:
    engine = create_engine(pg_url())
    ml_df = pd.read_sql("SELECT * FROM marts.mart_ml_dataset", engine)

    flow_metrics = train_flow_model(ml_df)
    failure_metrics = train_failure_model(engine)
    logistics_metrics = train_logistics_model(engine)

    # Save flow predictions to DB
    features = ["avg_pressure", "avg_temperature", "avg_power", "downtime_min"]
    rf = joblib.load(MODELS_DIR / "flow_random_forest.joblib")
    pred_df = ml_df.dropna(subset=features).copy()
    pred_df["predicted_flow"] = rf.predict(pred_df[features])
    pred_df["prediction_error"] = pred_df["daily_flow_tpd"] - pred_df["predicted_flow"]
    pred_df[["well_id", "feature_date", "daily_flow_tpd", "predicted_flow", "prediction_error"]].to_sql(
        "mart_flow_predictions", engine, schema="marts", if_exists="replace", index=False
    )

    report = {
        "flow_forecast": flow_metrics,
        "failure_detection": failure_metrics,
        "logistics_delay": logistics_metrics,
    }
    (MODELS_DIR / "metrics.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
