from strategies import RSIStrategy, MACDStrategy
from flask import Flask, jsonify, abort
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import logging
import numpy as np

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # Change to DEBUG level
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configure PostgreSQL connection
DB_URI = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URI)

def fetch_data(symbol, days=252):  # Changed to 252 (one trading year)
    """Fetch historical data from PostgreSQL"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Add validation for future dates
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
        
        # Add data quality metrics
        quality_metrics = {
            'total_rows': len(df),
            'missing_values': df.isna().sum().to_dict(),
            'date_range': f"{df.index.min()} to {df.index.max()}",
            'trading_days': len(df)
        }
        
        # Pre-process price data using newer pandas methods
        required_cols = ['Close', 'Open', 'High', 'Low']
        fill_stats = {}
        for col in required_cols:
            missing_before = df[col].isna().sum()
            if missing_before > 0:
                logger.warning(f"Filling {missing_before} missing {col} prices for {symbol}")
                df[col] = df[col].ffill().bfill()
                fill_stats[col] = missing_before
        
        # Handle volume data
        df['Volume'] = df['Volume'].fillna(0)
        
        # Calculate daily returns using pct_change without method parameter
        df['Daily_Return'] = (
            df['Close']
            .pct_change()
            .fillna(0)  # Fill first day's return with 0
        )
        
        # Add returns analysis
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
        
        # Log data quality information
        logger.info(f"Data quality for {symbol}: {quality_metrics}")
        if fill_stats:
            logger.info(f"Filled missing values: {fill_stats}")
        
        logger.info(f"Fetched data for {symbol}: {df.shape[0]} rows")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Missing values summary:\n{df.isna().sum()}")
        
        return df, quality_metrics
        
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
def backtest(strategy, symbol, lookback_days=252):
    try:
        # Validate strategy
        if strategy not in ['RSI', 'MACD']:
            abort(404, description="Strategy not supported")
        
        # Fetch data with quality metrics
        data, quality_metrics = fetch_data(symbol, days=lookback_days)
        
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
            .convert_dtypes()  # Better type inference than infer_objects
        )
        
        if data['Close'].isna().any():
            return jsonify({"error": "Invalid price data"}), 400
        
        # Execute strategy
        strategy_class = RSIStrategy() if strategy == 'RSI' else MACDStrategy()
        try:
            result = strategy_class.calculate_returns(data)
            
            # Calculate strategy metrics with safe operations
            strategy_returns = data['Strategy_Return'].fillna(0)
            positive_returns = strategy_returns[strategy_returns > 0]
            negative_returns = strategy_returns[strategy_returns < 0]
            
            strategy_metrics = {
                "win_rate": float((strategy_returns > 0).sum() / len(strategy_returns) * 100),
                "avg_win": float(positive_returns.mean() if not positive_returns.empty else 0),
                "avg_loss": float(negative_returns.mean() if not negative_returns.empty else 0),
                "number_of_trades": int((data['Signal'].fillna(0) != data['Signal'].fillna(0).shift(1)).sum()),
                "max_drawdown": float(
                    (strategy_returns.cumsum().cummax() - strategy_returns.cumsum()).max()
                ) if len(strategy_returns) > 0 else 0.0
            }
            
            # Calculate profit factor with safe division
            wins_sum = positive_returns.sum()
            losses_sum = abs(negative_returns.sum())
            strategy_metrics["profit_factor"] = (
                float(wins_sum / losses_sum) 
                if losses_sum != 0 and not pd.isna(losses_sum) 
                else 0.0
            )
            
            # Calculate Sharpe ratio safely
            returns_std = strategy_returns.std()
            if len(strategy_returns) > 1 and returns_std > 0:
                strategy_metrics["sharpe_ratio"] = float(
                    strategy_returns.mean() / returns_std * np.sqrt(252)
                )
            else:
                strategy_metrics["sharpe_ratio"] = 0.0
            
            # Save trade with safe float conversion
            trade = Trade(
                symbol=symbol, 
                strategy=strategy, 
                return_value=float(0 if pd.isna(result) else result)
            )
            trade.save()
            
            # Prepare response with safe value handling
            response_data = {
                "symbol": symbol,
                "strategy": strategy,
                "return": float(0 if pd.isna(result) else result),
                "data_quality": quality_metrics,
                "period": {
                    "start": data.index.min().strftime('%Y-%m-%d'),
                    "end": data.index.max().strftime('%Y-%m-%d'),
                    "trading_days": len(data)
                },
                "market_return": quality_metrics['returns_analysis']['annualized_return'],
                "strategy_metrics": strategy_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            return jsonify(response_data)
            
        except ValueError as ve:
            return jsonify({"error": f"Strategy calculation failed: {str(ve)}"}), 400
            
    except Exception as e:
        logger.error(f"Backtest error: {str(e)}")
        return jsonify({
            "error": str(e),
            "type": type(e).__name__,
            "strategy": strategy,
            "symbol": symbol
        }), 500

@app.route('/data_quality/<symbol>')
def data_quality(symbol):
    try:
        # Fetch data with quality metrics
        data, quality_metrics = fetch_data(symbol)
        
        # Prepare response
        response_data = {
            "symbol": symbol,
            "data_quality": quality_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Data quality error: {str(e)}")
        return jsonify({
            "error": str(e),
            "type": type(e).__name__,
            "symbol": symbol
        }), 500

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