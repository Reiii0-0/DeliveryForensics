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
    INSERT INTO dustinia.fact_deliveries
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
        seller_id,
        seller_state,
        seller_city,
        count()                                AS total_orders,
        countIf(is_late = 1)                   AS late_orders,
        round(countIf(is_late = 1)/count() * 100, 2) AS hist_late_rate,
        round(avg(total_delivery_days), 1)     AS avg_delivery_days,
        countIf(seller_miss_shipping_deadline = 1) AS miss_deadline_count
    FROM dustinia.fact_deliveries
    JOIN dustinia.stg_sellers USING seller_id
    GROUP BY seller_id, seller_state, seller_city
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
    client.command(seller_query)
    print("Refreshing dim_customers...")
    client.command(customer_query)
