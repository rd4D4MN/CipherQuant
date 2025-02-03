import React from 'react';
import StrategyTable from './components/StrategyTable';
import StrategyChart from './components/StrategyChart';
import './styles/main.css';

function App() {
  return (
    <div className="App">
      <h1>Trading Strategy Dashboard</h1>
      <StrategyChart symbol="AAPL" strategy="RSI" />
      <StrategyTable />
    </div>
  );
}

export default App;