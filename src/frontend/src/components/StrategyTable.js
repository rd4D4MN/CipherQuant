import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function StrategyTable() {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchTrades(page);
  }, [page]);

  const fetchTrades = async (currentPage) => {
    try {
      setLoading(true);
      const response = await axios.get(`http://localhost:5000/trades?page=${currentPage}`);
      setTrades(response.data.trades);
      setTotalPages(response.data.pages);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading trades...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="trades-container">
      <table className="strategy-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Strategy</th>
            <th>Return Value</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {trades.map(trade => (
            <tr key={trade.id}>
              <td>{trade.symbol}</td>
              <td>{trade.strategy}</td>
              <td>{(trade.return_value * 100).toFixed(2)}%</td>
              <td>{new Date(trade.created_at).toLocaleDateString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pagination">
        <button 
          onClick={() => setPage(p => p - 1)}
          disabled={page === 1}
        >
          Previous
        </button>
        <span>Page {page} of {totalPages}</span>
        <button 
          onClick={() => setPage(p => p + 1)}
          disabled={page === totalPages}
        >
          Next
        </button>
      </div>
    </div>
  );
}