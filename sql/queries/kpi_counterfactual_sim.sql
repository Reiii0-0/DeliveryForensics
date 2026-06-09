-- 21. Counterfactual Impact Simulation (What-If Forensics)
-- Goal: Quantify potential OTDR gain if specific bottlenecks were removed.
-- Logic: Simulate a 20% reduction in Seller Prep time (Stage 2).
SELECT
    'Baseline (Actual)' AS scenario,
    round(countIf(is_late = 0) / count() * 100, 2) AS otdr_pct,
    round(avg(total_delivery_days), 2) AS avg_delivery_days
FROM dustinia.fact_deliveries

UNION ALL

SELECT
    'Simulated (20% Faster Prep)' AS scenario,
    round(countIf(
        (stage1_hours + (stage2_hours * 0.8) + (stage3_days * 24)) / 24.0 <= 
        dateDiff('day', order_purchase_timestamp, order_estimated_delivery_date)
    ) / count() * 100, 2) AS otdr_pct,
    round(avg((stage1_hours + (stage2_hours * 0.8) + (stage3_days * 24)) / 24.0), 2) AS avg_delivery_days
FROM dustinia.fact_deliveries;
