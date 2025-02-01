from config.config_handler import ConfigHandler
from scripts.scraper import WebScraper, CrunchbaseScraper
from ..src.go_components import ScrapeYahooFinance
import time
from typing import Dict, Any
import sys

def test_coingecko(scraper: WebScraper) -> Dict[str, Any]:
    try:
        data = scraper.scrape_coingecko(
            "coins/bitcoin/market_chart",
            params={"vs_currency": "usd", "days": "1"}
        )
        return {
            "status": "success",
            "data_points": len(data),
            "sample": data[0] if data else None
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def test_crunchbase(scraper: CrunchbaseScraper) -> Dict[str, Any]:
    try:
        data = scraper.scrape("coinbase")
        return {
            "status": "success",
            "data_sample": {k: v for k, v in list(data.items())[:5]}
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def test_yahoo_finance() -> Dict[str, Any]:
    try:
        data = ScrapeYahooFinance(["AAPL", "GOOGL"])
        return {
            "status": "success",
            "symbols_fetched": len(data)
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}

def main():
    config_handler = ConfigHandler()
    
    # Test each scraper
    scrapers = {
        "CoinGecko": lambda: test_coingecko(WebScraper(config_handler)),
        "Crunchbase": lambda: test_crunchbase(CrunchbaseScraper(config_handler)),
        "Yahoo Finance": test_yahoo_finance
    }
    
    results = {}
    for name, test_func in scrapers.items():
        print(f"\nTesting {name} scraper...")
        start_time = time.time()
        try:
            result = test_func()
            duration = time.time() - start_time
            result["duration"] = f"{duration:.2f}s"
            results[name] = result
            
            if result["status"] == "success":
                print(f"✓ Success ({duration:.2f}s)")
            else:
                print(f"✗ Failed: {result['error']}")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            results[name] = {"status": "error", "error": str(e)}
    
    # Print summary
    print("\nTest Summary:")
    for name, result in results.items():
        status = "✓" if result["status"] == "success" else "✗"
        print(f"{status} {name}: {result['status']} ({result.get('duration', 'N/A')})")

if __name__ == "__main__":
    main()
