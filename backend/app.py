from backend.strategies import RSIStrategy, MACDStrategy
from flask import Flask, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import yfinance as yf
from datetime import datetime, timedelta

def fetch_data(symbol):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    return yf.download(symbol, start=start_date, end=end_date)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trading.db'
db = SQLAlchemy(app)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    strategy = db.Column(db.String(10), nullable=False)
    return_value = db.Column(db.Float, nullable=False)

# Error handling for invalid strategies
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.route('/backtest/<strategy>/<symbol>')
def backtest(strategy, symbol):
    try:
        # Validate strategy
        if strategy not in ['RSI', 'MACD']:
            abort(404, description="Strategy not supported")
        
        # Fetch data (implement this function)
        data = fetch_data(symbol)
        
        # Calculate returns
        strategy_class = RSIStrategy() if strategy == 'RSI' else MACDStrategy()
        result = strategy_class.calculate_returns(data)
        
        # Save to DB
        trade = Trade(symbol=symbol, strategy=strategy, return_value=result)
        db.session.add(trade)
        db.session.commit()
        
        return jsonify({"return": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/trades')
def get_trades():
    trades = Trade.query.all()
    return jsonify([{
        "id": trade.id,
        "symbol": trade.symbol,
        "strategy": trade.strategy,
        "return_value": trade.return_value
    } for trade in trades])