import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function StrategyTable() {
  const [strategies, setStrategies] = useState([]);

  useEffect(() => {
    axios.get('http://localhost:5000/strategies')
      .then(response => setStrategies(response.data))
      .catch(error => console.error("Error fetching strategies:", error));
  }, []);

  return (
    <table>
      {/* Render strategies data */}
    </table>
  );
}