#!/usr/bin/env python3
"""Clean, aggregate and load analytical marts into PostgreSQL."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import pg_url


def zscore_filter(df: pd.DataFrame, col: str, z: float = 3.0) -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return df
    mu, sigma = df[col].mean(), df[col].std()
    if sigma == 0 or np.isnan(sigma):
        return df
    return df[np.abs((df[col] - mu) / sigma) <= z]


def build_marts(engine) -> None:
    production = pd.read_sql("SELECT * FROM raw.production", engine)
    telemetry = pd.read_sql("SELECT * FROM raw.telemetry", engine)
    deliveries = pd.read_sql("SELECT * FROM raw.deliveries", engine)
    pump_sensors = pd.read_sql("SELECT * FROM raw.pump_sensors", engine)
    failures = pd.read_sql("SELECT * FROM raw.pump_failures", engine)

    # NULL handling
    production = production.fillna({"oil_tons": 0, "water_tons": 0, "gas_m3": 0})
    telemetry = telemetry.fillna({
        "flow_rate_tpd": telemetry["flow_rate_tpd"].median(),
        "pressure_bar": telemetry["pressure_bar"].median(),
        "temperature_c": telemetry["temperature_c"].median(),
        "power_kw": telemetry["power_kw"].median(),
        "downtime_min": 0,
    })

    # Outliers
    production = zscore_filter(production, "oil_tons")
    telemetry = zscore_filter(telemetry, "flow_rate_tpd")

    telemetry["day"] = pd.to_datetime(telemetry["ts"]).dt.date
    total_minutes = 24 * 60

    # Mart 1: daily production
    mart_production = (
        production.groupby("prod_date", as_index=False)
        .agg(total_oil_tons=("oil_tons", "sum"), total_water_tons=("water_tons", "sum"))
    )

    # Mart 2: well KPI
    tel_daily = (
        telemetry.groupby(["well_id", "day"], as_index=False)
        .agg(
            avg_flow=("flow_rate_tpd", "mean"),
            avg_pressure=("pressure_bar", "mean"),
            avg_temperature=("temperature_c", "mean"),
            avg_power=("power_kw", "mean"),
            downtime_min=("downtime_min", "sum"),
        )
    )
    tel_daily["downtime_pct"] = (tel_daily["downtime_min"] / total_minutes * 100).round(2)

    mart_well_kpi = (
        tel_daily.groupby("well_id", as_index=False)
        .agg(
            avg_flow_tpd=("avg_flow", "mean"),
            avg_pressure_bar=("avg_pressure", "mean"),
            avg_temperature_c=("avg_temperature", "mean"),
            downtime_pct=("downtime_pct", "mean"),
        )
    )
    mart_well_kpi["rank_flow"] = mart_well_kpi["avg_flow_tpd"].rank(ascending=False)

    # Feature table for ML (daily telemetry aggregates)
    ml_features = tel_daily.copy()
    ml_features.rename(columns={"day": "feature_date"}, inplace=True)

    targets = pd.read_sql("SELECT * FROM raw.well_targets", engine)
    ml_dataset = ml_features.merge(
        targets,
        left_on=["well_id", "feature_date"],
        right_on=["well_id", "target_date"],
        how="inner",
    )

    # Logistics mart
    deliveries = deliveries.copy()
    deliveries["cost_per_km"] = deliveries["cost_usd"] / deliveries["distance_km"].replace(0, np.nan)
    mart_logistics = (
        deliveries.groupby(["driver_id", "weather"], as_index=False)
        .agg(
            deliveries_count=("delivery_id", "count"),
            avg_delay_hours=("delay_hours", "mean"),
            avg_cost_per_km=("cost_per_km", "mean"),
            total_volume_m3=("volume_m3", "sum"),
        )
    )

    # Pump anomalies (z-score on vibration)
    pump = pump_sensors.copy()
    pump["vibration_z"] = (
        (pump["vibration_mm_s"] - pump["vibration_mm_s"].mean())
        / pump["vibration_mm_s"].std()
    )
    pump["is_anomaly"] = pump["vibration_z"].abs() > 2.5
    mart_failures = pump.merge(
        failures[["pump_id", "failure_ts"]],
        on="pump_id",
        how="left",
    )
    mart_failures["hours_to_failure"] = (
        (mart_failures["failure_ts"] - mart_failures["ts"]).dt.total_seconds() / 3600
    )

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS marts"))
        mart_production.to_sql("mart_production", conn, schema="marts", if_exists="replace", index=False)
        mart_well_kpi.to_sql("mart_well_kpi", conn, schema="marts", if_exists="replace", index=False)
        ml_dataset.to_sql("mart_ml_dataset", conn, schema="marts", if_exists="replace", index=False)
        mart_logistics.to_sql("mart_logistics", conn, schema="marts", if_exists="replace", index=False)
        mart_failures.to_sql("mart_failures", conn, schema="marts", if_exists="replace", index=False)

    print("Marts created: mart_production, mart_well_kpi, mart_ml_dataset, mart_logistics, mart_failures")


def main() -> None:
    engine = create_engine(pg_url())
    build_marts(engine)


if __name__ == "__main__":
    main()
