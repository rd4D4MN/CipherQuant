from abc import ABC, abstractmethod
import pandas as pd

class Strategy(ABC):
    @abstractmethod
    def calculate_returns(self, data: pd.DataFrame) -> float:
        pass

class RSIStrategy(Strategy):
    def calculate_returns(self, data):
        # RSI logic using vectorized operations
        return data['returns'].mean()  # Simplified example

class MACDStrategy(Strategy):
    def calculate_returns(self, data):
        # MACD crossover logic
        return data['returns'].max()