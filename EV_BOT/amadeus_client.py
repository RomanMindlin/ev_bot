import requests
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ev_bot.settings import settings
from ev_bot.logger import setup_logger


logger = setup_logger("amadeus_client")


class AmadeusClient:
    """Amadeus API Client for making requests to Amadeus APIs."""
    
    BASE_URL = "https://test.api.amadeus.com/v2"  # Test environment
    AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
    
    # Retry configuration
    MAX_RETRIES = 3
    MIN_WAIT = 1  # seconds
    MAX_WAIT = 10  # seconds
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Initialize the Amadeus client.
        
        Args:
            client_id (str, optional): Amadeus API client ID. If not provided, will look for AMADEUS_CLIENT_ID in environment.
            client_secret (str, optional): Amadeus API client secret. If not provided, will look for AMADEUS_CLIENT_SECRET in environment.
        """
        logger.info("Initializing AmadeusClient")
        self.client_id = client_id or settings.client_id
        self.client_secret = client_secret or settings.client_secret
        
        if not self.client_id or not self.client_secret:
            logger.error("Amadeus API credentials not found")
            raise ValueError("Amadeus API credentials not found. Please provide client_id and client_secret or set environment variables.")
        
        self.access_token = None
        self._authenticate()
        logger.info("AmadeusClient initialized successfully")
    
    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=settings.min_wait, max=settings.max_wait),
        retry=retry_if_exception_type((requests.RequestException, requests.HTTPError))
    )
    def _authenticate(self) -> None:
        """Authenticate with Amadeus API and get access token."""
        logger.info("Authenticating with Amadeus API")
        auth_data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(settings.auth_url, data=auth_data)
            response.raise_for_status()
            self.access_token = response.json()["access_token"]
            logger.info("Successfully authenticated with Amadeus API")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=settings.min_wait, max=settings.max_wait),
        retry=retry_if_exception_type((requests.RequestException, requests.HTTPError))
    )
    def search_flights(self, 
                      origin: str,
                      destination: str,
                      departure_date: str,
                      return_date: Optional[str] = None,
                      adults: int = 1,
                      currency_code: str = "USD") -> Dict[str, Any]:
        """
        Search for flights using Amadeus Flight Offers Search API.
        
        Args:
            origin (str): Origin airport IATA code
            destination (str): Destination airport IATA code
            departure_date (str): Departure date in YYYY-MM-DD format
            return_date (str, optional): Return date in YYYY-MM-DD format for round trips
            adults (int, optional): Number of adult travelers. Defaults to 1.
            currency_code (str, optional): Currency code for prices. Defaults to USD.
            
        Returns:
            Dict[str, Any]: Flight search results
        """
        logger.info(f"Searching flights from {origin} to {destination} on {departure_date}")
        endpoint = f"{settings.base_url}/shopping/flight-offers"
        
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "currencyCode": currency_code,
            "max": 5  # Limit results to 5 offers
        }
        
        if return_date:
            params["returnDate"] = return_date
            logger.info(f"Round trip with return date {return_date}")
        
        try:
            response = requests.get(endpoint, headers=self._get_headers(), params=params)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Found {len(result.get('data', []))} flight offers")
            return result
        except Exception as e:
            logger.error(f"Flight search failed: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=settings.min_wait, max=settings.max_wait),
        retry=retry_if_exception_type((requests.RequestException, requests.HTTPError))
    )
    def search_hotels(self,
                     city_code: str,
                     check_in_date: str,
                     check_out_date: str,
                     adults: int = 1,
                     radius: int = 5,
                     radius_unit: str = "KM") -> Dict[str, Any]:
        """
        Search for hotels using Amadeus Hotel Search API.
        
        Args:
            city_code (str): City IATA code
            check_in_date (str): Check-in date in YYYY-MM-DD format
            check_out_date (str): Check-out date in YYYY-MM-DD format
            adults (int, optional): Number of adult guests. Defaults to 1.
            radius (int, optional): Search radius. Defaults to 5.
            radius_unit (str, optional): Radius unit (KM or MI). Defaults to KM.
            
        Returns:
            Dict[str, Any]: Hotel search results
        """
        logger.info(f"Searching hotels in {city_code} from {check_in_date} to {check_out_date}")
        endpoint = f"{settings.base_url}/reference-data/locations/hotels/by-city"
        
        params = {
            "cityCode": city_code,
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "adults": adults,
            "radius": radius,
            "radiusUnit": radius_unit
        }
        
        try:
            response = requests.get(endpoint, headers=self._get_headers(), params=params)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Found {len(result.get('data', []))} hotels")
            return result
        except Exception as e:
            logger.error(f"Hotel search failed: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=settings.min_wait, max=settings.max_wait),
        retry=retry_if_exception_type((requests.RequestException, requests.HTTPError))
    )
    def search_flight_inspiration(self,
                                origin: str,
                                one_way: bool = True,
                                max_price: Optional[int] = None,
                                currency_code: str = "USD",
                                departure_date: Optional[str] = None,
                                return_date: Optional[str] = None,
                                duration: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for flight inspiration using Amadeus Flight Inspiration Search API.
        This API helps users discover destinations based on their origin and budget.
        
        Args:
            origin (str): Origin airport IATA code
            one_way (bool, optional): Whether to search for one-way flights. Defaults to True.
            max_price (int, optional): Maximum price for the flight in the specified currency
            currency_code (str, optional): Currency code for prices. Defaults to USD.
            departure_date (str, optional): Departure date in YYYY-MM-DD format
            return_date (str, optional): Return date in YYYY-MM-DD format for round trips
            duration (int, optional): Trip duration in days
            
        Returns:
            Dict[str, Any]: Flight inspiration search results
        """
        logger.info(f"Searching flight inspiration from {origin}")
        endpoint = f"{settings.base_url}/shopping/flight-destinations"
        
        params = {
            "origin": origin,
            "oneWay": str(one_way).lower(),
            "currencyCode": currency_code
        }
        
        if max_price is not None:
            params["maxPrice"] = max_price
            logger.info(f"Maximum price: {max_price} {currency_code}")
            
        if departure_date:
            params["departureDate"] = departure_date
            logger.info(f"Departure date: {departure_date}")
            
        if return_date:
            params["returnDate"] = return_date
            logger.info(f"Return date: {return_date}")
            
        if duration:
            params["duration"] = duration
            logger.info(f"Trip duration: {duration} days")
        
        try:
            response = requests.get(endpoint, headers=self._get_headers(), params=params)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Found {len(result.get('data', []))} flight destinations")
            return result
        except Exception as e:
            logger.error(f"Flight inspiration search failed: {str(e)}")
            raise 