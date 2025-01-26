import { Line } from 'react-chartjs-2';

export default function StrategyChart({ strategyData }) {
  const data = {
    labels: strategyData.dates,
    datasets: [{
      label: 'Portfolio Value',
      data: strategyData.values
    }]
  };
  return <Line data={data} />;
}