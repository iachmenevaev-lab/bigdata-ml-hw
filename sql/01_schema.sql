-- Schema: oilfield analytics homework
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS marts;

-- 1. Wells reference
CREATE TABLE raw.wells (
    well_id     VARCHAR(16) PRIMARY KEY,
    well_name   VARCHAR(64) NOT NULL,
    field_name  VARCHAR(64) NOT NULL,
    latitude    DOUBLE PRECISION,
    longitude   DOUBLE PRECISION,
    depth_m     INTEGER,
    status      VARCHAR(32) DEFAULT 'active'
);

-- 2. Daily production
CREATE TABLE raw.production (
    id          SERIAL PRIMARY KEY,
    well_id     VARCHAR(16) REFERENCES raw.wells(well_id),
    prod_date   DATE NOT NULL,
    oil_tons    DOUBLE PRECISION,
    water_tons  DOUBLE PRECISION,
    gas_m3      DOUBLE PRECISION,
    UNIQUE (well_id, prod_date)
);

-- 3. Equipment telemetry (hourly)
CREATE TABLE raw.telemetry (
    id              BIGSERIAL PRIMARY KEY,
    well_id         VARCHAR(16) REFERENCES raw.wells(well_id),
    ts              TIMESTAMP NOT NULL,
    flow_rate_tpd   DOUBLE PRECISION,
    pressure_bar    DOUBLE PRECISION,
    temperature_c   DOUBLE PRECISION,
    power_kw        DOUBLE PRECISION,
    downtime_min    INTEGER DEFAULT 0
);

-- 4. ML targets (daily debit)
CREATE TABLE raw.well_targets (
    id              SERIAL PRIMARY KEY,
    well_id         VARCHAR(16) REFERENCES raw.wells(well_id),
    target_date     DATE NOT NULL,
    daily_flow_tpd  DOUBLE PRECISION NOT NULL,
    UNIQUE (well_id, target_date)
);

-- 5. Pump sensors
CREATE TABLE raw.pump_sensors (
    id              BIGSERIAL PRIMARY KEY,
    pump_id         VARCHAR(16) NOT NULL,
    well_id         VARCHAR(16) REFERENCES raw.wells(well_id),
    ts              TIMESTAMP NOT NULL,
    vibration_mm_s    DOUBLE PRECISION,
    temperature_c   DOUBLE PRECISION,
    current_a       DOUBLE PRECISION,
    rpm             DOUBLE PRECISION
);

-- 6. Pump failures
CREATE TABLE raw.pump_failures (
    failure_id      SERIAL PRIMARY KEY,
    pump_id         VARCHAR(16) NOT NULL,
    well_id         VARCHAR(16) REFERENCES raw.wells(well_id),
    failure_ts      TIMESTAMP NOT NULL,
    failure_type    VARCHAR(64)
);

-- 7. Logistics deliveries
CREATE TABLE raw.deliveries (
    delivery_id     SERIAL PRIMARY KEY,
    route_id        VARCHAR(32) NOT NULL,
    driver_id       VARCHAR(32) NOT NULL,
    delivery_date   DATE NOT NULL,
    distance_km     DOUBLE PRECISION,
    volume_m3       DOUBLE PRECISION,
    cost_usd        DOUBLE PRECISION,
    delay_hours     DOUBLE PRECISION DEFAULT 0,
    weather         VARCHAR(32)
);

CREATE INDEX idx_production_date ON raw.production(prod_date);
CREATE INDEX idx_telemetry_ts ON raw.telemetry(ts);
CREATE INDEX idx_telemetry_well ON raw.telemetry(well_id, ts);
CREATE INDEX idx_pump_sensors_ts ON raw.pump_sensors(ts);
