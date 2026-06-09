-- 16. Topology Anomaly Scatter Distribution
-- Goal: Visualize the outlier cluster in Distance vs. Time space.
-- Standard: @data-scientist
SELECT
    distance_km,
    total_delivery_days,
    CASE WHEN is_late = 1 THEN 'Delayed' ELSE 'On-Time' END as status
FROM dustinia.fact_deliveries
WHERE distance_km > 0 AND total_delivery_days > 0
ORDER BY cityHash64(order_id)
LIMIT 2000;
