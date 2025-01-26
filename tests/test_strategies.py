import pytest
from backend.strategies import RSIStrategy

def test_rsi_strategy():
    data = pd.DataFrame({'returns': [0.01, -0.02, 0.03]})
    strategy = RSIStrategy()
    assert 0 < strategy.calculate_returns(data) < 1