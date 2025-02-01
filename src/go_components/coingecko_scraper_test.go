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
