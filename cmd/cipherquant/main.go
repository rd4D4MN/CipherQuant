package main

import (
	"fmt"
	"log"
	"os"

	"github.com/rd4D4MN/CipherQuant/go_components"
	// ^ This import path assumes you ran `go mod init github.com/rd4D4MN/CipherQuant`
	//   in your project root. Adjust if your module name is different.
)

func main() {
	coins := []string{"bitcoin", "ethereum"}
	tickers, err := go_components.ScrapeCoinGecko(coins)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("Scrape successful! Retrieved the following prices:")
	for _, t := range tickers {
		fmt.Printf("- %s: $%.2f\n", t.Symbol, t.CurrentPrice)
	}

	os.Exit(0)
}
