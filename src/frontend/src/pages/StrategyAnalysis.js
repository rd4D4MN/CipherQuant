import React, { useState, useEffect } from 'react';
import StrategyChart from '../components/StrategyChart';
import StrategyTable from '../components/StrategyTable';
import './StrategyAnalysis.css';

export default function StrategyAnalysis() {
  const [selectedSymbol, setSelectedSymbol] = useState('MSFT');
  const [selectedStrategy, setSelectedStrategy] = useState('RSI');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [compareStrategies, setCompareStrategies] = useState(false);
  const [strategyMetrics, setStrategyMetrics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const symbols = ['MSFT', 'AAPL', 'GOOGL'];
  const strategies = ['RSI', 'MACD'];

  useEffect(() => {
    // Set default dates (last 30 days)
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    
    // Format dates as YYYY-MM-DD
    const formatDate = (date) => {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };
    
    // Set initial dates
    setEndDate(formatDate(end));
    setStartDate(formatDate(start));
  }, []);

  // Get max date for date pickers (today)
  const maxDate = new Date().toISOString().split('T')[0];

  // Add date validation function
  const validateDates = (start, end) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const startDateObj = new Date(start);
    const endDateObj = new Date(end);

    // Reset time part to ensure proper date comparison
    startDateObj.setHours(0, 0, 0, 0);
    endDateObj.setHours(0, 0, 0, 0);

    if (startDateObj > today || endDateObj > today) {
      setError('Cannot analyze future dates. Please select dates in the past.');
      return false;
    }

    if (startDateObj > endDateObj) {
      setError('Start date must be before end date');
      return false;
    }

    setError(null);
    return true;
  };

  // Handle date changes
  const handleStartDateChange = (e) => {
    const newDate = e.target.value;
    if (new Date(newDate) > new Date()) {
      setError('Cannot select future dates');
      return;
    }
    setStartDate(newDate);
    validateDates(newDate, endDate);
  };

  const handleEndDateChange = (e) => {
    const newDate = e.target.value;
    if (new Date(newDate) > new Date()) {
      setError('Cannot select future dates');
      return;
    }
    setEndDate(newDate);
    validateDates(startDate, newDate);
  };

  useEffect(() => {
    const fetchStrategyComparison = async () => {
      if (!compareStrategies || !startDate || !endDate) return;
      
      if (!validateDates(startDate, endDate)) return;

      try {
        setLoading(true);
        setError(null);

        // Format dates in YYYY-MM-DD format for API request
        const formatDateForAPI = (dateStr) => {
          const date = new Date(dateStr);
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = String(date.getDate()).padStart(2, '0');
          return `${year}-${month}-${day}`;
        };

        const response = await fetch(
          `/api/compare_strategies?symbol=${selectedSymbol}&start_date=${formatDateForAPI(startDate)}&end_date=${formatDateForAPI(endDate)}`
        );
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        setStrategyMetrics(data);
        
      } catch (err) {
        setError(`Error comparing strategies: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchStrategyComparison();
  }, [compareStrategies, selectedSymbol, startDate, endDate]);

  return (
    <div className="strategy-analysis">
      <h1>Strategy Analysis</h1>
      
      <div className="controls">
        <div className="control-group">
          <label>Symbol:</label>
          <select 
            value={selectedSymbol} 
            onChange={(e) => setSelectedSymbol(e.target.value)}
          >
            {symbols.map(symbol => (
              <option key={symbol} value={symbol}>{symbol}</option>
            ))}
          </select>
        </div>
        
        <div className="control-group">
          <label>Strategy:</label>
          <select 
            value={selectedStrategy} 
            onChange={(e) => setSelectedStrategy(e.target.value)}
            disabled={compareStrategies}
          >
            {strategies.map(strategy => (
              <option key={strategy} value={strategy}>{strategy}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Start Date:</label>
          <input
            type="date"
            value={startDate}
            onChange={handleStartDateChange}
            max={maxDate}
            required
          />
        </div>

        <div className="control-group">
          <label>End Date:</label>
          <input
            type="date"
            value={endDate}
            onChange={handleEndDateChange}
            max={maxDate}
            required
          />
        </div>

        <div className="control-group">
          <label>
            <input
              type="checkbox"
              checked={compareStrategies}
              onChange={(e) => setCompareStrategies(e.target.checked)}
            />
            Compare Strategies
          </label>
        </div>

        {error && (
          <div className="error-message" style={{ 
            color: 'red', 
            marginTop: '10px',
            padding: '10px',
            backgroundColor: '#ffebee',
            borderRadius: '4px',
            border: '1px solid #ffcdd2'
          }}>
            <strong>Error:</strong> {error}
            <br />
            <small>Please select dates in the past and ensure start date is before end date.</small>
          </div>
        )}
      </div>

      {compareStrategies ? (
        <div className="comparison-section">
          <h2>Strategy Comparison</h2>
          {loading ? (
            <div className="loading">Loading comparison data...</div>
          ) : error ? (
            <div className="error">{error}</div>
          ) : (
            <div className="comparison-grid">
              {strategyMetrics.sort((a, b) => b.total_return - a.total_return).map(metric => (
                <div key={metric.strategy} className="comparison-card">
                  <h3>{metric.strategy}</h3>
                  <div className="metric-row">
                    <label>Total Return:</label>
                    <span className={metric.total_return >= 0 ? 'positive' : 'negative'}>
                      {(metric.total_return * 100).toFixed(2)}%
                    </span>
                  </div>
                  <div className="metric-row">
                    <label>Win Rate:</label>
                    <span>{(metric.win_rate * 100).toFixed(2)}%</span>
                  </div>
                  <div className="metric-row">
                    <label>Sharpe Ratio:</label>
                    <span>{metric.sharpe_ratio.toFixed(2)}</span>
                  </div>
                  <div className="metric-row">
                    <label>Max Drawdown:</label>
                    <span className="negative">{(metric.max_drawdown * 100).toFixed(2)}%</span>
                  </div>
                  <div className="metric-row">
                    <label>Total Trades:</label>
                    <span>{metric.trades}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <>
          <div className="chart-section">
            <StrategyChart 
              symbol={selectedSymbol} 
              strategy={selectedStrategy}
              startDate={startDate}
              endDate={endDate}
            />
          </div>

          <div className="table-section">
            <StrategyTable 
              symbol={selectedSymbol} 
              strategy={selectedStrategy}
            />
          </div>
        </>
      )}
    </div>
  );
} 