import { Line } from 'react-chartjs-2';

export default function StrategyChart({ strategyData }) {
  const data = {
    labels: strategyData.dates,
    datasets: [
      {
        label: 'RSI Strategy',
        data: strategyData.rsiReturns,
        borderColor: 'blue',
      },
      {
        label: 'MACD Strategy',
        data: strategyData.macdReturns,
        borderColor: 'green',
      },
    ],
  };
  return <Line data={data} />;
}