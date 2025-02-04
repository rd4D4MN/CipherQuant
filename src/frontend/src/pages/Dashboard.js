import React from 'react';
import './Dashboard.css';

export default function Dashboard() {
  return (
    <div className="dashboard">
      <h1>Welcome to CipherQuant</h1>
      <div className="dashboard-grid">
        <div className="dashboard-card">
          <h3>Strategy Analysis</h3>
          <p>Analyze trading strategies using technical indicators like RSI and MACD.</p>
          <button onClick={() => window.location.href = '/strategies'}>View Strategies</button>
        </div>
        <div className="dashboard-card">
          <h3>Trade History</h3>
          <p>View and analyze your historical trades and performance metrics.</p>
          <button onClick={() => window.location.href = '/trades'}>View Trades</button>
        </div>
        <div className="dashboard-card">
          <h3>Settings</h3>
          <p>Configure your trading parameters and preferences.</p>
          <button onClick={() => window.location.href = '/settings'}>View Settings</button>
        </div>
      </div>
    </div>
  );
} 