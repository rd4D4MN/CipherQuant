package go_components

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type YahooQuote struct {
	Symbol     string  `json:"symbol"`
	ShortName  string  `json:"shortName"`
	Price      float64 `json:"regularMarketPrice"`
	Volume     int64   `json:"regularMarketVolume"`
	TimeStamp  int64   `json:"regularMarketTime"`
	ChangePerc float64 `json:"regularMarketChangePercent"`
}

func ScrapeYahooFinance(symbols []string) ([]YahooQuote, error) {
	client := &http.Client{
		Timeout: time.Second * 10,
	}

	var results []YahooQuote
	for _, symbol := range symbols {
		url := fmt.Sprintf(
			"https://query1.finance.yahoo.com/v8/finance/chart/%s",
			symbol,
		)

		req, err := http.NewRequest("GET", url, nil)
		if err != nil {
			return nil, fmt.Errorf("failed to create request: %w", err)
		}

		// Add headers to mimic browser
		req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
		req.Header.Set("Accept", "application/json")

		resp, err := client.Do(req)
		if err != nil {
			return nil, fmt.Errorf("failed to GET: %w", err)
		}
		defer resp.Body.Close()

		body, err := io.ReadAll(resp.Body)
		if err != nil {
			return nil, fmt.Errorf("failed to read response: %w", err)
		}

		var quote YahooQuote
		if err := json.Unmarshal(body, &quote); err != nil {
			return nil, fmt.Errorf("failed to parse JSON: %w", err)
		}

		results = append(results, quote)
		// Respect rate limits
		time.Sleep(time.Second)
	}

	return results, nil
}
