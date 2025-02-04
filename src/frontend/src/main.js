import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import StrategyAnalysis from './pages/StrategyAnalysis';
import './styles/main.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/strategies" element={<StrategyAnalysis />} />
            <Route path="/trades" element={<StrategyAnalysis />} />
            <Route path="/settings" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;