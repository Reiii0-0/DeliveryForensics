-- ============================================================================
-- Analysis: Freight Value vs Delivery Speed
-- Goal: Understand if higher shipping costs result in faster delivery.
-- Standard: @data-scientist
-- ============================================================================

SELECT
    round(freight_value, 0) AS freight_bracket,
    avg(total_delivery_days) AS avg_delivery_days,
    count() AS total_orders
FROM dustinia.fact_deliveries
WHERE total_delivery_days > 0
GROUP BY freight_bracket
ORDER BY freight_bracket ASC
LIMIT 100;
