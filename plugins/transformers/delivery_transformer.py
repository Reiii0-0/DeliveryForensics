"""Plugin for transforming staging data into analytical tables.

Standard: PEP-8, SQL-Pro, CDD (@data_schema.md)
"""

import os
from extractors.csv_extractor import get_ch_client


def transform_fact_deliveries():
    """Executes the core transformation from stg_* to fact_deliveries."""
    client = get_ch_client()
    
    # Pseudocode from @pipeline_dag.md translated to production SQL
    query = """
    INSERT INTO dustinia.fact_deliveries (
        order_id, customer_id, seller_id, customer_state, seller_state,
        order_purchase_timestamp, order_approved_at, order_delivered_carrier_date,
        order_delivered_customer_date, order_estimated_delivery_date,
        order_month, order_year, order_dayofweek,
        stage1_hours, stage2_hours, stage3_days, total_delivery_days,
        is_late, delay_days,
        freight_value, product_weight_g, product_volume_cm3,
        distance_km, seller_miss_shipping_deadline
    )
    SELECT
        o.order_id,
        o.customer_id,
        oi.seller_id,
        c.customer_state,
        s.seller_state,

        -- Timestamps
        o.order_purchase_timestamp,
        o.order_approved_at,
        o.order_delivered_carrier_date,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,

        -- Time features
        toMonth(o.order_purchase_timestamp)      AS order_month,
        toYear(o.order_purchase_timestamp)       AS order_year,
        toDayOfWeek(o.order_purchase_timestamp)  AS order_dayofweek,

        -- Stage durations (in hours and days as per spec)
        dateDiff('hour', o.order_purchase_timestamp, o.order_approved_at)
            AS stage1_hours,
        dateDiff('hour', o.order_approved_at, o.order_delivered_carrier_date)
            AS stage2_hours,
        dateDiff('day', o.order_delivered_carrier_date, o.order_delivered_customer_date)
            AS stage3_days,
        dateDiff('day', o.order_purchase_timestamp, o.order_delivered_customer_date)
            AS total_delivery_days,

        -- Late flag (1 if actual > estimated)
        if(o.order_delivered_customer_date > o.order_estimated_delivery_date, 1, 0)
            AS is_late,
        greatest(0, dateDiff('day', o.order_estimated_delivery_date,
            o.order_delivered_customer_date))
            AS delay_days,

        -- Financial
        oi.freight_value,

        -- Product features
        p.product_weight_g,
        (p.product_length_cm * p.product_height_cm * p.product_width_cm)
            AS product_volume_cm3,

        -- Native Distance Calculation (KM)
        greatCircleDistance(c_geo.lng, c_geo.lat, s_geo.lng, s_geo.lat) / 1000.0
            AS distance_km,

        -- Seller compliance
        if(o.order_delivered_carrier_date > oi.shipping_limit_date, 1, 0)
            AS seller_miss_shipping_deadline

    FROM dustinia.stg_orders o
    JOIN dustinia.stg_order_items oi ON o.order_id = oi.order_id AND oi.order_item_id = 1
    JOIN dustinia.stg_customers c ON o.customer_id = c.customer_id
    JOIN dustinia.stg_sellers s ON oi.seller_id = s.seller_id
    LEFT JOIN dustinia.stg_products p ON oi.product_id = p.product_id
    -- Join centroids twice for Seller and Customer
    LEFT JOIN dustinia.geo_centroids s_geo ON s.seller_zip_code_prefix = s_geo.zip
    LEFT JOIN dustinia.geo_centroids c_geo ON c.customer_zip_code_prefix = c_geo.zip
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_delivered_carrier_date IS NOT NULL
      AND o.order_approved_at IS NOT NULL
    """
    
    print("Truncating fact_deliveries for fresh transformation...")
    client.command("TRUNCATE TABLE dustinia.fact_deliveries")
    
    # Also truncate materialized views to prevent data duplication
    # since they are AggregatingMergeTree triggered on fact_deliveries insert
    mv_tables = [
        'mv_state_metrics', 'mv_monthly_trend', 'mv_seller_performance',
        'mv_stage_breakdown', 'mv_freight_analysis', 'mv_entropy_forensics'
    ]
    for mv in mv_tables:
        # Check if MV exists before truncating to avoid errors on first run
        try:
            client.command(f"TRUNCATE TABLE dustinia.{mv}")
        except Exception:
            pass
    
    print("Executing main transformation query...")
    client.command(query)
    
    count = client.command("SELECT count() FROM dustinia.fact_deliveries")
    print(f"Transformation complete. Rows in fact_deliveries: {count}")


def transform_dimensions():
    """Populates dim_sellers and dim_customers from fact and staging data."""
    client = get_ch_client()
    
    # 1. dim_sellers
    seller_query = """
    INSERT INTO dustinia.dim_sellers (
        seller_id, seller_state, seller_city, total_orders, 
        late_orders, hist_late_rate, avg_delivery_days, miss_deadline_count
    )
    SELECT
        f.seller_id,
        f.seller_state,
        s.seller_city,
        count()                                AS total_orders,
        countIf(f.is_late = 1)                 AS late_orders,
        round(countIf(f.is_late = 1)/count() * 100, 2) AS hist_late_rate,
        round(avg(f.total_delivery_days), 1)   AS avg_delivery_days,
        countIf(f.seller_miss_shipping_deadline = 1) AS miss_deadline_count
    FROM dustinia.fact_deliveries f
    JOIN dustinia.stg_sellers s ON f.seller_id = s.seller_id
    GROUP BY f.seller_id, f.seller_state, s.seller_city
    """
    
    # 2. dim_customers
    customer_query = """
    INSERT INTO dustinia.dim_customers (
        customer_id, customer_unique_id, customer_city, 
        customer_state, zip_code_prefix
    )
    SELECT
        customer_id,
        customer_unique_id,
        customer_city,
        customer_state,
        customer_zip_code_prefix
    FROM dustinia.stg_customers
    """
    
    print("Refreshing dim_sellers...")
    client.command("TRUNCATE TABLE dustinia.dim_sellers")
    client.command(seller_query)
    print("Refreshing dim_customers...")
    client.command("TRUNCATE TABLE dustinia.dim_customers")
    client.command(customer_query)
