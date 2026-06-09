"""Script to restore the ClickHouse database state to align with the IEEE paper.
This script orchestrates the full ELT process from within the container.
"""

import sys
import os

# Add plugins path to sys.path so we can import them
sys.path.append('/opt/airflow/plugins')

from extractors.csv_extractor import (
    init_clickhouse_schema, 
    extract_validate_csvs, 
    load_staging_clickhouse
)
from transformers.delivery_transformer import (
    transform_fact_deliveries, 
    transform_dimensions
)
from transformers.geo_transformer import create_materialized_views

def run_restoration():
    print("=== Starting DeliveryForensics Database Restoration ===")
    
    print("\n[1/5] Initializing Schema...")
    init_clickhouse_schema()
    
    print("\n[2/5] Validating Source CSVs...")
    extract_validate_csvs()
    
    print("\n[3/5] Loading Staging Tables...")
    load_staging_clickhouse()
    
    print("\n[4/5] Running Core Transformations (Fact & Dimensions)...")
    transform_fact_deliveries()
    transform_dimensions()
    
    print("\n[5/5] Creating Materialized Views...")
    create_materialized_views()
    
    print("\n=== Restoration Complete! Database aligns with IEEE Revision 5 ===")

if __name__ == "__main__":
    run_restoration()
