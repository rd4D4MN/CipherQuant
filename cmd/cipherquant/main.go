package main

import (
	"database/sql"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
	"github.com/piquette/finance-go/quote"
)

// Connect to PostgreSQL
func connectDB() (*sql.DB, error) {
	dbHost := os.Getenv("DB_HOST")
	dbPort := os.Getenv("DB_PORT")
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")

	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)
	return sql.Open("postgres", connStr)
}

// Get the latest date for a given stock from the database
func getLastRecordedDate(symbol string, db *sql.DB) (string, error) {
	var lastDate string
	err := db.QueryRow("SELECT MAX(price_date) FROM prices WHERE symbol = $1", symbol).Scan(&lastDate)
	if err != nil {
		return "", err
	}
	return lastDate, nil
}

// Fetch and insert stock data only if it's missing
func fetchStockData(symbol string, db *sql.DB) {
	q, err := quote.Get(symbol)
	if err != nil {
		log.Println("Error fetching stock data:", err)
		return
	}

	// Get today's date
	today := time.Now().Format("2006-01-02")

	// Check the last recorded date
	lastDate, err := getLastRecordedDate(symbol, db)
	if err != nil {
		log.Println("Error checking last date:", err)
		return
	}

	// Only insert if today's data is not already in the database
	if lastDate < today {
		_, err = db.Exec(
			`INSERT INTO prices (symbol, price_date, open_price, high_price, low_price, close_price, volume, market_source)
			 VALUES ($1, $2, $3, $4, $5, $6, $7, 'stock') 
			 ON CONFLICT (symbol, price_date) DO NOTHING`,
			q.Symbol, today, q.RegularMarketOpen, q.RegularMarketDayHigh, q.RegularMarketDayLow, q.RegularMarketPrice, q.RegularMarketVolume)

		if err != nil {
			log.Println("Error inserting stock data:", err)
		} else {
			log.Println("✅ Data updated successfully for", symbol)
		}
	} else {
		log.Println("⏭ Data for", symbol, "is already up to date.")
	}
}

func main() {
	// Load environment variables
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}

	// Connect to the database
	db, err := connectDB()
	if err != nil {
		log.Fatal("Error connecting to database:", err)
	}
	defer db.Close()

	// List of stocks to update
	stocks := []string{"AAPL", "GOOGL", "MSFT"}

	// Fetch and insert stock prices
	for _, symbol := range stocks {
		fetchStockData(symbol, db)
	}

	log.Println("📊 Fresh data fetching completed.")
}
