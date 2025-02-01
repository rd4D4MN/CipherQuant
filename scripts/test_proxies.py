import requests
import yaml
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
import time

def load_config() -> Dict:
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

def test_proxy(proxy: str) -> Dict:
    start_time = time.time()
    try:
        response = requests.get(
            'https://api.ipify.org?format=json',
            proxies={'http': proxy, 'https': proxy},
            timeout=10
        )
        ip = response.json()['ip']
        latency = time.time() - start_time
        return {
            'proxy': proxy,
            'status': 'success',
            'ip': ip,
            'latency': round(latency, 2)
        }
    except Exception as e:
        return {
            'proxy': proxy,
            'status': 'failed',
            'error': str(e),
            'latency': None
        }

def main():
    config = load_config()
    proxies = config['scraping']['proxy_list']
    
    print(f"Testing {len(proxies)} proxies...")
    results = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_proxy = {
            executor.submit(test_proxy, proxy): proxy 
            for proxy in proxies
        }
        
        for future in as_completed(future_to_proxy):
            result = future.result()
            results.append(result)
            if result['status'] == 'success':
                print(f"✓ {result['proxy']}: {result['ip']} ({result['latency']}s)")
            else:
                print(f"✗ {result['proxy']}: {result['error']}")
    
    working_proxies = [r for r in results if r['status'] == 'success']
    print(f"\nSummary: {len(working_proxies)}/{len(proxies)} proxies working")

if __name__ == "__main__":
    main()
