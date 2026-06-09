-- ============================================================================
-- High-Risk Sellers: Target for Operational Intervention
-- Standard: @sql-pro
-- ============================================================================

-- List Top 10 sellers with more than 50 orders and the highest late rate
SELECT
    seller_id,
    seller_state,
    count() AS total_orders,
    round(countIf(is_late = 1) / count() * 100, 2) AS late_rate_pct,
    round(avg(delay_days), 1) AS avg_delay_days,
    round(countIf(seller_miss_shipping_deadline = 1) / count() * 100, 2) AS compliance_miss_rate_pct
FROM dustinia.fact_deliveries
GROUP BY seller_id, seller_state
HAVING total_orders >= 50
ORDER BY late_rate_pct DESC
LIMIT 10;
