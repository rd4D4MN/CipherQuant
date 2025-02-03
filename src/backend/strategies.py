from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import logging

# Configure logging
logger = logging.getLogger(__name__)

class Strategy(ABC):
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        try:
            required_columns = ['Close', 'Open', 'High', 'Low', 'Volume', 'Daily_Return']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            # Initialize strategy columns
            data['Position'] = 0.0
            data['Signal'] = 0.0
            data['Entry_Price'] = 0.0
            data['Strategy_Return'] = 0.0
            
            return data

        except Exception as e:
            logger.error(f"Error preprocessing data: {str(e)}")
            raise

class RSIStrategy(Strategy):
    def __init__(self):
        # RSI parameters
        self.rsi_period = 14
        self.oversold = 30
        self.overbought = 70
        
        # Position sizing and risk management
        self.position_size = 1.0
        self.stop_loss = 0.02    # 2% stop loss
        self.take_profit = 0.05  # 5% take profit
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI and other technical indicators"""
        try:
            # Copy input data to avoid modifications
            df = data.copy()
            
            # Calculate daily returns
            df['Daily_Return'] = df['Close'].pct_change()
            
            # Calculate RSI with data validation
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).fillna(0)
            loss = (-delta.where(delta < 0, 0)).fillna(0)
            
            # Use EMA for smoother calculation
            avg_gain = gain.ewm(span=self.rsi_period, adjust=False).mean()
            avg_loss = loss.ewm(span=self.rsi_period, adjust=False).mean()
            
            rs = avg_gain / avg_loss.replace(0, np.inf)
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Fill any remaining NaN values
            df['RSI'] = df['RSI'].fillna(50)
            df['Daily_Return'] = df['Daily_Return'].fillna(0)
            
            logger.info(f"RSI calculation completed. Range: {df['RSI'].min():.2f} to {df['RSI'].max():.2f}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            raise  
    def calculate_returns(self, data: pd.DataFrame) -> float:
        try:
            data = self.preprocess_data(data)
            
            # Calculate RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss.replace(0, np.inf)
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # Generate signals and positions
            for i in range(1, len(data)):
                price = data['Close'].iloc[i]
                rsi = data['RSI'].iloc[i]
                position = data['Position'].iloc[i-1]
                
                # Risk management
                if position != 0:
                    entry_price = data['Entry_Price'].iloc[i-1]
                    returns = (price - entry_price) / entry_price
                    
                    if returns <= -self.stop_loss or returns >= self.take_profit:
                        position = 0
                        data.iloc[i, data.columns.get_loc('Signal')] = 0
                    else:
                        data.iloc[i, data.columns.get_loc('Signal')] = position
                        
                    data.iloc[i, data.columns.get_loc('Strategy_Return')] = \
                        position * data['Daily_Return'].iloc[i]
                
                # Entry signals    
                if position == 0:
                    if rsi < self.oversold:
                        position = self.position_size
                        data.iloc[i, data.columns.get_loc('Signal')] = 1
                    elif rsi > self.overbought:
                        position = -self.position_size
                        data.iloc[i, data.columns.get_loc('Signal')] = -1
                
                # Update position tracking
                data.iloc[i, data.columns.get_loc('Position')] = position
                data.iloc[i, data.columns.get_loc('Entry_Price')] = \
                    price if position != 0 else 0
            
            # Calculate metrics
            metrics = self.calculate_metrics(data)
            logger.info(f"""
            RSI Strategy Performance:
            Total Return: {metrics['total_return']:.2%}
            Win Rate: {metrics['win_rate']:.2%}
            Max Drawdown: {metrics['max_drawdown']:.2%}
            Number of Trades: {metrics['trades']}
            """)
            
            return float(metrics['total_return'])
            
        except Exception as e:
            logger.error(f"Error in RSI strategy: {str(e)}")
            raise

    def calculate_metrics(self, data: pd.DataFrame) -> dict:
        """Calculate strategy performance metrics"""
        try:
            # Calculate total return
            total_return = data['Strategy_Return'].sum()
            
            # Calculate win rate
            winning_trades = (data['Strategy_Return'] > 0).sum()
            total_trades = (data['Signal'] != 0).sum()
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # Calculate maximum drawdown
            cumulative_returns = data['Strategy_Return'].cumsum()
            rolling_max = cumulative_returns.expanding().max()
            drawdowns = cumulative_returns - rolling_max
            max_drawdown = drawdowns.min()
            
            # Count number of trades (signal changes)
            trades = ((data['Signal'] != 0) & (data['Signal'] != data['Signal'].shift(1))).sum()
            
            return {
                'total_return': total_return,
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'trades': trades
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            raise
class MACDStrategy(Strategy):
    def get_minimum_required_data(self) -> int:
        return 40  # Need sufficient data for MACD calculation

    def calculate_returns(self, data: pd.DataFrame) -> float:
        data = self.preprocess_data(data)
        
        # Calculate MACD with error handling
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        # Generate signals
        data['Signal'] = np.where(macd > signal, 1, -1)
        data['Strategy_Return'] = data['Signal'].shift(1).fillna(0) * data['Daily_Return'].fillna(0)
        
        return float(data['Strategy_Return'].fillna(0).cumsum().iloc[-1])