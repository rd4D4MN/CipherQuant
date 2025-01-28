import requests
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from pydantic import BaseModel, ValidationError
from typing import List, Dict, Any

class OHLCVData(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class WebScraper:
    def __init__(self, config_handler):
        self.config = config_handler.config.scraping['coingecko']
        self.session = requests.Session()
        retries = Retry(total=self.config.max_retries)
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.user_agent = UserAgent()

    def scrape(self, url: str, params: dict = None) -> Any:
        """
        Make HTTP GET request with retry logic
        """
        headers = {"User-Agent": self.user_agent.random}
        response = self.session.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def parse_and_validate(self, raw_data: List[Dict[str, Any]]) -> List[OHLCVData]:
        validated_data = []
        for item in raw_data:
            try:
                validated_data.append(OHLCVData(**item))
            except ValidationError as e:
                print(f"Data validation error: {e}")
        return validated_data

    def scrape_coingecko(self, endpoint: str, params: dict = None) -> List[OHLCVData]:
        """
        Scrape data from CoinGecko API
        Args:
            endpoint: API endpoint
            params: Optional query parameters
        Returns:
            List of OHLCV data
        """
        url = f"{self.config.base_url}/{endpoint}"
        raw_data = self.scrape(url, params)
        parsed_data = self._parse_coingecko_response(raw_data)
        return self.parse_and_validate(parsed_data)

    def scrape_binance(self, endpoint: str, params: Dict[str, Any]) -> List[OHLCVData]:
        url = f"https://api.binance.com/api/v3/{endpoint}"
        raw_data = self.scrape(url, params=params)
        parsed_data = self._parse_binance_response(raw_data)
        return self.parse_and_validate(parsed_data)

    def _parse_coingecko_response(self, data: Dict[str, List[List[float]]]) -> List[Dict[str, Any]]:
        """Parse CoinGecko market chart response into format compatible with OHLCVData model"""
        parsed_data = []
        
        if not isinstance(data, dict) or 'prices' not in data:
            return parsed_data
            
        prices = data['prices']
        volumes = data.get('total_volumes', [])
        
        # Create a volume lookup dictionary
        volume_dict = {int(ts): vol for ts, vol in volumes}
        
        for price_data in prices:
            timestamp = int(price_data[0])  # Timestamp in milliseconds
            close_price = float(price_data[1])
            
            parsed_item = {
                "timestamp": timestamp,
                "open": close_price,  # Use close as open since we only have price points
                "high": close_price,
                "low": close_price,
                "close": close_price,
                "volume": volume_dict.get(timestamp, 0.0)
            }
            parsed_data.append(parsed_item)
        
        return parsed_data

    def _parse_binance_response(self, data: Any) -> List[Dict[str, Any]]:
        # Implement parsing logic specific to Binance's API response
        pass
