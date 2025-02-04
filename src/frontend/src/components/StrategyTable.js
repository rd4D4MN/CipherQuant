import React, { useEffect, useState } from 'react';
import './StrategyTable.css';

export default function StrategyTable({ symbol, strategy }) {
  const [trades, setTrades] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    const fetchData = async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds timeout

      try {
        if (!symbol || !strategy) {
          console.warn('Missing required parameters:', { symbol, strategy });
          setError('Missing required parameters');
          return;
        }

        setLoading(true);
        setError(null);

        const apiUrl = new URL('http://localhost:5000/api/trades');
        apiUrl.searchParams.append('symbol', symbol);
        apiUrl.searchParams.append('strategy', strategy);
        apiUrl.searchParams.append('page', page.toString());
        apiUrl.searchParams.append('per_page', '10');

        console.log('Fetching from:', apiUrl.toString());

        const response = await fetch(apiUrl, {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          signal: controller.signal
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Received data:', data);

        if (!data.trades) {
          throw new Error('Invalid response format');
        }

        setTrades(data.trades);
        setTotalPages(Math.ceil(data.total / data.per_page));
        setMetrics(data.metrics);

      } catch (err) {
        console.error('Error in fetchData:', err);
        setError(`Error loading data: ${err.message}`);
      } finally {
        clearTimeout(timeoutId);
        setLoading(false);
      }
    };

    fetchData();
  }, [symbol, strategy, page]);

  const formatPercent = (value) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString();
  };

  if (loading) {
    return <div className="loading">Loading data...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="strategy-table-container">
      {metrics && (
        <div className="metrics-summary">
          <h3>Strategy Performance Metrics</h3>
          <div className="metrics-grid">
            <div className="metric-item">
              <label>Total Return</label>
              <span>{formatPercent(metrics.total_return)}</span>
            </div>
            <div className="metric-item">
              <label>Win Rate</label>
              <span>{formatPercent(metrics.win_rate)}</span>
            </div>
            <div className="metric-item">
              <label>Max Drawdown</label>
              <span>{formatPercent(metrics.max_drawdown)}</span>
            </div>
            <div className="metric-item">
              <label>Sharpe Ratio</label>
              <span>{metrics.sharpe_ratio.toFixed(2)}</span>
            </div>
            <div className="metric-item">
              <label>Total Trades</label>
              <span>{metrics.trades}</span>
            </div>
            <div className="metric-item">
              <label>Avg Return/Trade</label>
              <span>{formatPercent(metrics.avg_return_per_trade)}</span>
            </div>
          </div>
        </div>
      )}

      <h3>Trade History</h3>
      <table className="strategy-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Symbol</th>
            <th>Strategy</th>
            <th>Type</th>
            <th>Entry Price</th>
            <th>Exit Price</th>
            <th>Return</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade, index) => (
            <tr key={index}>
              <td>{formatDate(trade.created_date)}</td>
              <td>{trade.symbol}</td>
              <td>{trade.strategy}</td>
              <td>{trade.signal > 0 ? 'Buy' : 'Sell'}</td>
              <td>${trade.entry_price.toFixed(2)}</td>
              <td>${trade.exit_price ? trade.exit_price.toFixed(2) : '-'}</td>
              <td className={trade.return > 0 ? 'positive' : 'negative'}>
                {formatPercent(trade.return)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            Previous
          </button>
          <span>
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}