-- 12. Chain-of-Custody: Handoff Latency Analysis
-- Goal: Identify where "The Digital Handshake" fails between Seller and Carrier.
-- Standard: @sql-pro
SELECT
    customer_state,
    round(avg(stage1_hours), 1) AS avg_approval_lag_hrs,
    round(avg(stage2_hours), 1) AS avg_seller_prep_hrs,
    round(avg(stage3_days * 24), 1) AS avg_carrier_transit_hrs
FROM dustinia.fact_deliveries
GROUP BY customer_state
ORDER BY avg_seller_prep_hrs DESC
LIMIT 20;
