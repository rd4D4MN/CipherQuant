package go_components

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

type Ticker struct {
	Symbol       string  `json:"symbol"`
	CurrentPrice float64 `json:"current_price"`
}

// ScrapeCoinGecko fetches the current USD price for specified coins
func ScrapeCoinGecko(coins []string) ([]Ticker, error) {
	// Construct the query for multiple coins
	// e.g., "bitcoin,ethereum,dogecoin"
	coinList := ""
	for i, c := range coins {
		coinList += c
		if i < len(coins)-1 {
			coinList += ","
		}
	}

	// Build the request URL. The "simple/price" endpoint
	// returns a JSON map of { "coin": { "usd": <price> }, ... }
	url := fmt.Sprintf(
		"https://api.coingecko.com/api/v3/simple/price?ids=%s&vs_currencies=usd",
		coinList,
	)

	resp, err := http.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to GET: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("received non-OK status: %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	// The API returns a structure like:
	// {
	//   "bitcoin": {"usd": 23456.78},
	//   "ethereum": {"usd": 1234.56}
	// }
	// We'll unmarshal into a dynamic map.
	var data map[string]map[string]float64
	if err := json.Unmarshal(body, &data); err != nil {
		return nil, fmt.Errorf("failed to parse JSON: %w", err)
	}

	// Convert the map into a slice of Ticker
	var results []Ticker
	for symbol, pricing := range data {
		usdPrice, ok := pricing["usd"]
		if ok {
			results = append(results, Ticker{Symbol: symbol, CurrentPrice: usdPrice})
		}
	}
	return results, nil
}
