"""Unit tests for the CSV Extractor plugin.

Standard: PEP-8, pytest
"""

import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open
from extractors.csv_extractor import extract_validate_csvs, get_ch_client


@patch('os.path.exists')
@patch('os.path.getsize')
@patch('pandas.read_csv')
@patch('builtins.open', new_callable=mock_open, read_data=b"header\nrow1\nrow2\n")
def test_extract_validate_csvs_success(mock_file, mock_read_csv, mock_getsize, mock_exists):
    """Test successful validation of all mandatory files."""
    # Setup mocks
    mock_exists.return_value = True
    mock_getsize.return_value = 1000
    mock_read_csv.return_value = pd.DataFrame([{'dummy': 1}])
    
    # Mock REQUIRED_FILES to avoid needing millions of lines in mock_file
    with patch('extractors.csv_extractor.REQUIRED_FILES', {f: 1 for f in ['orders.csv', 'order_items.csv', 'customers.csv', 'sellers.csv', 'products.csv', 'geolocation.csv', 'order_reviews.csv']}):
        result = extract_validate_csvs()
    
    assert result['status'] == 'ok'
    assert len(result['files']) == 7


@patch('os.path.exists')
@patch('os.path.getsize')
@patch('pandas.read_csv')
@patch('builtins.open', new_callable=mock_open, read_data=b"header\nrow1\n")
def test_extract_validate_csvs_missing_file(mock_file, mock_read_csv, mock_getsize, mock_exists):
    """Test that validation fails if a file is missing."""
    from airflow.exceptions import AirflowException
    
    # Setup mock: first file exists, second is missing
    mock_exists.side_effect = [True, False]
    mock_getsize.return_value = 1000
    
    # Execute & Assert
    # It will fail on the second iteration if the first one passes row count
    with patch('extractors.csv_extractor.REQUIRED_FILES', {'f1.csv': 1, 'f2.csv': 1}):
        with pytest.raises(AirflowException) as excinfo:
            extract_validate_csvs()
    
    assert "Missing mandatory file" in str(excinfo.value)


def test_get_ch_client_config():
    """Test that ClickHouse client is initialized with correct environment variables."""
    with patch('clickhouse_connect.get_client') as mock_get_client:
        with patch.dict(os.environ, {
            'CLICKHOUSE_HOST': 'test-host',
            'CLICKHOUSE_PORT': '1234',
            'CLICKHOUSE_USER': 'test-user',
            'CLICKHOUSE_PASSWORD': 'test-password',
            'CLICKHOUSE_DB': 'test-db'
        }):
            get_ch_client()
            
            mock_get_client.assert_called_once_with(
                host='test-host',
                port=1234,
                username='test-user',
                password='test-password',
                database='test-db'
            )
