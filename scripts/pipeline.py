import pandas as pd
from sqlalchemy import create_engine

def process_data():
    engine = create_engine('sqlite:///trading.db')
    # Load, clean, merge data from multiple sources
    df = pd.read_csv('data/raw_prices.csv')
    df.to_sql('processed_data', engine, index=False)