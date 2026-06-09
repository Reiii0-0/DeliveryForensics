-- 1. OTDR (On-Time Delivery Rate)
-- Target: 95.0%
SELECT
    round(countIf(is_late = 0) / count() * 100, 2) AS otdr_pct,
    count() AS total_orders,
    countIf(is_late = 1) AS late_orders
FROM dustinia.fact_deliveries
WHERE 1=1;
