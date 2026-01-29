"""Price scraper module for fetching market prices."""

def scrape_mangalore_prices():
    """Scrape prices from Mangalore market."""
    return {
        'red_arecanut_price': 150,
        'white_arecanut_price': 160,
        'kokum_price': 120,
        'coconut_price': 25,
        'banana_price': 40,
    }

def get_fallback_prices():
    """Get fallback prices when scraping fails."""
    return {
        'red_arecanut_price': 145,
        'white_arecanut_price': 155,
        'kokum_price': 115,
        'coconut_price': 23,
        'banana_price': 38,
    }
