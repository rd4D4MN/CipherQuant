from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trading.db'
db = SQLAlchemy(app)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10))
    strategy = db.Column(db.String(50))
    return_value = db.Column(db.Float)

@app.route('/strategies')
def get_strategies():
    # Fetch strategies from DB and return as JSON
    return jsonify([{"name": "RSI"}, {"name": "MACD"}])

@app.route('/backtest/<strategy>/<symbol>')
def backtest(strategy, symbol):
    # Fetch data, run strategy, save to DB
    return jsonify({"return": 0.15})