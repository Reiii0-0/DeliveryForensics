-- 10. ML Forensic Feature Importance
-- Goal: Model explainability in supply chain forensics.
-- Standard: @ml-engineer
SELECT
    feature,
    round(importance, 4) AS importance_score
FROM dustinia.ml_feature_importance
ORDER BY importance DESC;
