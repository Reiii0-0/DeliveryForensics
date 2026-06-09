-- 13. Economic Forensics: Revenue & Freight at Risk
-- Goal: Quantify the financial impact of late deliveries.
-- Standard: @data-scientist
SELECT
    toStartOfMonth(order_purchase_timestamp) AS month,
    sumIf(freight_value, is_late = 1) AS freight_at_risk,
    countIf(is_late = 1) AS late_order_volume,
    round(avgIf(freight_value, is_late = 1), 2) AS avg_late_freight_cost
FROM dustinia.fact_deliveries
GROUP BY month
ORDER BY month ASC;
