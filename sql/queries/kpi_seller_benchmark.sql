-- ============================================================================
-- Seller Benchmarking: Specific Seller vs Regional Average
-- Standard: @sql-pro, @analytics-tracking
-- ============================================================================

-- This query compares a specific seller (by ID) against other sellers in the same state
WITH regional_avg AS (
    SELECT
        customer_state,
        avg(total_delivery_days) AS state_avg_delivery_days,
        avg(is_late) * 100 AS state_avg_late_rate
    FROM dustinia.fact_deliveries
    GROUP BY customer_state
)
SELECT
    f.seller_id,
    f.customer_state,
    round(avg(f.total_delivery_days), 1) AS seller_avg_delivery_days,
    round(r.state_avg_delivery_days, 1) AS regional_benchmark_days,
    round(avg(f.is_late) * 100, 2) AS seller_late_rate_pct,
    round(r.state_avg_late_rate, 2) AS regional_benchmark_late_rate
FROM dustinia.fact_deliveries f
JOIN regional_avg r ON f.customer_state = r.customer_state
WHERE 1=1
-- Metabase filter:
-- [[AND f.seller_id = {{seller_id}}]]
GROUP BY f.seller_id, f.customer_state, r.state_avg_delivery_days, r.state_avg_late_rate;
