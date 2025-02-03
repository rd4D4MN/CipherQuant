from strategies import RSIStrategy, MACDStrategy
from flask import Flask, jsonify, abort, request
import pandas as pd
import os
import numpy as np
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import logging
from flask_cors import CORS
import json
from decimal import Decimal

# Custom JSON encoder for datetime and Decimal
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if pd.isna(obj):
            return None
        return super().default(obj)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
CORS(app)
app.json_encoder = CustomJSONEncoder

# Configure PostgreSQL connection
DB_URI = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URI)

def fetch_data(symbol, days=252):
    """Fetch historical data from PostgreSQL"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        if any(pd.date_range(start=start_date, end=end_date) > datetime.now()):
            logger.warning(f"Removing future dates from request for {symbol}")
            end_date = datetime.now()
        
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
        AND price_date <= CURRENT_DATE
        ORDER BY price_date
        """
        
        df = pd.read_sql_query(
            text(query),
            engine,
            params={'symbol': symbol, 'start_date': start_date, 'end_date': end_date},
            index_col='price_date',
            parse_dates=['price_date']
        )
        
        if df.empty:
            raise ValueError(f"No data available for {symbol}")
            
        if len(df) < 30:
            raise ValueError(f"Insufficient data points for {symbol} (minimum 30 required)")
            
        df.columns = [col.capitalize() for col in df.columns]
        
        quality_metrics = {
            'total_rows': len(df),
            'missing_values': df.isna().sum().to_dict(),
            'date_range': f"{df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}",
            'trading_days': len(df)
        }
        
        required_cols = ['Close', 'Open', 'High', 'Low']
        fill_stats = {}
        for col in required_cols:
            missing_before = df[col].isna().sum()
            if missing_before > 0:
                df[col] = df[col].ffill().bfill()
                fill_stats[col] = missing_before
        
        df['Volume'] = df['Volume'].fillna(0)
        df['Daily_Return'] = df['Close'].pct_change().fillna(0)
        
        returns_analysis = {
            'annualized_return': float(((1 + df['Daily_Return']).prod() ** (252/len(df)) - 1) * 100),
            'volatility': float(df['Daily_Return'].std() * np.sqrt(252) * 100),
            'max_drawdown': float((df['Close'] / df['Close'].expanding().max() - 1).min() * 100),
            'positive_days': int((df['Daily_Return'] > 0).sum())
        }
        
        quality_metrics.update({
            'returns_analysis': returns_analysis,
            'data_completeness': float((1 - df.isna().sum().mean()) * 100)
        })
        
        logger.info(f"Data quality for {symbol}: {quality_metrics}")
        return df, quality_metrics
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        raise

class Trade:
    def __init__(self, symbol, strategy, return_value):
        self.symbol = symbol
        self.strategy = strategy
        self.return_value = float(return_value)
        
    def save(self):
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO trades (symbol, strategy, return_value, created_at)
                        VALUES (:symbol, :strategy, :return_value, NOW())
                    """),
                    {
                        'symbol': self.symbol,
                        'strategy': self.strategy,
                        'return_value': self.return_value
                    }
                )
                conn.commit()
                logger.info(f"Saved trade: {self.symbol} {self.strategy} {self.return_value}")
        except Exception as e:
            logger.error(f"Error saving trade: {str(e)}")
            raise


@app.route('/chart_data/<strategy>/<symbol>')
def get_chart_data(strategy, symbol):
    try:
        # Validate inputs
        if strategy not in ['RSI', 'MACD']:
            return jsonify({"error": "Invalid strategy"}), 400
            
        # Fetch historical data
        df, _ = fetch_data(symbol)
        
        # Calculate strategy indicators
        if strategy == 'RSI':
            strategy_obj = RSIStrategy()
            df = strategy_obj.calculate_indicators(df)
            
            return jsonify({
                'dates': df.index.strftime('%Y-%m-%d').tolist(),
                'prices': df['Close'].tolist(),
                'returns': df['Daily_Return'].cumsum().tolist(),
                'rsi': df['RSI'].tolist(),
                'rsi_overbought': [70] * len(df),
                'rsi_oversold': [30] * len(df)
            })
        
        elif strategy == 'MACD':
            strategy_obj = MACDStrategy()
            df = strategy_obj.calculate_indicators(df)
            
            return jsonify({
                'dates': df.index.strftime('%Y-%m-%d').tolist(),
                'prices': df['Close'].tolist(),
                'returns': df['Daily_Return'].cumsum().tolist(),
                'macd': df['MACD'].tolist(),
                'signal': df['Signal'].tolist()
            })

    except Exception as e:
        logger.error(f"Error generating chart data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/trades')
def get_trades():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM trades")).scalar()
            offset = (page - 1) * per_page
            
            result = conn.execute(
                text("""
                    SELECT id, symbol, strategy, return_value, created_at 
                    FROM trades 
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                {'limit': per_page, 'offset': offset}
            )
            
            trades = [{
                'id': row.id,
                'symbol': row.symbol,
                'strategy': row.strategy,
                'return_value': float(row.return_value),
                'created_at': row.created_at.isoformat() if row.created_at else None
            } for row in result]
            
            return jsonify({
                'trades': trades,
                'total': count,
                'page': page,
                'per_page': per_page,
                'pages': (count + per_page - 1) // per_page,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Error fetching trades: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                strategy VARCHAR(10) NOT NULL,
                return_value DECIMAL(10,4) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
    
    app.run(debug=True)