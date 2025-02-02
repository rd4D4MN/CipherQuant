package main

import (
	"database/sql"
	"fmt"
	"log"
	"os"

	// PostgreSQL driver
	"github.com/joho/godotenv"
	"github.com/piquette/finance-go/crypto"
	"github.com/piquette/finance-go/quote"
)

func main() {
	// Load environment variables from .env
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}

	// Get database credentials from environment variables
	dbHost := os.Getenv("DB_HOST")
	dbPort := os.Getenv("DB_PORT")
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")

	// Connect to PostgreSQL
	dbInfo := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)
	db, err := sql.Open("postgres", dbInfo)
	if err != nil {
		log.Fatal("Error connecting to database:", err)
	}
	defer db.Close()

	// Fetch stock data
	stocks := []string{"AAPL", "GOOGL", "MSFT"}
	fmt.Println("Fetching stock prices...")
	for _, symbol := range stocks {
		q, err := quote.Get(symbol)
		if err != nil {
			log.Printf("Warning: Unable to fetch %s data: %v", symbol, err)
			continue
		}
		saveToDatabase(db, symbol, q.RegularMarketPrice, "stock")
	}

	// Fetch crypto data
	cryptos := []string{"BTC-USD", "ETH-USD"}
	fmt.Println("Fetching crypto prices...")
	for _, symbol := range cryptos {
		q, err := crypto.Get(symbol)
		if err != nil {
			log.Printf("Warning: Unable to fetch %s data: %v", symbol, err)
			continue
		}
		saveToDatabase(db, symbol, q.RegularMarketPrice, "crypto")
	}
}

// Function to insert data into the database
func saveToDatabase(db *sql.DB, symbol string, price float64, marketType string) {
	query := `
        INSERT INTO prices (symbol, price_date, close_price, market_source)
        VALUES ($1, CURRENT_DATE, $2, $3)
        ON CONFLICT (symbol, price_date) DO UPDATE
        SET close_price = EXCLUDED.close_price;
    `
	_, err := db.Exec(query, symbol, price, marketType)
	if err != nil {
		log.Printf("Error inserting data for %s: %v", symbol, err)
	} else {
		fmt.Printf("Stored %s price: $%.2f\n", symbol, price)
	}
}
