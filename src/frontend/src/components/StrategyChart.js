import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
} from 'chart.js';
import 'chartjs-adapter-date-fns';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

export default function StrategyChart({ symbol, strategy, startDate, endDate }) {
  const [chartData, setChartData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 3;
  const RETRY_DELAY = 2000; // 2 seconds

  useEffect(() => {
    const fetchData = async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds timeout

      try {
        if (!symbol || !strategy || !startDate || !endDate) {
          console.warn('Missing required parameters:', { symbol, strategy, startDate, endDate });
          return;
        }

        // Parse dates and handle different formats
        const parseDate = (dateStr) => {
          try {
            // Handle MM/DD/YYYY format
            if (dateStr.includes('/')) {
              const [month, day, year] = dateStr.split('/');
              return new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
            }
            // Handle YYYY-MM-DD format
            return new Date(dateStr);
          } catch (error) {
            console.error('Date parsing error:', error);
            return null;
          }
        };

        // Get current date for validation
        const today = new Date();
        const defaultEndDate = new Date(today);
        defaultEndDate.setDate(today.getDate() - 1); // Yesterday
        const defaultStartDate = new Date(defaultEndDate);
        defaultStartDate.setDate(defaultEndDate.getDate() - 30); // Last 30 days

        // Parse input dates
        const startDateObj = parseDate(startDate) || defaultStartDate;
        const endDateObj = parseDate(endDate) || defaultEndDate;

        // Reset time part to ensure proper date comparison
        startDateObj.setHours(0, 0, 0, 0);
        endDateObj.setHours(0, 0, 0, 0);
        today.setHours(0, 0, 0, 0);

        // Validate dates
        if (startDateObj > today || endDateObj > today) {
          console.warn('Future dates detected, using last 30 days');
          startDateObj.setTime(defaultStartDate.getTime());
          endDateObj.setTime(defaultEndDate.getTime());
        }

        if (startDateObj > endDateObj) {
          console.warn('Start date after end date, swapping dates');
          [startDateObj, endDateObj] = [endDateObj, startDateObj];
        }

        const maxDays = 365;
        const daysDiff = Math.floor((endDateObj - startDateObj) / (1000 * 60 * 60 * 24));
        if (daysDiff > maxDays) {
          console.warn(`Date range exceeds ${maxDays} days, adjusting start date`);
          startDateObj.setTime(endDateObj.getTime());
          startDateObj.setDate(startDateObj.getDate() - maxDays);
        }

        setLoading(true);
        setError(null);

        // Format dates in YYYY-MM-DD format for API request
        const formatDateForAPI = (date) => {
          return date.toISOString().split('T')[0];  // Returns YYYY-MM-DD
        };

        const formattedStartDate = formatDateForAPI(startDateObj);
        const formattedEndDate = formatDateForAPI(endDateObj);

        console.log('API Request Parameters:', {
          symbol,
          strategy,
          startDate: formattedStartDate,
          endDate: formattedEndDate
        });

        console.log('Making API request with parameters:', {
          symbol,
          strategy,
          startDate: formattedStartDate,
          endDate: formattedEndDate,
          url: `/api/strategy_data?symbol=${encodeURIComponent(symbol)}&strategy=${encodeURIComponent(strategy)}&start_date=${encodeURIComponent(formattedStartDate)}&end_date=${encodeURIComponent(formattedEndDate)}`
        });

        // Test API connection
        try {
          const testResponse = await fetch('http://localhost:5000/api/test', {
            signal: controller.signal
          });
          if (!testResponse.ok) {
            throw new Error('API server is not responding correctly');
          }
          const testData = await testResponse.json();
          console.log('API test response:', testData);
        } catch (error) {
          console.error('API test failed:', error);
          throw new Error('API server is not responding correctly');
        }

        // Fetch strategy data with proper URL
        const apiUrl = new URL('http://localhost:5000/api/strategy_data');
        apiUrl.searchParams.append('symbol', symbol);
        apiUrl.searchParams.append('strategy', strategy);
        apiUrl.searchParams.append('start_date', formattedStartDate);
        apiUrl.searchParams.append('end_date', formattedEndDate);

        console.log('Fetching from:', apiUrl.toString());

        const response = await fetch(apiUrl, {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          signal: controller.signal,
          mode: 'cors',
          credentials: 'include'
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text();
          console.error('Error response from API:', {
            status: response.status,
            statusText: response.statusText,
            errorText
          });
          throw new Error(`Failed to fetch data: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Received data from API:', {
          hasData: !!data,
          hasDates: !!data.dates,
          dateCount: data.dates?.length,
          hasPrices: !!data.prices,
          priceCount: data.prices?.length,
          hasSignals: !!data.signals,
          signalCount: data.signals?.length,
          hasReturns: !!data.strategy_returns,
          returnCount: data.strategy_returns?.length
        });

        if (!data.dates || !data.prices || !data.signals || !data.strategy_returns) {
          console.error('Invalid data format:', data);
          throw new Error('Invalid data format received from server');
        }

        // Process data for chart
        const chartData = {
          labels: data.dates.map(date => new Date(date)),
          datasets: [
            {
              label: 'Price',
              data: data.prices,
              borderColor: 'rgb(75, 192, 192)',
              tension: 0.1,
              yAxisID: 'price'
            },
            {
              label: 'Strategy Returns',
              data: data.strategy_returns,
              borderColor: 'rgb(255, 99, 132)',
              tension: 0.1,
              yAxisID: 'returns'
            },
            {
              label: 'Buy Signals',
              data: data.signals.map((signal, i) => signal === 1 ? data.prices[i] : null),
              pointStyle: 'triangle',
              pointRadius: 10,
              pointBackgroundColor: 'green',
              showLine: false,
              yAxisID: 'price'
            },
            {
              label: 'Sell Signals',
              data: data.signals.map((signal, i) => signal === -1 ? data.prices[i] : null),
              pointStyle: 'triangle',
              pointRadius: 10,
              pointBackgroundColor: 'red',
              showLine: false,
              yAxisID: 'price'
            }
          ]
        };

        console.log('Chart data processed:', {
          hasLabels: !!chartData.labels,
          labelCount: chartData.labels?.length,
          datasetCount: chartData.datasets?.length
        });

        setChartData(chartData);
        setLoading(false);
      } catch (err) {
        console.error('Error in fetchData:', err);
        setError(`Error loading chart: ${err.message}`);
        setLoading(false);
      } finally {
        clearTimeout(timeoutId);
      }
    };

    fetchData();
  }, [symbol, strategy, startDate, endDate]);

  const options = {
    responsive: true,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: `${symbol} - ${strategy} Strategy Performance`,
      },
    },
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'day'
        },
        title: {
          display: true,
          text: 'Date'
        }
      },
      price: {
        type: 'linear',
        display: true,
        position: 'left',
        title: {
          display: true,
          text: 'Price ($)'
        }
      },
      returns: {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
          display: true,
          text: 'Returns (%)'
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  };

  if (loading) {
    return (
      <div className="chart-loading">
        <p>Loading chart data...</p>
        <p>Parameters: {JSON.stringify({ symbol, strategy, startDate, endDate })}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chart-error">
        <p style={{ color: 'red', fontWeight: 'bold' }}>{error}</p>
        <p>Please make sure:</p>
        <ul>
          <li>Both backend and frontend servers are running:
            <ul>
              <li>Backend: http://localhost:5000</li>
              <li>Frontend: http://localhost:3000</li>
            </ul>
          </li>
          <li>Selected dates are in the past</li>
          <li>Start date is before end date</li>
        </ul>
        <p>Parameters used:</p>
        <pre>{JSON.stringify({
          symbol,
          strategy,
          startDate: startDate ? new Date(startDate).toLocaleDateString() : null,
          endDate: endDate ? new Date(endDate).toLocaleDateString() : null
        }, null, 2)}</pre>
      </div>
    );
  }

  if (!chartData) {
    return (
      <div className="chart-error">
        <p>No data available for the selected parameters</p>
        <pre>{JSON.stringify({ symbol, strategy, startDate, endDate }, null, 2)}</pre>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <Line data={chartData} options={options} />
    </div>
  );
}