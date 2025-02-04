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
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
app.config['TIMEOUT'] = 300  # 5 minutes timeout
app.json_encoder = CustomJSONEncoder

# Test endpoint to verify API is working
@app.route('/api/test')
def test_api():
    return jsonify({
        "message": "API test endpoint is working",
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    })

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
        logger.info(f"Received request for chart data: strategy={strategy}, symbol={symbol}")
        # Validate inputs
        if strategy not in ['RSI', 'MACD']:
            logger.error(f"Invalid strategy: {strategy}")
            return jsonify({"error": "Invalid strategy"}), 400
            
        # Fetch historical data
        df, _ = fetch_data(symbol)
        
        # Calculate strategy indicators
        if strategy == 'RSI':
            strategy_obj = RSIStrategy()
            df = strategy_obj.calculate_indicators(df)
            
            logger.info(f"Returning chart data for {symbol} with strategy {strategy}")
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
            
            logger.info(f"Returning chart data for {symbol} with strategy {strategy}")
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

# Add strategy_data endpoint
@app.route('/api/strategy_data')
def get_strategy_data():
    try:
        symbol = request.args.get('symbol')
        strategy = request.args.get('strategy')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        logger.info(f"Received strategy data request: {symbol}, {strategy}, {start_date}, {end_date}")

        if not all([symbol, strategy, start_date, end_date]):
            return jsonify({"error": "Missing required parameters"}), 400

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
                'signals': [0] * len(df),  # Add signals array
                'strategy_returns': df['Daily_Return'].tolist()
            })
            
        elif strategy == 'MACD':
            strategy_obj = MACDStrategy()
            df = strategy_obj.calculate_indicators(df)
            
            return jsonify({
                'dates': df.index.strftime('%Y-%m-%d').tolist(),
                'prices': df['Close'].tolist(),
                'returns': df['Daily_Return'].cumsum().tolist(),
                'signals': [0] * len(df),  # Add signals array
                'strategy_returns': df['Daily_Return'].tolist()
            })
        else:
            return jsonify({"error": "Invalid strategy"}), 400

    except Exception as e:
        logger.error(f"Error in get_strategy_data: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add trades endpoint
@app.route('/api/trades')
def get_trades_data():
    try:
        symbol = request.args.get('symbol')
        strategy = request.args.get('strategy')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        logger.info(f"Received trades request: {symbol}, {strategy}, page={page}")

        # Fetch historical data and calculate strategy indicators
        df, _ = fetch_data(symbol)
        
        if strategy == 'RSI':
            strategy_obj = RSIStrategy()
            df = strategy_obj.calculate_indicators(df)
        elif strategy == 'MACD':
            strategy_obj = MACDStrategy()
            df = strategy_obj.calculate_indicators(df)
        else:
            return jsonify({"error": "Invalid strategy"}), 400

        # Generate trades from signals
        trades_list = []
        current_position = None
        entry_price = None
        entry_date = None

        for index, row in df.iterrows():
            if 'RSI' in df.columns:
                # RSI strategy signals
                signal = 1 if row['RSI'] < 30 else -1 if row['RSI'] > 70 else 0
            else:
                # MACD strategy signals
                signal = 1 if row['MACD'] > row['Signal'] else -1 if row['MACD'] < row['Signal'] else 0

            if signal != 0 and current_position is None:
                # Enter position
                current_position = signal
                entry_price = row['Close']
                entry_date = index
            elif current_position is not None and (signal == -current_position or signal == 0):
                # Exit position
                exit_price = row['Close']
                return_value = (exit_price - entry_price) / entry_price * current_position
                
                trades_list.append({
                    'id': len(trades_list) + 1,
                    'symbol': symbol,
                    'strategy': strategy,
                    'signal': current_position,
                    'entry_price': float(entry_price),
                    'exit_price': float(exit_price),
                    'return': float(return_value),
                    'created_date': entry_date.isoformat()
                })
                
                current_position = None
                entry_price = None
                entry_date = None

        # Calculate total number of trades
        total_trades = len(trades_list)
        
        # Paginate trades
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_trades = trades_list[start_idx:end_idx]

        # Calculate metrics
        if trades_list:
            total_return = sum(trade['return'] for trade in trades_list)
            winning_trades = sum(1 for trade in trades_list if trade['return'] > 0)
            win_rate = winning_trades / total_trades
            max_drawdown = min(trade['return'] for trade in trades_list)
        else:
            total_return = win_rate = max_drawdown = 0

        response = {
            'trades': paginated_trades,
            'total': total_trades,
            'page': page,
            'per_page': per_page,
            'pages': (total_trades + per_page - 1) // per_page,
            'metrics': {
                'total_return': total_return,
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': 0,  # Calculate if needed
                'trades': total_trades,
                'avg_return_per_trade': total_return / total_trades if total_trades > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Returning {len(paginated_trades)} trades for {symbol} {strategy}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in get_trades_data: {str(e)}")
        return jsonify({"error": str(e)}), 500

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