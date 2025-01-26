from flask import Flask, jsonify, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trading.db'
db = SQLAlchemy(app)

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