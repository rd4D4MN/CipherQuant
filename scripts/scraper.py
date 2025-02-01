import requests
import random
import yaml
import time
from pathlib import Path
from itertools import cycle
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load config
CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yaml"
with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

class ProxyManager:
    """Manages proxy rotation, failure handling, and testing"""

    def __init__(self, proxy_list, fail_threshold=3):
        self.proxy_list = proxy_list.copy()
        self.failed_proxies = {}
        self.fail_threshold = fail_threshold
        self.proxy_cycle = cycle(self.proxy_list)

    def get_proxy(self):
        """Returns the next available proxy"""
        if not self.proxy_list:
            raise Exception("No working proxies available")
        return next(self.proxy_cycle)

    def mark_failed(self, proxy):
        """Tracks failed proxy and removes it if it exceeds threshold"""
        self.failed_proxies[proxy] = self.failed_proxies.get(proxy, 0) + 1
        if self.failed_proxies[proxy] >= self.fail_threshold:
            self.proxy_list.remove(proxy)
            print(f"❌ Proxy removed: {proxy}")

    def test_proxies(self):
        """Tests proxies and keeps only working ones"""
        def test_proxy(proxy):
            try:
                response = requests.get(
                    "https://api.ipify.org?format=json",
                    proxies={"http": proxy, "https": proxy},
                    timeout=5
                )
                return proxy if response.status_code == 200 else None
            except:
                return None

        print("🔄 Testing proxies...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = {executor.submit(test_proxy, p): p for p in self.proxy_list}
        
        self.proxy_list = [future.result() for future in as_completed(results) if future.result()]
        self.proxy_cycle = cycle(self.proxy_list)  # Update cycle with working proxies
        print(f"✅ {len(self.proxy_list)} working proxies found.")

class WebScraper:
    """Handles scraping with proxy rotation and user-agent spoofing"""

    def __init__(self):
        self.config = config
        self.session = self._create_session()
        self.user_agent = UserAgent()
        self.proxy_manager = ProxyManager(self.config["scraping"]["proxy_list"])
        self.proxy_manager.test_proxies()  # Remove bad proxies before starting

    def _create_session(self):
        """Creates a session with retry logic"""
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def scrape(self, url, params=None):
        """Performs web scraping with proxy rotation"""
        headers = {"User-Agent": self.user_agent.random}
        
        for attempt in range(self.config["scraping"]["coingecko"]["max_retries"]):
            proxy = self.proxy_manager.get_proxy()
            try:
                response = self.session.get(
                    url, headers=headers, params=params, proxies={"http": proxy, "https": proxy}, timeout=10
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                print(f"⚠️ Attempt {attempt + 1} failed with proxy {proxy}: {e}")
                self.proxy_manager.mark_failed(proxy)
                time.sleep(2)  # Wait before retrying

        print("❌ All attempts failed.")
        return None

# Example Usage
if __name__ == "__main__":
    scraper = WebScraper()
    url = f"{config['scraping']['coingecko']['base_url']}/coins/bitcoin/market_chart"
    params = config["scraping"]["coingecko"]["params"]
    data = scraper.scrape(url, params)

    if data:
        print(f"✅ Scraped {len(data)} data points successfully.")
    else:
        print("❌ Scraping failed.")
