import os
import psycopg2
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Database credentials
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cur = conn.cursor()

stocks = ["AAPL", "GOOGL", "MSFT"]

for symbol in stocks:
    # 🔍 Step 1: Get the latest date available in the database
    cur.execute("SELECT MAX(price_date) FROM prices WHERE symbol = %s;", (symbol,))
    last_date = cur.fetchone()[0]

    if last_date is None:
        print(f"⚠️ No data found for {symbol}, fetching full history...")
        start_date = "1980-01-01"  # Fetch all data for first-time setup
    else:
        start_date = last_date + timedelta(days=1)  # Fetch from the next missing date

    today = datetime.today().date()
    print(f"📊 Fetching {symbol} from {start_date} to {today}...")

    # 🔍 Step 2: Fetch only missing data
    df = yf.download(symbol, start=start_date, end=today)

    if df.empty:
        print(f"⚠️ No new data for {symbol}. Skipping...")
        continue

    df = df.rename(columns=lambda x: x.strip().replace(" ", "_").lower())

    for row in df.itertuples(index=True, name="StockData"):
        try:
            cur.execute("""
                INSERT INTO prices (symbol, price_date, open_price, high_price, low_price, close_price, volume, market_source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'stock')
                ON CONFLICT (symbol, price_date) DO NOTHING
            """, (
                symbol,
                row.Index.date(),
                getattr(row, "open", None),
                getattr(row, "high", None),
                getattr(row, "low", None),
                getattr(row, "close", None),
                int(getattr(row, "volume", 0))
            ))
        except Exception as e:
            print(f"⚠️ Error inserting {symbol} on {row.Index.date()}: {e}")
            conn.rollback()

    conn.commit()

cur.close()
conn.close()
print("\n✅ Data updated successfully.")
