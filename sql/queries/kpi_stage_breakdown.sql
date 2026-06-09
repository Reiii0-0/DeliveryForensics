-- ============================================================================
-- Stage Breakdown: Identifying the Operational Bottleneck
-- Standard: @sql-pro
-- ============================================================================

-- Average hours spent in each fulfillment stage
SELECT
    'S1: Approval Lag' AS stage,
    round(avg(stage1_hours), 1) AS avg_value,
    'Hours' AS unit
FROM dustinia.fact_deliveries

UNION ALL

SELECT
    'S2: Seller Prep' AS stage,
    round(avg(stage2_hours), 1) AS avg_value,
    'Hours' AS unit
FROM dustinia.fact_deliveries

UNION ALL

SELECT
    'S3: Last Mile' AS stage,
    round(avg(stage3_days) * 24, 1) AS avg_value, -- Convert days to hours for comparison
    'Hours' AS unit
FROM dustinia.fact_deliveries;
