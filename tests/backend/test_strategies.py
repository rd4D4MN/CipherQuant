import pytest
import pandas as pd
from backend.strategies import MACDStrategy, RSIStrategy

def test_rsi_strategy():
    data = pd.DataFrame({
        'Close': [100, 101, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90],
        'Daily_Return': [0.01, 0.02, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01]
    })
    strategy = RSIStrategy()
    result = strategy.calculate_returns(data)
    assert result > 0  # Example assertion


def test_macd_strategy():
    data = pd.DataFrame({
        'Close': [100, 101, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90],
        'Daily_Return': [0.01, 0.02, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01, -0.01]
    })
    strategy = MACDStrategy()
    result = strategy.calculate_returns(data)
    assert result > 0  # Example assertion