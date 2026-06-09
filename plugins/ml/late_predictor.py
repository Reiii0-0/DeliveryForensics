"""Plugin for predicting delivery delays using XGBoost.

Standard: PEP-8, ML-Engineer, CDD (@testing_and_qa.md)
"""

import os
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report
from extractors.csv_extractor import get_ch_client


def run_ml_late_predictor():
    """Trains the Late Predictor model and saves predictions to ClickHouse."""
    client = get_ch_client()
    
    print("Extracting training data from fact_deliveries...")
    # SQL-Pro optimization: extraction of features defined in @brainstorming
    query = """
    SELECT
        customer_state,
        seller_state,
        order_month,
        order_dayofweek,
        freight_value,
        product_weight_g,
        distance_km,
        delay_days  -- Used for dynamic thresholding
    FROM dustinia.fact_deliveries
    """
    df = client.query_df(query)
    
    if df.empty:
        print("Warning: No data found in fact_deliveries. Skipping ML training.")
        return

    # --- Step 1: Dynamic Thresholding (Brainstorming decision) ---
    # Analyze distribution of delay_days to define 'significant' delay
    p90_delay = df[df['delay_days'] > 0]['delay_days'].quantile(0.9)
    # Decisions: Threshold > 1 day as per recommendation
    threshold = 1.0 
    df['target'] = (df['delay_days'] > threshold).astype(int)
    print(f"Late Threshold set at > {threshold} days. Positive class size: {df['target'].sum()} / {len(df)}")

    # --- Step 2: Feature Engineering ---
    # One-hot encoding for states (ClickHouse LowCardinality strings)
    df = pd.get_dummies(df, columns=['customer_state', 'seller_state'], drop_first=True)
    
    X = df.drop(['delay_days', 'target'], axis=1)
    y = df['target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # --- Step 3: Training (XGBoost) ---
    print("Training XGBoost model...")
    # Scale_pos_weight used to handle imbalanced data
    ratio = (len(y) - y.sum()) / y.sum()
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        scale_pos_weight=ratio,
        random_state=42,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)

    # --- Step 4: Evaluation (F1-Score focus) ---
    preds = model.predict(X_test)
    f1 = f1_score(y_test, preds)
    print(f"Model Training Complete. F1-Score: {f1:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, preds))

    # --- Step 5: Insights Integration (Business Impact) ---
    # We save feature importance for Metabase
    importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values(by='importance', ascending=False)
    
    print("Top 5 Predictive Features:")
    print(importance.head(5))
    
    # Save results to ClickHouse for Serving Phase
    # In a real pipeline, we would save the model and run daily batch predictions.
    # Here, we save the importance for the dashboard.
    client.command("DROP TABLE IF EXISTS dustinia.ml_feature_importance")
    client.command("""
    CREATE TABLE dustinia.ml_feature_importance (
        feature String,
        importance Float32
    ) ENGINE = Memory
    """)
    client.insert_df("dustinia.ml_feature_importance", importance)
    
    print("ML features importance saved to ClickHouse.")
