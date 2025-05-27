import pytest
from unittest.mock import Mock, patch
from ev_bot.amadeus_client import AmadeusClient


@pytest.fixture
def mock_response():
    """Fixture for mock API response."""
    mock = Mock()
    mock.json.return_value = {
        "data": [
            {
                "id": "test_id",
                "type": "test_type"
            }
        ]
    }
    mock.raise_for_status = Mock()
    return mock


@pytest.fixture
def mock_requests():
    """Fixture for mocking requests library."""
    with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
        mock_post.return_value = Mock(
            json=lambda: {"access_token": "test_token"},
            raise_for_status=Mock()
        )
        mock_get.return_value = Mock(
            json=lambda: {"data": [{"id": "test_id"}]},
            raise_for_status=Mock()
        )
        yield mock_post, mock_get


@pytest.fixture
def amadeus_client(mock_requests):
    """Fixture for AmadeusClient instance with mocked requests."""
    with patch("ev_bot.amadeus_client.settings") as mock_settings:
        mock_settings.client_id = "test_client_id"
        mock_settings.client_secret = "test_client_secret"
        client = AmadeusClient()
        return client 