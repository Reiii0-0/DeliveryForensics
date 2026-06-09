-- 8. Geographic Performance Clusters
-- Visualization: Bar or Table
-- Standard: @sql-pro, @data-scientist
SELECT
    cluster_label,
    customer_state,
    round(late_rate_pct, 2) AS late_rate_pct,
    round(avg_delivery_days, 1) AS avg_delivery_days,
    cluster_id
FROM dustinia.dim_geo_clusters
ORDER BY cluster_id ASC, late_rate_pct DESC;
