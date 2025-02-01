import unittest
import requests
from datetime import datetime, timedelta
from scripts.scraper import WebScraper, OHLCVData
from config.config_handler import ConfigHandler

class TestWebScraper(unittest.TestCase):
    def setUp(self):
        config_handler = ConfigHandler()
        self.scraper = WebScraper(config_handler)

    def test_user_agent_randomization(self):
        user_agent1 = self.scraper.user_agent.random
        user_agent2 = self.scraper.user_agent.random
        self.assertNotEqual(user_agent1, user_agent2, "User-Agent should be randomized")

    def test_scrape_coingecko(self):
        # Mock the _parse_coingecko_response method to return known data
        self.scraper._parse_coingecko_response = lambda x: [
            {
                "timestamp": 1617184800,
                "open": 50000.0,
                "high": 51000.0,
                "low": 49000.0,
                "close": 50500.0,
                "volume": 1000.0,
            }
        ]
        data = self.scraper.scrape_coingecko("coins/bitcoin/market_chart?vs_currency=usd&days=1")
        self.assertIsInstance(data, list)
        self.assertIsInstance(data[0], OHLCVData)

    def test_data_validation(self):
        raw_data = [
            {
                "timestamp": 1617184800,
                "open": 50000.0,
                "high": 51000.0,
                "low": 49000.0,
                "close": 50500.0,
                "volume": 1000.0,
            },
            {
                "timestamp": "invalid_timestamp",
                "open": 50000.0,
                "high": 51000.0,
                "low": 49000.0,
                "close": 50500.0,
                "volume": 1000.0,
            },
        ]
        validated_data = self.scraper.parse_and_validate(raw_data)
        self.assertEqual(len(validated_data), 1, "One entry should be valid")

    def test_parse_coingecko_response(self):
        # Setup mock data in new CoinGecko format
        mock_data = {
            'prices': [[1617184800000, 50000.0]],
            'market_caps': [[1617184800000, 1000000000.0]],
            'total_volumes': [[1617184800000, 1000.0]]
        }
        
        # Call parse method
        result = self.scraper._parse_coingecko_response(mock_data)
        
        # Verify structure and values
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], dict)
        self.assertEqual(result[0]["timestamp"], 1617184800000)
        self.assertEqual(result[0]["close"], 50000.0)
        self.assertEqual(result[0]["volume"], 1000.0)

    def test_config_integration(self):
        # Verify config values are properly loaded
        self.assertEqual(self.scraper.config.base_url, "https://api.coingecko.com/api/v3")
        self.assertEqual(self.scraper.config.max_retries, 3)
        self.assertIsInstance(self.scraper.config.user_agents, list)

    def test_live_coingecko_api(self):
        try:
            endpoint = "coins/bitcoin/market_chart"
            params = {
                "vs_currency": "usd",
                "days": "1"
            }
            
            # Add request logging
            print("\nMaking live API call to CoinGecko...")
            print(f"URL: {self.scraper.config.base_url}/{endpoint}")
            print(f"Params: {params}")
            
            # Track API call start time
            start_time = datetime.now()
            
            data = self.scraper.scrape_coingecko(endpoint, params)
            
            # Verify API call duration
            api_duration = (datetime.now() - start_time).total_seconds()
            print(f"\nAPI call duration: {api_duration:.2f} seconds")
            
            # Ensure we got fresh data
            self.assertGreater(api_duration, 0.1, "API call was too fast, might be cached or mocked")
            
            # Basic validation
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0, "API returned empty data")
            
            if len(data) > 0:
                first_entry = data[0]
                latest_entry = data[-1]
                
                # Stricter timestamp validation
                current_time = datetime.now()
                first_time = datetime.fromtimestamp(first_entry.timestamp/1000)
                latest_time = datetime.fromtimestamp(latest_entry.timestamp/1000)
                
                # Ensure timestamps are within last 24 hours
                self.assertLess(
                    (current_time - first_time).total_seconds(), 
                    86400,  # 24 hours in seconds
                    "First entry timestamp too old"
                )
                self.assertLess(
                    (current_time - latest_time).total_seconds(),
                    3600,  # 1 hour in seconds
                    "Latest entry timestamp too old"
                )
                
                # Print validation info
                print(f"\nTimestamp validation:")
                print(f"Current time: {current_time}")
                print(f"Data time range: {first_time} to {latest_time}")
                
                # Value range validation
                self.assertGreater(first_entry.close, 0, "Price should be positive")
                self.assertGreater(first_entry.volume, 0, "Volume should be positive")
                
                # Print first entry for manual inspection
                print(f"\nFirst entry data:")
                print(f"Timestamp: {datetime.fromtimestamp(first_entry.timestamp/1000)}")
                print(f"Close: ${first_entry.close:,.2f}")
                print(f"Volume: ${first_entry.volume:,.2f}")
                
                # Data consistency checks
                for entry in data[:5]:  # Check first 5 entries
                    self.assertEqual(entry.open, entry.close, "Open should equal close for point data")
                    self.assertEqual(entry.high, entry.close, "High should equal close for point data")
                    self.assertEqual(entry.low, entry.close, "Low should equal close for point data")
                
                # Timestamp validation
                current_time = datetime.now().timestamp() * 1000
                max_age = (current_time - timedelta(days=7).total_seconds() * 1000)
                self.assertGreater(first_entry.timestamp, max_age)
                
                # Print more detailed data summary
                print(f"\nReceived {len(data)} data points")
                if len(data) > 0:
                    latest_entry = data[-1]
                    print(f"Latest entry timestamp: {datetime.fromtimestamp(latest_entry.timestamp/1000)}")
                    print(f"Latest price: ${latest_entry.close:,.2f}")
                
        except requests.exceptions.RequestException as e:
            self.fail(f"API request failed: {str(e)}")
        except Exception as e:
            self.fail(f"Test failed: {str(e)}")

if __name__ == "__main__":
    unittest.main()
