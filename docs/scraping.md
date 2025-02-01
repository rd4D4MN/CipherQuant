# Anti-Bot Tactics Documentation

## Overview
This document outlines the strategies we use to avoid being detected as a bot while scraping data.

## Implemented Tactics

### 1. User Agent Rotation
- Using `fake-useragent` library to randomize User-Agent headers
- Mimics real browser behavior
- Regularly updated list of modern browser signatures

### 2. Proxy Rotation
- Rotating pool of proxy servers
- Distributes requests across different IP addresses
- Helps avoid rate limiting and IP blocks

### 3. Request Rate Limiting
- Respects each API's rate limits
- Implements exponential backoff for retries
- Adds random delays between requests

### 4. Request Headers
- Includes common browser headers
- Maintains session cookies
- Sends appropriate Accept headers

### 5. Error Handling
- Graceful handling of 429 (Too Many Requests)
- Automatic retry with backoff
- Session management for persistent connections

## Usage Example

```python
scraper = WebScraper(config_handler)
data = scraper.scrape_coingecko("bitcoin")
```

## Configuration

Configure proxies and rate limits in `config.yaml`:

```yaml
scraping:
  proxy_list:
    - "http://proxy1.example.com:8080"
    - "http://proxy2.example.com:8080"
  rate_limits:
    coingecko: 50
    yahoo_finance: 100
    crunchbase: 50
```
