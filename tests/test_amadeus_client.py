import pytest
from unittest.mock import Mock, patch
from requests.exceptions import RequestException, HTTPError
from ev_bot.amadeus_client import AmadeusClient


def test_client_initialization(amadeus_client):
    """Test client initialization with credentials."""
    assert amadeus_client.client_id == "test_client_id"
    assert amadeus_client.client_secret == "test_client_secret"
    assert amadeus_client.access_token == "test_token"


def test_client_initialization_without_credentials():
    """Test client initialization without credentials raises error."""
    with patch("ev_bot.amadeus_client.settings") as mock_settings:
        mock_settings.client_id = None
        mock_settings.client_secret = None
        with pytest.raises(ValueError, match="Amadeus API credentials not found"):
            AmadeusClient()


def test_search_flights(amadeus_client, mock_requests):
    """Test flight search functionality."""
    mock_post, mock_get = mock_requests
    
    result = amadeus_client.search_flights(
        origin="NYC",
        destination="LON",
        departure_date="2024-06-01"
    )
    
    # Verify the request was made with correct parameters
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "shopping/flight-offers" in args[0]
    assert kwargs["params"]["originLocationCode"] == "NYC"
    assert kwargs["params"]["destinationLocationCode"] == "LON"
    assert kwargs["params"]["departureDate"] == "2024-06-01"
    
    # Verify the response
    assert result == {"data": [{"id": "test_id"}]}


def test_search_hotels(amadeus_client, mock_requests):
    """Test hotel search functionality."""
    mock_post, mock_get = mock_requests
    
    result = amadeus_client.search_hotels(
        city_code="LON",
        check_in_date="2024-06-01",
        check_out_date="2024-06-15"
    )
    
    # Verify the request was made with correct parameters
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "reference-data/locations/hotels/by-city" in args[0]
    assert kwargs["params"]["cityCode"] == "LON"
    assert kwargs["params"]["checkInDate"] == "2024-06-01"
    assert kwargs["params"]["checkOutDate"] == "2024-06-15"
    
    # Verify the response
    assert result == {"data": [{"id": "test_id"}]}


def test_search_flight_inspiration(amadeus_client, mock_requests):
    """Test flight inspiration search functionality."""
    mock_post, mock_get = mock_requests
    
    result = amadeus_client.search_flight_inspiration(
        origin="NYC",
        max_price=500,
        departure_date="2024-06-01"
    )
    
    # Verify the request was made with correct parameters
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "shopping/flight-destinations" in args[0]
    assert kwargs["params"]["origin"] == "NYC"
    assert kwargs["params"]["maxPrice"] == 500
    assert kwargs["params"]["departureDate"] == "2024-06-01"
    
    # Verify the response
    assert result == {"data": [{"id": "test_id"}]}


def test_retry_on_request_exception(amadeus_client, mock_requests):
    """Test retry mechanism on request exception."""
    mock_post, mock_get = mock_requests
    
    # Make the first call raise an exception, then succeed
    mock_get.side_effect = [
        RequestException("Connection error"),
        Mock(json=lambda: {"data": [{"id": "test_id"}]}, raise_for_status=Mock())
    ]
    
    result = amadeus_client.search_flights(
        origin="NYC",
        destination="LON",
        departure_date="2024-06-01"
    )
    
    # Verify the request was retried
    assert mock_get.call_count == 2
    assert result == {"data": [{"id": "test_id"}]}


def test_retry_on_http_error(amadeus_client, mock_requests):
    """Test retry mechanism on HTTP error."""
    mock_post, mock_get = mock_requests
    
    # Make the first call raise an HTTP error, then succeed
    mock_get.side_effect = [
        HTTPError("500 Server Error"),
        Mock(json=lambda: {"data": [{"id": "test_id"}]}, raise_for_status=Mock())
    ]
    
    result = amadeus_client.search_flights(
        origin="NYC",
        destination="LON",
        departure_date="2024-06-01"
    )
    
    # Verify the request was retried
    assert mock_get.call_count == 2
    assert result == {"data": [{"id": "test_id"}]} 