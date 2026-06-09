-- ============================================================================
-- Analysis: Geographical Disparity (Late Rate by State)
-- Goal: Identify region bottlenecks.
-- Standard: @data-scientist
-- ============================================================================

SELECT
    customer_state,
    round(countIf(is_late = 1) / count() * 100, 2) AS late_rate_pct,
    avg(total_delivery_days) AS avg_delivery_days,
    count() AS total_orders
FROM dustinia.fact_deliveries
GROUP BY customer_state
ORDER BY late_rate_pct DESC;
