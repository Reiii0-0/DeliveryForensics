-- 17. Fulfillment Entropy Index (Chaos Mapping) - MV Version
-- Goal: Quantify systemic disorder using pre-aggregated entropy states.
-- Standard: @sql-optimization-patterns
SELECT
    seller_state,
    round(entropyMerge(outcome_entropy_state), 4) AS entropy_index,
    avgMerge(avg_delivery_days) AS avg_days,
    countMerge(total_volume) AS order_volume
FROM dustinia.mv_entropy_forensics
GROUP BY seller_state
HAVING order_volume >= 500
ORDER BY entropy_index DESC;
