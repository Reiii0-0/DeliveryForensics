-- 9. Customer Satisfaction vs. Delivery Latency
-- Goal: Academic validation of the business impact of lateness.
-- Standard: @data-scientist
SELECT
    f.is_late,
    round(avg(r.review_score), 2) AS avg_review_score,
    count() AS total_reviews
FROM dustinia.fact_deliveries f
JOIN dustinia.stg_order_reviews r ON f.order_id = r.order_id
GROUP BY f.is_late
ORDER BY f.is_late ASC;
