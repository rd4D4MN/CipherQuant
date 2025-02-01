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
    def calculate_returns(self, data: pd.DataFrame) -> float:
        # Calculate MACD and Signal Line
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        # Generate signals (MACD > Signal = BUY, MACD < Signal = SELL)
        data['Signal'] = np.where(macd > signal, 1, -1)
        data['Strategy_Return'] = data['Signal'].shift(1) * data['Daily_Return']
        return data['Strategy_Return'].cumsum().iloc[-1]