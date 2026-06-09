-- ============================================================================
-- SQL DDL: Fact & Dimension Tables for DustiniaDelixia Groceria
-- Target: ClickHouse (dustinia database)
-- Standard: @database-architect, @sql-pro
-- ============================================================================

-- 1. fact_deliveries (Main Analytical Table)
-- Partitioned by month to optimize time-series analytical queries.
CREATE TABLE IF NOT EXISTS dustinia.fact_deliveries (
    order_id String,
    customer_id String,
    seller_id String,
    customer_state LowCardinality(String),
    seller_state LowCardinality(String),
    
    -- Timestamps
    order_purchase_timestamp DateTime,
    order_approved_at DateTime,
    order_delivered_carrier_date DateTime,
    order_delivered_customer_date DateTime,
    order_estimated_delivery_date DateTime,
    
    -- Extracted Time Features
    order_month UInt8,
    order_year UInt16,
    order_dayofweek UInt8,
    
    -- Calculated Metrics
    stage1_hours Float32,  -- purchase -> approved
    stage2_hours Float32,  -- approved -> carrier
    stage3_days Float32,   -- carrier -> customer
    total_delivery_days Float32,
    
    -- Business Logic Flags
    is_late UInt8,
    delay_days Float32,
    
    -- Aggregated Financials & Product Info
    freight_value Float32,
    product_weight_g Float32,
    product_volume_cm3 Float32,
    
    -- Geospatial (To be updated via geo_transformer)
    distance_km Float32 DEFAULT 0.0,
    
    -- Compliance Flags
    seller_miss_shipping_deadline UInt8
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(order_purchase_timestamp)
ORDER BY (order_purchase_timestamp, customer_state, seller_id);

-- 2. dim_sellers (Analytical Dimension)
-- Uses ReplacingMergeTree for efficient updates of seller metrics.
CREATE TABLE IF NOT EXISTS dustinia.dim_sellers (
    seller_id String,
    seller_state LowCardinality(String),
    seller_city String,
    total_orders UInt32,
    late_orders UInt32,
    hist_late_rate Float32,
    avg_delivery_days Float32,
    miss_deadline_count UInt32,
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY seller_id;

-- 3. dim_customers (Analytical Dimension)
CREATE TABLE IF NOT EXISTS dustinia.dim_customers (
    customer_id String,
    customer_unique_id String,
    customer_city String,
    customer_state LowCardinality(String),
    zip_code_prefix String,
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY customer_id;
