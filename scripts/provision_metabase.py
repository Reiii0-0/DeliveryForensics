import os
import time
from metabase_api import MetabaseAPI

def main():
    # Configuration
    metabase_url = "http://metabase:3000"
    admin_email = "admin@dustinia.com"
    admin_pass = "DustiniaMaster2026!" 
    
    clickhouse_host = "clickhouse"
    clickhouse_db = "dustinia"
    clickhouse_user = "default"
    clickhouse_pass = "dustiniapassword"

    api = MetabaseAPI(metabase_url, admin_email, admin_pass)

    # 1. Authenticate or Setup
    print("Connecting to Metabase API...")
    if not api.authenticate():
        print("Initial authentication failed. Attempting fresh setup...")
        if not api.setup_fresh("Tech", "Lead"):
            print("Failed to setup Metabase. Exiting.")
            return

    # 2. Database Connection
    db_details = {
        "host": clickhouse_host,
        "port": 8123,
        "dbname": clickhouse_db,
        "user": clickhouse_user,
        "password": clickhouse_pass,
        "ssl": False
    }
    db_id = api.add_database("Dustinia ClickHouse", "clickhouse", db_details)
    if not db_id:
        return

    # 3. Organization (Collection & Dashboard)
    collection_id = api.create_collection("Delivery Forensics Center")
    dash_id = api.create_dashboard("Operational Health Command Center", collection_id)

    # 4. Sync Metrics (Cards) with Visualizations (Aesthetic Forensic Catalog)
    queries_path = os.path.join(os.path.dirname(__file__), '..', 'sql', 'queries')
    
    # { name: (filename, display_type, viz_settings) }
    metric_configs = {
        # Tab 1: Executive Health
        '1. On-Time Delivery Rate (OTDR)': ('kpi_otdr.sql', 'scalar', {
            "scalar.suffix": "%", "scalar.field": "otdr_pct"
        }),
        '2. Avg Fulfillment Cycle (Days)': ('kpi_cycle_time.sql', 'scalar', {
            "scalar.suffix": " days", "scalar.field": "avg_cycle_days"
        }),
        '3. Monthly SLO Adherence Trend': ('kpi_slo_adherence.sql', 'area', {
            "graph.dimensions": ["month"], "graph.metrics": ["actual_otdr", "target_slo"],
            "stackable.stack_type": None, "graph.y_axis.min": 80, "graph.y_axis.max": 100
        }),
        
        # Tab 2: Operational Forensics
        '6. Logistics Anomaly Map (Scatter Distribution)': ('kpi_topology_scatter.sql', 'scatter', {
            "graph.dimensions": ["distance_km", "total_delivery_days"], 
            "graph.metrics": ["status"],
            "graph.show_values": False,
            "graph.x_axis.title_text": "Shipping Distance (KM)", 
            "graph.y_axis.title_text": "Actual Delivery Time (Days)"
        }),
        '16. Critical Delay Audit (High Priority)': ('kpi_topology_anomalies.sql', 'table', {}),
        '4. Stage Bottleneck Analysis': ('kpi_stage_breakdown.sql', 'bar', {
            "graph.dimensions": ["stage"], "graph.metrics": ["avg_value"]
        }),
        '5. Handoff Efficiency (Seller vs Carrier)': ('kpi_handoff_latency.sql', 'bar', {
            "graph.dimensions": ["customer_state"], 
            "graph.metrics": ["avg_seller_prep_hrs", "avg_carrier_transit_hrs"],
            "stackable.stack_type": "stacked"
        }),

        # Tab 3: Economic Efficiency
        '7. Revenue & Freight at Risk': ('kpi_revenue_at_risk.sql', 'bar', {
            "graph.dimensions": ["month"], "graph.metrics": ["freight_at_risk"]
        }),
        '8. Freight vs Speed Correlation': ('kpi_freight_correlation.sql', 'line', {
            "graph.dimensions": ["freight_bracket"], "graph.metrics": ["avg_delivery_days"]
        }),
        '9. Distance vs Speed Frontier': ('kpi_distance_efficiency.sql', 'line', {
            "graph.dimensions": ["distance_bucket"], "graph.metrics": ["avg_delivery_days"]
        }),

        # Tab 4: Partner Audit
        '11. Geographic Performance Clusters': ('kpi_geo_clusters.sql', 'row', {
            "graph.dimensions": ["cluster_label", "customer_state"], 
            "graph.metrics": ["late_rate_pct"],
            "graph.show_values": True
        }),
        '12. State-wise Performance Ranking': ('kpi_geo_disparity.sql', 'row', {
            "graph.dimensions": ["customer_state"], "graph.metrics": ["late_rate_pct"]
        }),
        '10. Seller Performance Matrix': ('kpi_seller_performance.sql', 'table', {}),
        '13. Seller vs Regional Benchmark': ('kpi_seller_benchmark.sql', 'table', {}),

        # Tab 5: AI & Sentiment
        '14. Customer Sentiment vs Latency': ('kpi_review_impact.sql', 'bar', {
            "graph.dimensions": ["is_late"], "graph.metrics": ["avg_review_score"], "graph.show_values": True
        }),
        '15. ML Forensic Feature Importance': ('kpi_feature_importance.sql', 'bar', {
            "graph.dimensions": ["feature"], "graph.metrics": ["importance_score"]
        }),

        # Tab 6: Forensic Entropy (Chaos)
        '17. Fulfillment Entropy Index (FEI)': ('kpi_fulfillment_entropy.sql', 'bar', {
            "graph.dimensions": ["seller_state"], "graph.metrics": ["entropy_index"],
            "graph.x_axis.title_text": "Shipping Hub", "graph.y_axis.title_text": "Chaos Score (Bits)"
        }),
        '18. Lead Time Complexity Map': ('kpi_lead_time_complexity.sql', 'row', {
            "graph.dimensions": ["customer_state"], "graph.metrics": ["lead_time_entropy"]
        }),
        '20. Temporal Entropy Drift': ('kpi_entropy_drift.sql', 'line', {
            "graph.dimensions": ["year_month"], "graph.metrics": ["monthly_global_entropy"],
            "graph.y_axis.title_text": "Global System Entropy"
        }),

        # Tab 7: Causal Counterfactuals
        '21. Counterfactual Impact Simulation': ('kpi_counterfactual_sim.sql', 'bar', {
            "graph.dimensions": ["scenario"], "graph.metrics": ["otdr_pct"],
            "graph.show_values": True, "graph.y_axis.title_text": "Predicted OTDR %"
        }),
        '19. N-Tier Forensic Risk Attribution': ('kpi_tier_attribution.sql', 'table', {})
    }

    cards_by_name = {}
    print("Synchronizing 21 forensic metrics with aesthetic visual styles...")
    for name, config in metric_configs.items():
        filename, display, viz_settings = config
        file_path = os.path.join(queries_path, filename)
        if not os.path.exists(file_path):
            print(f"Warning: {file_path} not found.")
            continue
            
        with open(file_path, 'r') as f:
            sql_clean = "\n".join([line for row in f.read().split('\n') if not (line := row.strip()).startswith('--')])
            sql_clean = sql_clean.rstrip(';').strip()
            
        card_id = api.sync_card(name, collection_id, db_id, sql_clean, display, viz_settings)
        if card_id:
            cards_by_name[name] = card_id

    # 5. Finalize Dashboard with Aesthetic High-Density Grid (Sprint 2 Final)
    tab_definitions = [
        {
            "name": "I. Executive Health",
            "cards": [
                {"id": cards_by_name.get('1. On-Time Delivery Rate (OTDR)'), "width": 9, "height": 4},
                {"id": cards_by_name.get('2. Avg Fulfillment Cycle (Days)'), "width": 9, "height": 4},
                {"id": cards_by_name.get('3. Monthly SLO Adherence Trend'), "width": 18, "height": 6}
            ]
        },
        {
            "name": "II. Anomaly Detection",
            "cards": [
                {"id": cards_by_name.get('6. Logistics Anomaly Map (Scatter Distribution)'), "width": 18, "height": 10},
                {"id": cards_by_name.get('16. Critical Delay Audit (High Priority)'), "width": 18, "height": 8},
                {"id": cards_by_name.get('4. Stage Bottleneck Analysis'), "width": 9, "height": 6},
                {"id": cards_by_name.get('5. Handoff Efficiency (Seller vs Carrier)'), "width": 9, "height": 6}
            ]
        },
        {
            "name": "III. Economic & Distance",
            "cards": [
                {"id": cards_by_name.get('7. Revenue & Freight at Risk'), "width": 18, "height": 6},
                {"id": cards_by_name.get('8. Freight vs Speed Correlation'), "width": 9, "height": 6},
                {"id": cards_by_name.get('9. Distance vs Speed Frontier'), "width": 9, "height": 6}
            ]
        },
        {
            "name": "IV. Partner Audit",
            "cards": [
                {"id": cards_by_name.get('12. State-wise Performance Ranking'), "width": 18, "height": 12},
                {"id": cards_by_name.get('11. Geographic Performance Clusters'), "width": 18, "height": 12},
                {"id": cards_by_name.get('10. Seller Performance Matrix'), "width": 18, "height": 8},
                {"id": cards_by_name.get('13. Seller vs Regional Benchmark'), "width": 18, "height": 8}
            ]
        },
        {
            "name": "V. AI & Sentiment",
            "cards": [
                {"id": cards_by_name.get('14. Customer Sentiment vs Latency'), "width": 9, "height": 6},
                {"id": cards_by_name.get('15. ML Forensic Feature Importance'), "width": 9, "height": 6}
            ]
        },
        {
            "name": "VI. Forensic Simulation",
            "cards": [
                {"id": cards_by_name.get('21. Counterfactual Impact Simulation'), "width": 18, "height": 8},
                {"id": cards_by_name.get('17. Fulfillment Entropy Index (FEI)'), "width": 18, "height": 8},
                {"id": cards_by_name.get('20. Temporal Entropy Drift'), "width": 18, "height": 6},
                {"id": cards_by_name.get('18. Lead Time Complexity Map'), "width": 9, "height": 8},
                {"id": cards_by_name.get('19. N-Tier Forensic Risk Attribution'), "width": 9, "height": 8}
            ]
        }
    ]
    
    # Filter out None values
    for tab in tab_definitions:
        tab['cards'] = [c for c in tab['cards'] if c['id'] is not None]

    api.finalize_dashboard(dash_id, tab_definitions)

    print(f"\nSUCCESS! Sprint 2 Dashboard is live at http://localhost:3000/dashboard/{dash_id}")

if __name__ == "__main__":
    main()
