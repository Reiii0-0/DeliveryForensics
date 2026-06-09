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
    args, _ = mock_client.command.call_args_list[1]
    assert "INSERT INTO dustinia.fact_deliveries" in args[0]


@patch('transformers.geo_transformer.get_ch_client')
@patch('transformers.geo_transformer.haversine')
def test_transform_dim_geo_logic(mock_haversine, mock_get_client):
    """Test haversine distance calculation and batch update flow."""
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    # Setup mock dataframes
    mock_client.query_df.side_effect = [
        pd.DataFrame({'zip': ['123', '456'], 'lat': [-23.5, -22.9], 'lng': [-46.6, -43.2]}), # Centroids
        pd.DataFrame({'order_id': ['ord1'], 's_zip': ['123'], 'c_zip': ['456']})             # Locations
    ]
    mock_haversine.return_value = 100.5
    
    transform_dim_geo()
    
    # Verify distance was calculated
    mock_haversine.assert_called_once()
    
    # Verify temp table was used for update
    mock_client.insert_df.assert_called_once()
    assert "dustinia.temp_distances" in mock_client.insert_df.call_args[0][0]
