import { render } from '@testing-library/react';
import StrategyChart from './StrategyChart';

test('renders chart with data', () => {
    const strategyData = {
        dates: ['2023-01-01', '2023-01-02'],
        rsiReturns: [100, 105],
        macdReturns: [100, 110],
    };
    render(<StrategyChart strategyData={strategyData} />);
});