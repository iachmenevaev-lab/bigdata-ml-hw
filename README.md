# Big Data и ML — домашнее задание

Полный аналитический pipeline: **PostgreSQL → ETL → MinIO → обработка → Jupyter → витрины → Superset**.

## Структура репозитория

```
bigdata-ml-hw/
├── docker-compose.yml      # PostgreSQL, MinIO, Jupyter, Superset
├── sql/                    # DDL + seed data
├── etl/                    # выгрузка в MinIO, построение витрин
├── ml/                     # обучение моделей
├── notebooks/              # Jupyter-ноутбуки
├── superset/               # инструкции по дашбордам
└── scripts/run_pipeline.sh # запуск ETL + ML
```

## Быстрый старт

```bash
cd ~/bigdata-ml-hw
cp .env.example .env
docker compose up -d --build
```

Дождитесь инициализации PostgreSQL (скрипты из `sql/` применяются автоматически).

### ETL и ML (с хоста)

```bash
chmod +x scripts/run_pipeline.sh
POSTGRES_PORT=5433 ./scripts/run_pipeline.sh
```

Или из Jupyter-контейнера:

```bash
docker exec -it oilfield-jupyter bash -c "cd /home/jovyan/work && ./scripts/run_pipeline.sh"
```

## Сервисы

| Сервис    | URL                      | Логин              |
|-----------|--------------------------|--------------------|
| PostgreSQL| localhost:5433           | oiluser / oilpass  |
| MinIO     | http://localhost:9000    | minioadmin         |
| MinIO UI  | http://localhost:9001    | minioadmin         |
| Jupyter   | http://localhost:8888    | token в логах      |
| Superset  | http://localhost:8088    | admin / admin      |

## Реализованные этапы

1. **Инфраструктура** — Docker Compose (PostgreSQL, MinIO, Jupyter, Superset)
2. **ETL** — `etl/export_to_minio.py` (Parquet, партиции по дате)
3. **Обработка** — `etl/process_marts.py` (NULL, outliers, агрегации, фичи)
4. **ML** — `ml/train_models.py` (RandomForest, LinearRegression, IsolationForest)
5. **Витрины** — `marts.mart_production`, `mart_well_kpi`, `mart_ml_dataset`, `mart_logistics`, `mart_failures`, `mart_flow_predictions`
6. **BI** — см. [superset/SUPERSET.md](superset/SUPERSET.md)

## Задания

| # | Тема              | Реализация                                      |
|---|-------------------|-------------------------------------------------|
| 1 | Аналитика добычи  | витрины + KPI скважин                           |
| 2 | Прогноз дебита    | RandomForest / LinearRegression, MAE/RMSE       |
| 3 | Аномалии насосов  | z-score + IsolationForest, risk score           |
| 4 | Логистика         | факторы задержек, cost/km, KPI водителей        |

Метрики ML сохраняются в `ml/artifacts/metrics.json`.

## Jupyter

Ноутбуки в `notebooks/` дублируют pipeline для отчёта преподавателю.

## Автор

Домашнее задание по дисциплине «Big Data и ML», семинар наставника.
