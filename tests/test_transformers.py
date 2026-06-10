"""Unit tests for the Transformation plugins.

Standard: PEP-8, pytest
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from transformers.delivery_transformer import transform_fact_deliveries
from transformers.geo_transformer import transform_dim_geo


@patch('transformers.delivery_transformer.get_ch_client')
def test_transform_fact_deliveries_execution(mock_get_client):
    """Test that the transformation query is sent to ClickHouse."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    transform_fact_deliveries()
    
    # Verify truncate and insert were called
    assert mock_client.command.call_count >= 2
    
    # Verify that the main insert query was called at some point
    insert_called = False
    for call in mock_client.command.call_args_list:
        if "INSERT INTO dustinia.fact_deliveries" in call[0][0]:
            insert_called = True
            break
    assert insert_called, "Insert query was not executed"


def test_transform_dim_geo_logic():
    """Test transform_dim_geo is a no-op."""
    # Since logic migrated to native ClickHouse, this is just a no-op
    transform_dim_geo()
