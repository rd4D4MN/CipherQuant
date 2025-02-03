from strategies import RSIStrategy, MACDStrategy
from flask import Flask, jsonify, abort
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configure PostgreSQL connection
DB_URI = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URI)

def fetch_data(symbol, days=365):
    """Fetch historical data from PostgreSQL"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = """
        SELECT 
            price_date,
            open_price as open,
            high_price as high,
            low_price as low,
            close_price as close,
            volume
        FROM prices 
        WHERE symbol = :symbol 
        AND price_date BETWEEN :start_date AND :end_date
        ORDER BY price_date
        """
        
        df = pd.read_sql_query(
            text(query),
            engine,
            params={
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date
            },
            index_col='price_date'
        )
        
        if df.empty:
            raise ValueError(f"No data available for {symbol}")
            
        # Validate minimum required data points
        if len(df) < 30:  # Need at least 30 days for reliable analysis
            raise ValueError(f"Insufficient data points for {symbol} (minimum 30 required)")
            
        # Standardize column names
        df.columns = [col.capitalize() for col in df.columns]
        
        # Pre-process price data - prices should never be null
        required_cols = ['Close', 'Open', 'High', 'Low']
        for col in required_cols:
            if df[col].isna().sum() > 0:
                logger.warning(f"Filling missing {col} prices for {symbol}")
                df[col] = df[col].fillna(method='ffill').fillna(method='bfill')
        
        # Volume can have some missing values, fill with 0
        df['Volume'] = df['Volume'].fillna(0)
        
        # Calculate daily returns after ensuring no missing prices
        df['Daily_Return'] = df['Close'].pct_change()
        
        # Remove first row which will have NaN return
        df = df.iloc[1:]
        
        # Validate final dataset
        if df.empty:
            raise ValueError(f"Insufficient data for {symbol} after preprocessing")
            
        logger.info(f"Fetched data for {symbol}: {df.shape[0]} rows")
        logger.debug(f"Missing values summary:\n{df.isna().sum()}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        raise

class Trade:
    def __init__(self, symbol, strategy, return_value):
        self.symbol = symbol
        self.strategy = strategy
        self.return_value = return_value
        
    def save(self):
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO trades (symbol, strategy, return_value, created_at)
                    VALUES (:symbol, :strategy, :return_value, NOW())
                """), {
                    'symbol': self.symbol,
                    'strategy': self.strategy,
                    'return_value': self.return_value
                })
                conn.commit()
                logger.info(f"Saved trade: {self.symbol} {self.strategy} {self.return_value}")
        except Exception as e:
            logger.error(f"Error saving trade: {str(e)}")
            raise

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.route('/backtest/<strategy>/<symbol>')
def backtest(strategy, symbol):
    try:
        # Validate strategy
        if strategy not in ['RSI', 'MACD']:
            abort(404, description="Strategy not supported")
        
        # Fetch data
        data = fetch_data(symbol)
        
        # Validate data
        if data.empty:
            return jsonify({"error": "Insufficient data for analysis"}), 400
            
        # Check for required columns and handle missing values
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Daily_Return']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            return jsonify({"error": f"Missing columns: {missing_columns}"}), 400
            
        # Handle missing values using newer pandas methods
        data = (
            data
            .ffill()  # Forward fill
            .bfill()  # Back fill any remaining NAs
            .infer_objects(copy=False)  # Handle downcasting warning
        )
        
        if data['Close'].isna().any():
            return jsonify({"error": "Invalid price data"}), 400
        
        # Execute strategy
        strategy_class = RSIStrategy() if strategy == 'RSI' else MACDStrategy()
        try:
            result = strategy_class.calculate_returns(data)
        except ValueError as ve:
            return jsonify({"error": f"Strategy calculation failed: {str(ve)}"}), 400
        
        if result is None:
            return jsonify({"error": "Strategy calculation returned no result"}), 500
        
        # Save trade
        trade = Trade(symbol=symbol, strategy=strategy, return_value=float(result))
        trade.save()
        
        return jsonify({
            "symbol": symbol,
            "strategy": strategy,
            "return": result
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Backtest error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/trades')
def get_trades():
    try:
        query = """
        SELECT id, symbol, strategy, return_value, created_at
        FROM trades
        ORDER BY created_at DESC
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(query))
            trades = [{
                "id": row.id,
                "symbol": row.symbol,
                "strategy": row.strategy,
                "return_value": float(row.return_value),
                "created_at": row.created_at.isoformat()
            } for row in result]
            
        return jsonify(trades)
        
    except Exception as e:
        logger.error(f"Error fetching trades: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Create trades table if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                strategy VARCHAR(10) NOT NULL,
                return_value DECIMAL(10,4) NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        """))
        conn.commit()
    
    app.run(debug=True)