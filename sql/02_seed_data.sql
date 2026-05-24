-- Seed data for oilfield homework (synthetic, reproducible)

INSERT INTO raw.wells (well_id, well_name, field_name, latitude, longitude, depth_m, status) VALUES
('W-001', 'Alpha-1',   'North Field', 55.75, 37.62, 3200, 'active'),
('W-002', 'Alpha-2',   'North Field', 55.76, 37.63, 3150, 'active'),
('W-003', 'Beta-1',    'South Field', 55.70, 37.55, 2800, 'active'),
('W-004', 'Beta-2',    'South Field', 55.71, 37.56, 2900, 'active'),
('W-005', 'Gamma-1',   'East Field',  55.78, 37.70, 3400, 'active'),
('W-006', 'Gamma-2',   'East Field',  55.79, 37.71, 3350, 'maintenance'),
('W-007', 'Delta-1',   'West Field',  55.72, 37.50, 2600, 'active'),
('W-008', 'Delta-2',   'West Field',  55.73, 37.51, 2650, 'active'),
('W-009', 'Epsilon-1', 'North Field', 55.77, 37.64, 3100, 'active'),
('W-010', 'Epsilon-2', 'South Field', 55.69, 37.54, 2750, 'active');

-- Production: 60 days for each well
INSERT INTO raw.production (well_id, prod_date, oil_tons, water_tons, gas_m3)
SELECT
    w.well_id,
    d::date,
    ROUND((80 + (random() * 40) + CASE w.well_id WHEN 'W-001' THEN 30 WHEN 'W-010' THEN -25 ELSE 0 END)::numeric, 2),
    ROUND((10 + random() * 15)::numeric, 2),
    ROUND((500 + random() * 200)::numeric, 2)
FROM raw.wells w
CROSS JOIN generate_series('2025-01-01'::date, '2025-03-01'::date, '1 day') d
WHERE w.status = 'active' OR w.well_id = 'W-006';

-- Telemetry: hourly for 14 days (sample)
INSERT INTO raw.telemetry (well_id, ts, flow_rate_tpd, pressure_bar, temperature_c, power_kw, downtime_min)
SELECT
    w.well_id,
    ts,
    ROUND((85 + sin(extract(hour from ts) / 3.0) * 10 + random() * 5)::numeric, 2),
    ROUND((120 + random() * 30)::numeric, 2),
    ROUND((45 + random() * 15)::numeric, 2),
    ROUND((200 + random() * 80)::numeric, 2),
    CASE WHEN random() < 0.05 THEN (random() * 60)::int ELSE 0 END
FROM raw.wells w
CROSS JOIN generate_series(
    '2025-02-01'::timestamp,
    '2025-02-14'::timestamp + interval '23 hours',
    '1 hour'
) ts
WHERE w.status = 'active';

-- Well targets for ML
INSERT INTO raw.well_targets (well_id, target_date, daily_flow_tpd)
SELECT well_id, prod_date, oil_tons * 1.02
FROM raw.production
WHERE prod_date >= '2025-02-01';

-- Pump sensors
INSERT INTO raw.pump_sensors (pump_id, well_id, ts, vibration_mm_s, temperature_c, current_a, rpm)
SELECT
    'P-' || w.well_id,
    w.well_id,
    ts,
    ROUND((2 + random() * 3)::numeric, 2),
    ROUND((55 + random() * 10)::numeric, 2),
    ROUND((15 + random() * 8)::numeric, 2),
    ROUND((2800 + random() * 200)::numeric, 0)
FROM raw.wells w
CROSS JOIN generate_series('2025-02-01'::timestamp, '2025-02-28'::timestamp, '4 hours') ts
WHERE w.status = 'active';

-- Pre-failure spike for W-003 pump
UPDATE raw.pump_sensors SET
    vibration_mm_s = vibration_mm_s + 8,
    temperature_c = temperature_c + 12,
    current_a = current_a + 5
WHERE well_id = 'W-003' AND ts >= '2025-02-25' AND ts < '2025-02-27';

INSERT INTO raw.pump_failures (pump_id, well_id, failure_ts, failure_type) VALUES
('P-W-003', 'W-003', '2025-02-27 14:00:00', 'bearing_wear'),
('P-W-007', 'W-007', '2025-02-20 08:30:00', 'seal_leak');

-- Deliveries
INSERT INTO raw.deliveries (route_id, driver_id, delivery_date, distance_km, volume_m3, cost_usd, delay_hours, weather) VALUES
('R-101', 'DRV-01', '2025-01-05', 120, 45, 850, 0.5, 'clear'),
('R-102', 'DRV-02', '2025-01-06', 85,  30, 520, 0,   'clear'),
('R-103', 'DRV-01', '2025-01-08', 200, 60, 1400, 3.5, 'snow'),
('R-104', 'DRV-03', '2025-01-10', 150, 50, 980, 1.2, 'rain'),
('R-105', 'DRV-02', '2025-01-12', 95,  35, 560, 0,   'clear'),
('R-106', 'DRV-01', '2025-01-15', 180, 55, 1250, 4.0, 'snow'),
('R-107', 'DRV-04', '2025-01-18', 110, 40, 720, 0.8, 'clear'),
('R-108', 'DRV-03', '2025-01-20', 220, 70, 1580, 5.0, 'storm'),
('R-109', 'DRV-02', '2025-01-22', 90,  28, 490, 0,   'clear'),
('R-110', 'DRV-01', '2025-01-25', 160, 52, 1100, 2.5, 'rain'),
('R-111', 'DRV-04', '2025-02-01', 130, 42, 800, 1.0, 'clear'),
('R-112', 'DRV-03', '2025-02-05', 190, 58, 1350, 3.0, 'snow'),
('R-113', 'DRV-02', '2025-02-10', 100, 32, 540, 0,   'clear'),
('R-114', 'DRV-01', '2025-02-15', 175, 54, 1180, 2.0, 'rain'),
('R-115', 'DRV-04', '2025-02-20', 140, 46, 870, 1.5, 'clear');
