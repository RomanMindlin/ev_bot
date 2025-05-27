# Amadeus API Python Client

A simple Python client for interacting with the Amadeus API, supporting flight and hotel searches.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root with your Amadeus API credentials:
```
AMADEUS_CLIENT_ID=your_client_id
AMADEUS_CLIENT_SECRET=your_client_secret
```

You can get your API credentials by registering at [Amadeus for Developers](https://developers.amadeus.com/).

## Configuration

The client uses a settings module (`settings.py`) to manage configuration. You can customize the following settings:

- API URLs (base_url, auth_url)
- Retry configuration (max_retries, min_wait, max_wait)

Settings can be configured through:
1. Environment variables
2. `.env` file
3. Direct modification of `settings.py`

## Usage

Here's a basic example of how to use the client:

```python
from amadeus_client import AmadeusClient

# Initialize the client
client = AmadeusClient()

# Search for flights
flights = client.search_flights(
    origin="NYC",
    destination="LON",
    departure_date="2024-06-01",
    return_date="2024-06-15",
    adults=2
)

# Search for hotels
hotels = client.search_hotels(
    city_code="LON",
    check_in_date="2024-06-01",
    check_out_date="2024-06-15",
    adults=2
)

# Search for flight inspiration
inspiration = client.search_flight_inspiration(
    origin="NYC",
    max_price=500,
    departure_date="2024-06-01",
    duration=7
)
```

## Features

- Authentication with Amadeus API
- Flight search
- Flight inspiration search
- Hotel search
- Environment variable support for credentials
- Type hints for better IDE support
- Automatic retry mechanism for failed requests:
  - Maximum 3 retry attempts
  - Exponential backoff between retries (1-10 seconds)
  - Retries on network errors and HTTP errors
- Centralized configuration management using Pydantic

## Note

This client uses the Amadeus test environment by default. For production use, you'll need to modify the `base_url` and `auth_url` in the settings module to point to the production environment. 