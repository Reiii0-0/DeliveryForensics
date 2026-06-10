"""Plugin for clustering regions based on operational performance.

Standard: PEP-8, Data-Scientist, @sql-pro
"""

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from extractors.csv_extractor import get_ch_client


def run_ml_geo_cluster(n_clusters: int = 4):
    """Clusters states based on late rate and delivery speed."""
    client = get_ch_client()
    
    print("Extracting performance metrics per state...")
    # SQL-Pro: Aggregating from the fact table directly
    query = """
    SELECT
        customer_state,
        avg(is_late) * 100 AS late_rate_pct,
        avg(total_delivery_days) AS avg_delivery_days
    FROM dustinia.fact_deliveries
    GROUP BY customer_state
    """
    df = client.query_df(query)
    
    if df.empty:
        print("Warning: No data found for clustering.")
        return
        
    if len(df) < n_clusters:
        print(f"Warning: Not enough states for clustering (expected >={n_clusters}, got {len(df)}). Adjusting n_clusters.")
        n_clusters = len(df)
        if n_clusters == 0:
            return

    # --- Step 1: Preprocessing ---
    X = df[['late_rate_pct', 'avg_delivery_days']]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # --- Step 2: Clustering (KMeans) ---
    print(f"Running KMeans with k={n_clusters}...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df['cluster_id'] = kmeans.fit_predict(X_scaled)

    # --- Step 3: Cluster Labeling (Decision B from brainstorming) ---
    # We assign labels based on performance ranking
    # Cluster with highest late rate = 'High Risk'
    cluster_means = df.groupby('cluster_id')['late_rate_pct'].mean().sort_values(ascending=False)
    
    label_map = {}
    labels = ["Zona Merah (Kritis)", "Zona Kuning (Waspada)", "Zona Hijau (Lancar)", "Zona Biru (Performa Tinggi)"]
    
    for i, c_id in enumerate(cluster_means.index):
        label_map[c_id] = labels[min(i, len(labels)-1)]
        
    df['cluster_label'] = df['cluster_id'].map(label_map)
    print("Clustering Results:")
    print(df[['customer_state', 'cluster_label']].head(10))

    # --- Step 4: Output Integration ---
    client.command("DROP TABLE IF EXISTS dustinia.dim_geo_clusters")
    client.command("""
    CREATE TABLE dustinia.dim_geo_clusters (
        customer_state String,
        late_rate_pct Float32,
        avg_delivery_days Float32,
        cluster_id UInt8,
        cluster_label String
    ) ENGINE = MergeTree() ORDER BY cluster_id
    """)
    client.insert_df("dustinia.dim_geo_clusters", df)
    
    print("Geospatial clusters saved to dim_geo_clusters.")
