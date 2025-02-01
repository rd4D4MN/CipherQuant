# Web Scraping in CipherQuant

This document explains how CipherQuant handles data scraping for crypto (and potentially other assets).

## Overview

- **Primary Languages**: Go for the main scraper (`coingecko_scraper.go`) and Python for additional scraping or API calls.
- **Reasons to Scrape**:
  - Obtain fields or metrics not exposed by standard APIs.
  - Validate or cross-check data from official endpoints.

## How It Works

1. **Configuration**  
   - Set up your scraping targets in `config.yaml`, including any rate limits or endpoints.
2. **Execution**  
   - Run `go run coingecko_scraper.go` (example) to parse target pages and fetch data.
   - Data is transformed (if needed) and stored in the PostgreSQL database.
3. **Error Handling**  
   - Implement retries if a connection fails or the site is temporarily down.
   - Log scraping results and failures for debugging.

## Best Practices & Tips

- **Respect Rate Limits**: Even if a site doesn’t publicly post them, be mindful to avoid hammering the server.
- **HTML Changes**: If the site layout changes, update your selectors or parsing logic.
- **Security & Legal**: Always check the site’s Terms of Service before scraping.

