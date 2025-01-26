from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class Strategy(ABC):
    @abstractmethod
    def calculate_returns(self, data: pd.DataFrame) -> float:
        pass

class RSIStrategy(Strategy):
    def calculate_returns(self, data: pd.DataFrame) -> float:
        # Calculate RSI
        delta = data['Close'].diff(1)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Generate signals (RSI < 30 = BUY, RSI > 70 = SELL)
        data['Signal'] = np.where(data['RSI'] < 30, 1, np.where(data['RSI'] > 70, -1, 0))
        data['Strategy_Return'] = data['Signal'].shift(1) * data['Daily_Return']
        return data['Strategy_Return'].cumsum().iloc[-1]

class MACDStrategy(Strategy):
    def calculate_returns(self, data):
        # MACD crossover logic
        return data['returns'].max()