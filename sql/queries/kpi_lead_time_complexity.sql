-- 18. Information Theoretic Lead Time Complexity - MV Version
-- Goal: Analyze uncertainty in transit using pre-aggregated states.
SELECT
    customer_state,
    round(entropyMerge(lead_time_entropy_state), 4) AS lead_time_entropy,
    avgMerge(avg_delivery_days) AS avg_days
FROM dustinia.mv_entropy_forensics
GROUP BY customer_state
ORDER BY lead_time_entropy DESC
LIMIT 15;
