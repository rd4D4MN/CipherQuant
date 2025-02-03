import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import axios from 'axios';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function BacktestChart({ symbol, strategy }) {
  const [chartData, setChartData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    axios.get(`http://localhost:5000/chart_data/${strategy}/${symbol}`)
      .then(response => setChartData(response.data))
      .catch(error => {
        console.error("Error fetching chart data:", error);
        setError(error.message);
      });
  }, [symbol, strategy]);

  if (error) return <div className="chart-error">Error loading chart: {error}</div>;
  if (!chartData) return <div className="chart-loading">Loading chart...</div>;

  const priceChartData = {
    labels: chartData.dates,
    datasets: [
      {
        label: 'Price',
        data: chartData.prices,
        borderColor: 'rgb(53, 162, 235)',
        yAxisID: 'price'
      },
      {
        label: 'Returns',
        data: chartData.returns,
        borderColor: 'rgb(75, 192, 192)',
        yAxisID: 'returns'
      }
    ]
  };

  const priceChartOptions = {
    responsive: true,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    stacked: false,
    scales: {
      price: {
        type: 'linear',
        display: true,
        position: 'left',
        title: {
          display: true,
          text: 'Price'
        }
      },
      returns: {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
          display: true,
          text: 'Returns'
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    }
  };

  return (
    <div className="chart-container">
      <h2>{symbol} - {strategy} Analysis</h2>
      <Line data={priceChartData} options={priceChartOptions} />
      {strategy === 'RSI' && chartData.rsi && (
        <Line
          data={{
            labels: chartData.dates,
            datasets: [
              {
                label: 'RSI',
                data: chartData.rsi,
                borderColor: 'purple',
              },
              {
                label: 'Overbought',
                data: chartData.rsi_overbought,
                borderColor: 'red',
                borderDash: [5, 5]
              },
              {
                label: 'Oversold',
                data: chartData.rsi_oversold,
                borderColor: 'green',
                borderDash: [5, 5]
              }
            ]
          }}
          options={{
            responsive: true,
            scales: {
              y: {
                min: 0,
                max: 100,
                title: {
                  display: true,
                  text: 'RSI'
                }
              }
            }
          }}
        />
      )}
    </div>
  );
}