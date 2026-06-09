-- 14. Anomaly Detection: Distance vs Speed Outliers
-- Goal: Identify deliveries that defy "Logistics Topology" (too slow for the distance).
-- Standard: @ml-engineer
SELECT
    order_id,
    customer_state,
    seller_state,
    round(distance_km, 1) AS distance_km,
    total_delivery_days,
    round(distance_km / if(total_delivery_days=0, 0.1, total_delivery_days), 2) AS speed_km_day
FROM dustinia.fact_deliveries
WHERE total_delivery_days > 15 
  AND distance_km < 250
ORDER BY total_delivery_days DESC
LIMIT 50;
