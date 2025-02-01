package main

import (
	"fmt"
	"log"

	"github.com/piquette/finance-go/crypto"
	"github.com/piquette/finance-go/quote"
)

func main() {
	// Stock symbols to fetch
	stocks := []string{"AAPL", "GOOGL", "MSFT"}
	fmt.Println("Fetching stock prices...")
	for _, symbol := range stocks {
		q, err := quote.Get(symbol)
		if err != nil {
			log.Fatalf("Error fetching stock data for %s: %v", symbol, err)
		}
		fmt.Printf("Stock: %s | Price: $%.2f\n", q.ShortName, q.RegularMarketPrice)
	}

	// Crypto symbols to fetch
	cryptos := []string{"BTC-USD", "ETH-USD"}
	fmt.Println("Fetching crypto prices...")
	for _, symbol := range cryptos {
		q, err := crypto.Get(symbol)
		if err != nil {
			log.Fatalf("Error fetching crypto data for %s: %v", symbol, err)
		}
		fmt.Printf("Crypto: %s | Price: $%.2f\n", q.ShortName, q.RegularMarketPrice)
	}
}
