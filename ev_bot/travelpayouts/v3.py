import datetime
import travelpayouts.exceptions

API_V3_URL = 'https://api.travelpayouts.com/aviasales/v3'


def prices_for_dates(client,
                     origin=None,
                     destination=None,
                     departure_at=None,
                     return_at=None,
                     currency='usd',
                     direct=False,
                     limit=30,
                     page=1,
                     one_way=True,
                     sorting='price',
                     unique=False,
                     cy=None # Alias for currency if needed, but API docs say 'currency' or 'cy'? Docs said 'cy' in the URL example but usually libraries normalize. Let's check docs again or just support both/map.
                     ):
    """
    Returns the cheapest tickets for specific dates found by Aviasales users in the last 48 hours.
    
    :param origin: IATA code of the departure city.
    :param destination: IATA code of the destination city.
    :param departure_at: Departure date (YYYY-MM or YYYY-MM-DD).
    :param return_at: Return date (YYYY-MM or YYYY-MM-DD).
    :param currency: Currency of prices (usd, eur, rub). Default: usd.
    :param direct: If true, only direct flights.
    :param limit: Number of results per page. Default: 30.
    :param page: Page number. Default: 1.
    :param one_way: If true, one-way flights.
    :param sorting: Sorting by 'price' or 'route'. Default: 'price'.
    :param unique: If true, returns only unique flights.
    """
    params = {
        'currency': currency,
        'direct': str(direct).lower(),
        'limit': limit,
        'page': page,
        'one_way': str(one_way).lower(),
        'sorting': sorting,
        'unique': str(unique).lower()
    }

    if origin:
        params['origin'] = origin
    
    if destination:
        params['destination'] = destination
        
    if departure_at:
        params['departure_at'] = departure_at
        
    if return_at:
        params['return_at'] = return_at

    # The client handles the token in headers usually, but v3 might need it in params?
    # The browser subagent found: ...&token=PutYourTokenHere
    # So we should add the token to params.
    if client.token:
        params['token'] = client.token

    data = client._get(API_V3_URL + "/prices_for_dates", params)

    if 'success' in data and not data['success']:
         raise travelpayouts.exceptions.ApiError(data.get('error', 'Unknown error'))
         
    return data
