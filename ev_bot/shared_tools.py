from typing import Dict, Any, Optional
from ev_bot.logger import setup_logger
import requests

logger = setup_logger("tool")
def get_wikipedia_image(destination: str) -> Optional[str]:
    """
    Retrieves a thumbnail image URL for a travel destination from Wikipedia.

    Args:
        destination (str): Name of the city or point of interest.

    Returns:
        str | None: Image URL if found, otherwise None.
    """
    api_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": destination,
        "prop": "pageimages",
        "pithumbsize": 600
    }
    logger.info(f"Fetching Wikipedia image for: {destination}")
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", {})
        for page in pages.values():
            if "thumbnail" in page:
                logger.info(f"Found image URL: {page['thumbnail']['source']}")
                return page["thumbnail"]["source"]
    except requests.RequestException as e:
        logger.error(f"Wikipedia image search failed: {e}")
    logger.info(f"Image not found for destination: {destination}")
    return None