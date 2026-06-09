-- ============================================================================
-- SQL DDL: Staging Tables for DustiniaDelixia Groceria
-- Target: ClickHouse (dustinia database)
-- Standard: @sql-pro
-- ============================================================================

CREATE DATABASE IF NOT EXISTS dustinia;

-- 1. stg_orders
CREATE TABLE IF NOT EXISTS dustinia.stg_orders (
    order_id String,
    customer_id String,
    order_status LowCardinality(String),
    order_purchase_timestamp DateTime,
    order_approved_at Nullable(DateTime),
    order_delivered_carrier_date Nullable(DateTime),
    order_delivered_customer_date Nullable(DateTime),
    order_estimated_delivery_date DateTime
) ENGINE = MergeTree() 
ORDER BY order_purchase_timestamp;

-- 2. stg_order_items
CREATE TABLE IF NOT EXISTS dustinia.stg_order_items (
    order_id String,
    order_item_id UInt8,
    product_id String,
    seller_id String,
    shipping_limit_date DateTime,
    price Float32,
    freight_value Float32
) ENGINE = MergeTree() 
ORDER BY order_id;

-- 3. stg_customers
CREATE TABLE IF NOT EXISTS dustinia.stg_customers (
    customer_id String,
    customer_unique_id String,
    customer_zip_code_prefix String,
    customer_city String,
    customer_state LowCardinality(String)
) ENGINE = MergeTree() 
ORDER BY customer_id;

-- 4. stg_sellers
CREATE TABLE IF NOT EXISTS dustinia.stg_sellers (
    seller_id String,
    seller_zip_code_prefix String,
    seller_city String,
    seller_state LowCardinality(String)
) ENGINE = MergeTree() 
ORDER BY seller_id;

-- 5. stg_products
CREATE TABLE IF NOT EXISTS dustinia.stg_products (
    product_id String,
    product_category_name Nullable(String),
    product_weight_g Nullable(Float32),
    product_length_cm Nullable(Float32),
    product_height_cm Nullable(Float32),
    product_width_cm Nullable(Float32)
) ENGINE = MergeTree() 
ORDER BY product_id;

-- 6. stg_geolocation
CREATE TABLE IF NOT EXISTS dustinia.stg_geolocation (
    geolocation_zip_code_prefix String,
    geolocation_lat Float64,
    geolocation_lng Float64,
    geolocation_city String,
    geolocation_state LowCardinality(String)
) ENGINE = MergeTree() 
ORDER BY geolocation_zip_code_prefix;

-- 7. stg_order_reviews
CREATE TABLE IF NOT EXISTS dustinia.stg_order_reviews (
    review_id String,
    order_id String,
    review_score UInt8,
    review_comment_title Nullable(String),
    review_comment_message Nullable(String),
    review_creation_date DateTime,
    review_answer_timestamp Nullable(DateTime)
) ENGINE = MergeTree() 
ORDER BY review_creation_date;

-- 8. geo_centroids (Internal reference for distance calculation)
CREATE TABLE IF NOT EXISTS dustinia.geo_centroids (
    zip String,
    lat Float64,
    lng Float64
) ENGINE = MergeTree()
ORDER BY zip;
