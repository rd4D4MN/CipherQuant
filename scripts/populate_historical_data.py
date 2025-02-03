import os
import psycopg2
import pandas as pd
import yfinance as yf
import logging
import time
from dotenv import load_dotenv
from datetime import datetime
from pandas.tseries.offsets import BDay  # Business day offset
import sys
import io

# Force UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set up logging
logging.basicConfig(
    filename="logs/update_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def log(message):
    """Log messages to both console and file."""
    print(message)
    logging.info(message)


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

# Define stock symbols to track
stocks = ["AAPL", "GOOGL", "MSFT"]

# Get all latest dates in one query (optimization)
cur.execute("SELECT symbol, MAX(price_date) FROM prices GROUP BY symbol;")
last_dates = dict(cur.fetchall())  # Stores latest price_date for each stock

# Determine today's date (handling market open cases)
today = datetime.today() #NL time

if today.hour < 22:  # If it's before market close in New York (22.00 NL time), use the last business day
    today = today - BDay(1)
today = today.date()  # Convert to date only

def validate_price_data(row, df, symbol, today):
    """Validate a single row of price data with yfinance format"""
    try:
        date = row.Index.date()
        if date > today:
            return False, "Future date"
        
        # Extract raw numeric values from the DataFrame
        values = {
            'Open': float(df.loc[row.Index, 'Open']),
            'High': float(df.loc[row.Index, 'High']),
            'Low': float(df.loc[row.Index, 'Low']),
            'Close': float(df.loc[row.Index, 'Close']),
            'Volume': float(df.loc[row.Index, 'Volume'])
        }
        
        # Debug log the actual numeric values
        log(f"Debug - Row data for {symbol} on {date}:")
        for field, value in values.items():
            log(f"  {field}: {value}")
        
        # Validate price values
        for field, value in values.items():
            if field != 'Volume':
                if not isinstance(value, (int, float)) or pd.isna(value) or value <= 0:
                    return False, f"Invalid {field} price: {value}"
            else:
                if not isinstance(value, (int, float)) or pd.isna(value) or value < 0:
                    return False, f"Invalid volume: {value}"
        
        return True, values
        
    except Exception as e:
        log(f"Debug - Validation error details: {str(e)}")
        return False, f"Validation error: {str(e)}"

for symbol in stocks:
    last_date = last_dates.get(symbol, None)

    # Determine start date for fetching new data
    if last_date is None:
        log(f"⚠️ No data found for {symbol}, fetching full history...")
        start_date = "1980-01-01"
    else:
        # Ensure last_date is a datetime.date object
        if isinstance(last_date, datetime):
            last_date = last_date.date()
        else:
            last_date = pd.to_datetime(last_date).date()

        # Ensure start_date is a business day (skip weekends & holidays)
        start_date = (pd.to_datetime(last_date) + BDay(1)).date()

        # Skip API call if data is already up to date
        if start_date >= today:
            log(f"✅ {symbol} is already up to date. Skipping...")
            continue

    log(f"📊 Fetching {symbol} from {start_date} to {today}...")

    # Fetch stock data with retry mechanism to handle API failures
    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        try:
            df = yf.download(symbol, start=start_date, end=today)
            
            # Ensure DataFrame has numeric types
            df = df.astype({
                'Open': float,
                'High': float,
                'Low': float,
                'Close': float,
                'Volume': float
            })
            
            # Debug log the DataFrame info
            log(f"\nDebug - DataFrame info for {symbol}:")
            log(f"Columns: {df.columns.tolist()}")
            log(f"Shape: {df.shape}")
            log(f"Types:\n{df.dtypes}")
            
            break  # Success, exit retry loop
        except Exception as e:
            log(f"⚠️ Attempt {attempt+1} failed for {symbol}: {e}")
            time.sleep(5)  # Wait 5 seconds before retrying
    else:
        log(f"❌ Failed to fetch {symbol} after {MAX_RETRIES} attempts. Skipping...")
        continue

    if df.empty:
        log(f"⚠️ No new data for {symbol}. Skipping...")
        continue

    # Insert new data into database
    for row in df.itertuples():
        try:
            is_valid, data = validate_price_data(row, df, symbol, today)
            if not is_valid:
                if isinstance(data, str):
                    log(f"⚠️ Skipping invalid data for {symbol} on {row.Index.date()}: {data}")
                continue

            cur.execute("""
                INSERT INTO prices (symbol, price_date, open_price, high_price, low_price, close_price, volume, market_source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'stock')
                ON CONFLICT (symbol, price_date) DO NOTHING
            """, (
                symbol,
                row.Index.date(),
                data['Open'],
                data['High'],
                data['Low'],
                data['Close'],
                int(data['Volume'])
            ))
            conn.commit()  # Commit each successful insert
            
        except Exception as e:
            log(f"⚠️ Error inserting {symbol} on {row.Index.date()}: {e}")
            conn.rollback()
            continue

cur.close()
conn.close()
log("\n✅ Data updated successfully.")
