from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class Strategy(ABC):
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean data before processing"""
        if data is None or data.empty:
            raise ValueError("No data provided")
        
        # Validate minimum data requirements
        if len(data) < self.get_minimum_required_data():
            raise ValueError(f"Insufficient data points. Need at least {self.get_minimum_required_data()} days")
        
        # Ensure required columns exist
        required_columns = ['Close', 'Daily_Return']
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"Missing required columns: {required_columns}")
        
        return data

    def get_minimum_required_data(self) -> int:
        """Return minimum number of data points required for the strategy"""
        return 30  # Default minimum, can be overridden by specific strategies

    @abstractmethod
    def calculate_returns(self, data: pd.DataFrame) -> float:
        pass

class RSIStrategy(Strategy):
    def get_minimum_required_data(self) -> int:
        return 50  # Need more data for reliable RSI calculation

    def calculate_returns(self, data: pd.DataFrame) -> float:
        data = self.preprocess_data(data)
        
        # Calculate RSI with error handling
        delta = data['Close'].diff(1)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Prevent division by zero
        avg_gain = gain.rolling(window=14, min_periods=1).mean()
        avg_loss = loss.rolling(window=14, min_periods=1).mean()
        
        # Safe division
        rs = avg_gain.div(avg_loss.replace(0, np.nan))
        data['RSI'] = 100 - (100 / (1 + rs)).fillna(50)
        
        # Generate signals
        data['Signal'] = np.where(data['RSI'] < 30, 1, np.where(data['RSI'] > 70, -1, 0))
        data['Strategy_Return'] = data['Signal'].shift(1).fillna(0) * data['Daily_Return'].fillna(0)
        
        return float(data['Strategy_Return'].fillna(0).cumsum().iloc[-1])

class MACDStrategy(Strategy):
    def get_minimum_required_data(self) -> int:
        return 40  # Need sufficient data for MACD calculation

    def calculate_returns(self, data: pd.DataFrame) -> float:
        data = self.preprocess_data(data)
        
        # Calculate MACD with error handling
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        # Generate signals
        data['Signal'] = np.where(macd > signal, 1, -1)
        data['Strategy_Return'] = data['Signal'].shift(1).fillna(0) * data['Daily_Return'].fillna(0)
        
        return float(data['Strategy_Return'].fillna(0).cumsum().iloc[-1])