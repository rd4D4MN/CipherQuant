# Scraping with Go

This document outlines how to use the Go-based scraper in the CipherQuant repository. It fetches live crypto prices from CoinGecko’s public API.

## 1. Overview

**Purpose:** Collect real-time crypto price data for further analytics, ML modeling, or fintech dashboards.  
**Language:** Go (with HTTP requests to the CoinGecko API).  
**Why Go?** Demonstrates concurrency/performance benefits and showcases multi-language proficiency alongside Python scripts.

## 2. Installation & Setup

Ensure Go is installed (1.18+ recommended):  
[Official Go Installation Guide](https://go.dev/doc/install)

### Clone the Repository (if you haven’t already):

```bash
git clone https://github.com/rd4D4MN/CipherQuant.git
cd CipherQuant
```

### Initialize or Update Go Modules:

```bash
go mod tidy
```

This will download and tidy up any dependencies, ensuring you have everything needed.

## 3. Usage & Examples

### 3.1 Running the Scraper

The main Go entry point is in `cmd/cipherquant/main.go`. To run it:

```bash
go run ./cmd/cipherquant
```

#### Default Behavior

Scrapes the current prices for Bitcoin and Ethereum in USD.  
Prints output to the console, for example:

```yaml
Scrape successful! Retrieved the following prices:
- bitcoin: $XYZ
- ethereum: $ABC
```

### 3.2 Changing the Coins

If you want to modify which coins are scraped, open `cmd/cipherquant/main.go` and adjust the `coins` slice:

```go
coins := []string{"bitcoin", "ethereum", "dogecoin"}
```

Re-run:

```bash
go run ./cmd/cipherquant
```

Now you’ll see Dogecoin in the results as well.

### 3.3 (Optional) Parsing Flags

If you decide to parse command-line flags, your code might look like:

```go
// Example snippet in main.go
coinsFlag := flag.String("coins", "bitcoin,ethereum", "Comma-separated list of coin IDs (e.g. bitcoin,ethereum,dogecoin)")
flag.Parse()

coins := strings.Split(*coinsFlag, ",")
tickers, err := go_components.ScrapeCoinGecko(coins)
...
```

Then run:

```bash
go run ./cmd/cipherquant --coins="bitcoin,ethereum,dogecoin"
```

## 4. Fintech Relevance

### Price Correlation & Risk

In fintech or private equity contexts, real-time crypto prices can be correlated with traditional equity indices or used to assess market volatility.

### Data Pipeline Inputs

This scraper can feed the collected data into a SQL database for historical tracking, AI/ML modeling (like LSTM or Prophet), or interactive dashboards.

### Private Equity/VC Insights

Compare crypto returns with investment data from private equity or venture capital deals, bridging the gap between emerging digital assets and traditional finance metrics.

## 5. Testing the Scraper

A basic test is included in `go_components/coingecko_scraper_test.go`. To run it:

```bash
go test ./go_components/...
```

### Example Test Logic

```go
package go_components

import (
    "testing"
)

func TestScrapeCoinGecko(t *testing.T) {
    coins := []string{"bitcoin"}
    tickers, err := ScrapeCoinGecko(coins)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if len(tickers) == 0 {
        t.Error("expected at least one ticker")
    }
}
```

#### What It Checks

- Ensures the function doesn’t return an error for a valid coin.
- Expects at least one ticker in the response.

## 6. Common Pitfalls

### Invalid Coins

If you pass a coin name that doesn’t exist in CoinGecko’s database, the scraper might return an empty price or partial data.

### Rate Limits

CoinGecko has generous free API limits, but if you scale to many requests, consider introducing delays or caching.

### Network Errors

Handle temporary network failures gracefully, e.g., by retrying or logging the error for debugging.

## 7. Next Steps

### Store Data in a Database

Use our future SQL schema to archive historical prices.

### Integrate with Frontend

Display live or historical prices on the React dashboard.

### Expand to Additional Endpoints

CoinGecko provides more data (market cap, 24h volume, etc.). See [CoinGecko API docs](https://www.coingecko.com/en/api) for details.

## 8. Questions or Contributions

For feature requests, bug reports, or contributions:

- **Open an Issue** in [GitHub Issues](https://github.com/rd4D4MN/CipherQuant/issues).
- **Submit a Pull Request** if you have code improvements or want to add new features (like additional scraping endpoints).
