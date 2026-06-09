"""Plugin for performing Data Quality Checks (DQC) after transformation.

Standard: PEP-8, Data-Quality-Frameworks, @sql-pro
"""

from extractors.csv_extractor import get_ch_client
from airflow.exceptions import AirflowException


def validate_data_quality():
    """Runs a series of DQC checks on the analytical layer."""
    client = get_ch_client()
    
    print("Running DQC: Fact Integrity...")
    count = client.command("SELECT count() FROM dustinia.fact_deliveries")
    if count < 90000:
        raise AirflowException(f"DQC Failed: fact_deliveries has only {count} rows. Expected >= 90k.")

    print("Running DQC: Chronology Validity...")
    bad_dates = client.command("""
        SELECT count() FROM dustinia.fact_deliveries 
        WHERE order_delivered_customer_date < order_purchase_timestamp
    """)
    if bad_dates > 0:
        print(f"Warning: Found {bad_dates} records with delivered_date < purchase_date.")

    print("Running DQC: Business Logic Boundary...")
    invalid_late_flag = client.command("""
        SELECT count() FROM dustinia.fact_deliveries 
        WHERE is_late NOT IN (0, 1)
    """)
    if invalid_late_flag > 0:
        raise AirflowException(f"DQC Failed: Found {invalid_late_flag} records with invalid is_late flag.")

    print("Running DQC: Distance Calculation Integrity...")
    null_distances = client.command("""
        SELECT count() FROM dustinia.fact_deliveries 
        WHERE distance_km = 0
    """)
    null_rate = (null_distances / count) * 100
    print(f"Distance Null Rate: {null_rate:.2f}%")
    if null_rate > 10:
        print("Warning: Distance null rate is high. Check geolocation coverage.")

    print("All mandatory DQC checks passed.")
