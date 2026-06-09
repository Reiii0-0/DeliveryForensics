-- 15. Service Level Objective (SLO) Adherence
-- Goal: Measure compliance against the 95% OTDR threshold.
-- Standard: @analytics-tracking
SELECT
    toStartOfMonth(order_purchase_timestamp) AS month,
    round(countIf(is_late = 0) / count() * 100, 2) AS actual_otdr,
    95.0 AS target_slo
FROM dustinia.fact_deliveries
GROUP BY month
ORDER BY month ASC;
