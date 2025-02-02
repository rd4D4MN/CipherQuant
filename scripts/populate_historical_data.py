import os
import yfinance as yf
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

# Load .env variables
load_dotenv()

# Database credentials
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
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
    stock_info = yf.Ticker(symbol).history(period="max")
    if stock_info.empty:
        print(f"⚠️ No data for {symbol}")
        continue

    first_date = stock_info.index[0].date()
    today = datetime.today().date()

    print(f"📊 Fetching {symbol} from {first_date} to {today}...")

    df = yf.download(symbol, start=first_date, end=today)

    # 🔍 Debug: Print first few rows before cleaning
    print(f"\n🔍 First few rows of {symbol} data before cleaning:\n", df.head())

    # **Fix Multi-Index Issue Properly**
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(0)  # Drops the "Ticker" level

    # **Ensure the first row is not being used as a header**
    if df.columns[0] in stocks:  # If column names are tickers, something is wrong
        df.reset_index(inplace=True)  # Ensure Date is a proper column
        df.columns = ["date", "open", "high", "low", "close", "volume"]  # Assign correct column names

    # **Ensure proper column renaming**
    df = df.rename(columns=lambda x: x.strip().replace(" ", "_").lower())

    # 🔍 Debug: Print renamed DataFrame columns
    print(f"\n🔍 Final Renamed Columns for {symbol}:", df.columns.tolist())

    for row in df.itertuples(index=True, name="StockData"):
        try:
            cur.execute("""
                INSERT INTO prices (symbol, price_date, open_price, high_price, low_price, close_price, volume, market_source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'stock')
                ON CONFLICT (symbol, price_date) DO NOTHING
            """, (
                symbol,
                row.date if hasattr(row, "date") else row.Index.date(),  # Ensure correct date column
                getattr(row, "open", None) if not pd.isna(getattr(row, "open", None)) else None,
                getattr(row, "high", None) if not pd.isna(getattr(row, "high", None)) else None,
                getattr(row, "low", None) if not pd.isna(getattr(row, "low", None)) else None,
                getattr(row, "close", None) if not pd.isna(getattr(row, "close", None)) else None,
                int(getattr(row, "volume", 0)) if not pd.isna(getattr(row, "volume", 0)) else None
            ))
        except Exception as e:
            print(f"⚠️ Error inserting {symbol} on {row.Index.date()}: {e}")
            conn.rollback()

    conn.commit()

cur.close()
conn.close()
print("\n✅ Data inserted successfully.")
