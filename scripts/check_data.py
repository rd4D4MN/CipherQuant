import os
import psycopg2
from dotenv import load_dotenv
from tabulate import tabulate
import sys

def check_database():
    load_dotenv()
    
    # Connect to PostgreSQL using environment variables
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    
    cur = conn.cursor()
    
    print("\n1. Data Summary by Symbol:")
    cur.execute("""
        SELECT 
            symbol, 
            COUNT(*) as records,
            MIN(price_date) as earliest,
            MAX(price_date) as latest,
            COUNT(*) FILTER (WHERE close_price IS NULL) as null_prices,
            COUNT(*) FILTER (WHERE volume = 0 OR volume IS NULL) as zero_volume
        FROM prices
        GROUP BY symbol
        ORDER BY symbol;
    """)
    results = cur.fetchall()
    print(tabulate(results, 
                  headers=['Symbol', 'Records', 'Earliest', 'Latest', 'Null Prices', 'Zero Volume'], 
                  tablefmt='psql'))
    
    print("\n2. Recent Data Check (Last 5 days):")
    cur.execute("""
        SELECT 
            symbol, 
            price_date, 
            CASE 
                WHEN close_price IS NULL THEN 'NULL'
                ELSE close_price::text 
            END as close,
            volume
        FROM prices
        WHERE price_date >= CURRENT_DATE - INTERVAL '5 days'
        ORDER BY symbol, price_date DESC;
    """)
    results = cur.fetchall()
    print(tabulate(results, headers=['Symbol', 'Date', 'Close', 'Volume'], tablefmt='psql'))
    
    print("\n3. Data Quality Issues:")
    cur.execute("""
        SELECT symbol, price_date, close_price, volume
        FROM prices
        WHERE close_price IS NULL 
           OR volume = 0 
           OR volume IS NULL
        ORDER BY price_date DESC
        LIMIT 10;
    """)
    results = cur.fetchall()
    print(tabulate(results, 
                  headers=['Symbol', 'Date', 'Close', 'Volume'], 
                  tablefmt='psql'))
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_database()
