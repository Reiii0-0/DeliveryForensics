-- 20. Entropy Drift Analysis (Temporal Chaos Trend)
-- Goal: Detect if systemic disorder is worsening over time.
-- Standard: @matematico-tao
SELECT
    year_month,
    round(entropyMerge(outcome_entropy_state), 4) AS monthly_global_entropy,
    countMerge(total_volume) AS total_volume
FROM dustinia.mv_entropy_forensics
GROUP BY year_month
ORDER BY year_month ASC;
