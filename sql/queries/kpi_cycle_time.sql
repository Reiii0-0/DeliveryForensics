-- 2. Average Fulfillment Cycle Time (Days)
SELECT
    round(avg(total_delivery_days), 1) AS avg_cycle_days
FROM dustinia.fact_deliveries
WHERE 1=1;
