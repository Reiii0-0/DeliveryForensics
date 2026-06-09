-- ============================================================================
-- SQL DDL: Materialized Views for High-Performance Dashboarding
-- Target: ClickHouse (dustinia database)
-- Standard: @sql-pro
-- ============================================================================

-- 1. mv_state_metrics: Summary metrics per customer state
CREATE MATERIALIZED VIEW IF NOT EXISTS dustinia.mv_state_metrics
ENGINE = AggregatingMergeTree() 
ORDER BY customer_state
AS
SELECT
    customer_state,
    countState() AS total_orders,
    countIfState(is_late = 1) AS late_orders,
    avgState(total_delivery_days) AS avg_delivery_days,
    avgState(stage3_days) AS avg_stage3_days
FROM dustinia.fact_deliveries
GROUP BY customer_state;

-- 2. mv_monthly_trend: Delivery trend over time
CREATE MATERIALIZED VIEW IF NOT EXISTS dustinia.mv_monthly_trend
ENGINE = AggregatingMergeTree()
ORDER BY year_month
AS
SELECT
    toStartOfMonth(order_purchase_timestamp) AS year_month,
    countState() AS total_orders,
    countIfState(is_late = 1) AS late_orders,
    avgState(total_delivery_days) AS avg_delivery_days
FROM dustinia.fact_deliveries
GROUP BY year_month;

-- 3. mv_seller_performance: Detailed seller analytics (Filter applied at Query level)
CREATE MATERIALIZED VIEW IF NOT EXISTS dustinia.mv_seller_performance
ENGINE = AggregatingMergeTree()
ORDER BY (seller_state, seller_id)
AS
SELECT
    seller_id,
    seller_state,
    countState() AS total_orders,
    countIfState(is_late = 1) AS late_orders,
    avgState(delay_days) AS avg_delay_days,
    countIfState(seller_miss_shipping_deadline = 1) AS miss_deadline_count
FROM dustinia.fact_deliveries
GROUP BY seller_id, seller_state;

-- 4. mv_stage_breakdown: In-depth stage analysis per state
CREATE MATERIALIZED VIEW IF NOT EXISTS dustinia.mv_stage_breakdown
ENGINE = AggregatingMergeTree()
ORDER BY customer_state
AS
SELECT
    customer_state,
    avgState(stage1_hours) AS avg_stage1_hours,
    avgState(stage2_hours) AS avg_stage2_hours,
    avgState(stage3_days) AS avg_stage3_days,
    quantilesState(0.5, 0.9, 0.95)(total_delivery_days) AS delivery_percentiles
FROM dustinia.fact_deliveries
GROUP BY customer_state;

-- 5. mv_freight_analysis: Correlation between cost and speed
CREATE MATERIALIZED VIEW IF NOT EXISTS dustinia.mv_freight_analysis
ENGINE = AggregatingMergeTree()
ORDER BY freight_bucket
AS
SELECT
    floor(freight_value / 10) * 10 AS freight_bucket,
    countState() AS total_orders,
    countIfState(is_late = 1) AS late_orders,
    avgState(total_delivery_days) AS avg_delivery_days
FROM dustinia.fact_deliveries
GROUP BY freight_bucket;

-- 6. mv_entropy_forensics: Multi-stage Entropy Diagnostics (Innovation Sprint 2)
-- Standard: @sql-pro, @matematico-tao
CREATE MATERIALIZED VIEW IF NOT EXISTS dustinia.mv_entropy_forensics
ENGINE = AggregatingMergeTree()
ORDER BY (year_month, seller_state, customer_state)
AS
SELECT
    toStartOfMonth(order_purchase_timestamp) AS year_month,
    seller_state,
    customer_state,
    -- Outcome Entropy (4-State FEI)
    entropyState(toUInt8(multiIf(
        total_delivery_days <= 5,  0,
        total_delivery_days <= 10, 1,
        total_delivery_days <= 20, 2,
        3
    ))) AS outcome_entropy_state,
    -- Lead Time Complexity (Discrete Entropy)
    entropyState(toUInt8(total_delivery_days)) AS lead_time_entropy_state,
    -- Handoff Uncertainty (Seller Prep)
    entropyState(toUInt8(stage2_hours)) AS prep_entropy_state,
    -- Logistics Transit Volatility (Carrier)
    entropyState(toUInt8(stage3_days)) AS transit_entropy_state,
    -- Basic aggregations for correlation
    avgState(total_delivery_days) AS avg_delivery_days,
    countState() AS total_volume
FROM dustinia.fact_deliveries
GROUP BY year_month, seller_state, customer_state;
