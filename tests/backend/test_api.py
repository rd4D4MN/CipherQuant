def test_backtest_endpoint(client):
    response = client.get('/backtest/RSI/AAPL')
    assert response.status_code == 200
    assert 'return' in response.json