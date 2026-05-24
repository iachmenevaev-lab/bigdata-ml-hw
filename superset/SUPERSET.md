# Superset: подключение и дашборды

## 1. Запуск

```bash
docker compose up -d
```

Superset: http://localhost:8088 (admin / admin)

## 2. Подключение к PostgreSQL

- **SQLAlchemy URI:** `postgresql+psycopg2://oiluser:oilpass@postgres:5432/oilfield`
- Host с хост-машины: `localhost:5433`

Добавьте database **Oilfield** в Superset → Settings → Database.

## 3. Датасеты (SQL Lab → Save as dataset)

### Задание 1 — Аналитика добычи

**mart_production_daily** — `marts.mart_production`

```sql
SELECT prod_date, total_oil_tons, total_water_tons FROM marts.mart_production ORDER BY prod_date
```

- **Line chart:** prod_date × total_oil_tons
- **Bar chart:** `SELECT well_id, avg_flow_tpd FROM marts.mart_well_kpi ORDER BY avg_flow_tpd DESC LIMIT 10`
- **Heatmap:** telemetry avg_pressure vs avg_flow (из mart_ml_dataset)

**mart_well_kpi** — KPI по скважинам

```sql
SELECT * FROM marts.mart_well_kpi ORDER BY avg_flow_tpd DESC
```

### Задание 2 — Прогноз дебита

```sql
SELECT feature_date, daily_flow_tpd AS actual, predicted_flow AS predicted, prediction_error
FROM marts.mart_flow_predictions
ORDER BY feature_date
```

- **Line chart:** actual vs predicted по времени
- **Line chart:** prediction_error по feature_date

### Задание 3 — Аномалии и отказы

```sql
SELECT ts, pump_id, vibration_mm_s, temperature_c, is_anomaly_iso, risk_score
FROM marts.mart_failure_predictions
ORDER BY ts
```

- **Line chart:** vibration_mm_s по ts (фильтр pump_id = P-W-003)
- **Bar chart:** risk_score по pump_id

### Задание 4 — Логистика

```sql
SELECT * FROM marts.mart_logistics
```

```sql
SELECT weather, AVG(delay_hours) AS avg_delay, AVG(cost_usd / distance_km) AS cost_per_km
FROM raw.deliveries GROUP BY weather
```

- **Bar chart:** Delay vs Weather
- **Scatter:** cost_usd vs distance_km
- **Table:** KPI по driver_id из mart_logistics

## 4. MinIO

Console: http://localhost:9001 (minioadmin / minioadmin)

Bucket: `oilfield-data`, prefix: `raw/*/date=YYYY-MM-DD/`
