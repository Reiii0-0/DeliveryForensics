-- 11. Distance vs Speed Efficiency Frontier
-- Goal: Analyze if logitics speed scales linearly with distance.
-- Standard: @data-scientist
SELECT
    round(distance_km, -1) AS distance_bucket,
    avg(total_delivery_days) AS avg_delivery_days,
    count() AS order_count
FROM dustinia.fact_deliveries
WHERE distance_km > 0 AND total_delivery_days > 0
GROUP BY distance_bucket
ORDER BY distance_bucket ASC
LIMIT 500;
