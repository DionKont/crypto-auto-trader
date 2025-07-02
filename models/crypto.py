"""
Crypto class for managing cryptocurrency data across multiple timeframes
and calculating technical indicators
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import logging

class Crypto:
    """
    Class representing a cryptocurrency with data across multiple timeframes
    and methods to calculate and access technical indicators.
    """
    
    def __init__(self, symbol: str):
        """
        Initialize a Crypto object for a specific symbol.
        
        Args:
            symbol (str): The cryptocurrency symbol (e.g., 'BTC', 'ETH')
        """
        self.symbol = symbol.upper()
        self.timeframe_data: Dict[str, pd.DataFrame] = {}
        self.indicators: Dict[str, Dict[str, pd.Series]] = {}
        self.market_data: Dict[str, Any] = {
            'last_price': None,
            'bid': None,
            'ask': None,
            'spread': None,
            'spread_percent': None,
            'volume_24h': None,
            'high_24h': None,
            'low_24h': None,
            'last_update': None
        }
        self.logger = logging.getLogger(f"crypto.{self.symbol}")
    
    def set_ohlcv_data(self, timeframe: str, df) -> None:
        """
        Set OHLCV data for a specific timeframe.
        
        Args:
            timeframe (str): The timeframe (e.g., '1m', '5m', '15m', '1h')
            df: DataFrame or polars DataFrame with OHLCV data
        """
        # Convert to pandas DataFrame if it's not already
        if not isinstance(df, pd.DataFrame):
            # Assuming it's a polars DataFrame
            try:
                self.timeframe_data[timeframe] = df.to_pandas()
            except:
                # If to_pandas() doesn't work, try direct conversion
                self.timeframe_data[timeframe] = pd.DataFrame({
                    'timestamp': df['timestamp'].to_list(),
                    'open': df['open'].to_list(),
                    'high': df['high'].to_list(),
                    'low': df['low'].to_list(),
                    'close': df['close'].to_list(),
                    'volume': df['volume'].to_list()
                })
        else:
            self.timeframe_data[timeframe] = df.copy()
        
        # Ensure timestamps are datetime objects
        if 'timestamp' in self.timeframe_data[timeframe].columns:
            if not pd.api.types.is_datetime64_any_dtype(self.timeframe_data[timeframe]['timestamp']):
                self.timeframe_data[timeframe]['timestamp'] = pd.to_datetime(self.timeframe_data[timeframe]['timestamp'])
        
        # Initialize indicators dictionary for this timeframe
        if timeframe not in self.indicators:
            self.indicators[timeframe] = {}
        
        self.logger.info(f"Set {len(self.timeframe_data[timeframe])} candles for {self.symbol} {timeframe}")
    
    def update_ohlcv_data(self, timeframe: str, new_candle: Dict) -> None:
        """
        Update OHLCV data with a new candle from websocket.
        
        Args:
            timeframe (str): The timeframe to update
            new_candle (Dict): Dictionary containing the new candle data
        """
        if timeframe not in self.timeframe_data:
            self.logger.warning(f"Cannot update {timeframe} data - timeframe not initialized")
            return
            
        # Convert dict to DataFrame row
        new_df = pd.DataFrame([new_candle])
        
        # Ensure timestamp is datetime
        if 'timestamp' in new_df.columns and not pd.api.types.is_datetime64_any_dtype(new_df['timestamp']):
            new_df['timestamp'] = pd.to_datetime(new_df['timestamp'])
        
        # Check if timestamp already exists
        if timeframe in self.timeframe_data and 'timestamp' in self.timeframe_data[timeframe].columns:
            df = self.timeframe_data[timeframe]
            timestamps = df['timestamp'].to_list()
            
            if new_candle['timestamp'] in timestamps:
                # Update existing candle
                idx = df.index[df['timestamp'] == new_candle['timestamp']][0]
                self.timeframe_data[timeframe].loc[idx] = new_df.iloc[0]
            else:
                # Append new candle
                self.timeframe_data[timeframe] = pd.concat([
                    self.timeframe_data[timeframe], 
                    new_df
                ]).reset_index(drop=True)
        else:
            # Just append if we can't check timestamps
            self.timeframe_data[timeframe] = pd.concat([
                self.timeframe_data[timeframe], 
                new_df
            ]).reset_index(drop=True)
        
        # Update indicators for this timeframe
        self._recalculate_indicators(timeframe)
    
    def set_market_data(self, data: Dict[str, Any]) -> None:
        """
        Update market data like current price, spread, 24h stats.
        
        Args:
            data (Dict[str, Any]): Dictionary with market data fields
        """
        for key, value in data.items():
            if key in self.market_data:
                self.market_data[key] = value
        
        # Calculate spread if bid and ask are available
        if self.market_data['bid'] is not None and self.market_data['ask'] is not None:
            self.market_data['spread'] = self.market_data['ask'] - self.market_data['bid']
            if self.market_data['bid'] > 0:
                self.market_data['spread_percent'] = (
                    self.market_data['spread'] / self.market_data['bid']
                ) * 100
        
        # Set update timestamp
        self.market_data['last_update'] = datetime.now()
    
    def get_ohlcv(self, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Get OHLCV data for a specific timeframe.
        
        Args:
            timeframe (str): The timeframe to retrieve
            
        Returns:
            Optional[pd.DataFrame]: DataFrame with OHLCV data or None if not available
        """
        return self.timeframe_data.get(timeframe)
    
    def get_latest_candle(self, timeframe: str) -> Optional[Dict]:
        """
        Get the latest candle for a specific timeframe.
        
        Args:
            timeframe (str): The timeframe to retrieve
            
        Returns:
            Optional[Dict]: Latest candle data or None if not available
        """
        if timeframe not in self.timeframe_data or len(self.timeframe_data[timeframe]) == 0:
            return None
        
        latest = self.timeframe_data[timeframe].iloc[-1]
        return latest.to_dict()
    
    def calculate_ema(self, timeframe: str, window: int) -> None:
        """
        Calculate EMA (Exponential Moving Average) for a specific timeframe and window.
        
        Args:
            timeframe (str): The timeframe to calculate EMA for
            window (int): EMA window size
        """
        if timeframe not in self.timeframe_data:
            self.logger.warning(f"Cannot calculate EMA for {timeframe} - timeframe not available")
            return
        
        df = self.timeframe_data[timeframe]
        if len(df) < window:
            self.logger.warning(f"Not enough data for {window} EMA on {timeframe} - need at least {window} candles")
            return
            
        ema_key = f'ema_{window}'
        
        # Calculate EMA
        ema = df['close'].ewm(span=window, adjust=False).mean()
        
        # Store in indicators dictionary
        if timeframe not in self.indicators:
            self.indicators[timeframe] = {}
        
        self.indicators[timeframe][ema_key] = ema
    
    def calculate_atr(self, timeframe: str, window: int = 14) -> None:
        """
        Calculate ATR (Average True Range) for a specific timeframe.
        
        Args:
            timeframe (str): The timeframe to calculate ATR for
            window (int, optional): ATR window size. Defaults to 14.
        """
        if timeframe not in self.timeframe_data:
            self.logger.warning(f"Cannot calculate ATR for {timeframe} - timeframe not available")
            return
        
        df = self.timeframe_data[timeframe]
        if len(df) <= window:
            self.logger.warning(f"Not enough data for ATR on {timeframe} - need at least {window+1} candles")
            return
        
        # Calculate True Range
        df_copy = df.copy()
        df_copy['previous_close'] = df_copy['close'].shift(1)
        df_copy['tr1'] = df_copy['high'] - df_copy['low']
        df_copy['tr2'] = abs(df_copy['high'] - df_copy['previous_close'])
        df_copy['tr3'] = abs(df_copy['low'] - df_copy['previous_close'])
        df_copy['true_range'] = df_copy[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # Calculate ATR
        atr = df_copy['true_range'].rolling(window=window).mean()
        
        # Store in indicators dictionary
        if timeframe not in self.indicators:
            self.indicators[timeframe] = {}
        
        self.indicators[timeframe]['atr'] = atr
        
        # Calculate ATR%
        if 'close' in df.columns:
            with np.errstate(divide='ignore', invalid='ignore'):  # Handle div by zero
                atr_percent = (atr / df['close']) * 100
                atr_percent.replace([np.inf, -np.inf], np.nan, inplace=True)
            self.indicators[timeframe]['atr_percent'] = atr_percent
    
    def calculate_rsi(self, timeframe: str, window: int = 14) -> None:
        """
        Calculate RSI (Relative Strength Index) for a specific timeframe.
        
        Args:
            timeframe (str): The timeframe to calculate RSI for
            window (int, optional): RSI window size. Defaults to 14.
        """
        if timeframe not in self.timeframe_data:
            self.logger.warning(f"Cannot calculate RSI for {timeframe} - timeframe not available")
            return
        
        df = self.timeframe_data[timeframe]
        if len(df) <= window:
            self.logger.warning(f"Not enough data for RSI on {timeframe} - need at least {window+1} candles")
            return
        
        # Calculate price changes
        delta = df['close'].diff()
        
        # Split gains (up) and losses (down)
        up = delta.copy()
        up[up < 0] = 0
        down = -delta.copy()
        down[down < 0] = 0
        
        # Calculate EMA of gains and losses
        avg_gain = up.rolling(window=window).mean()
        avg_loss = down.rolling(window=window).mean()
        
        # Calculate RS and RSI
        with np.errstate(divide='ignore', invalid='ignore'):  # Handle div by zero
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        # Store in indicators dictionary
        if timeframe not in self.indicators:
            self.indicators[timeframe] = {}
        
        self.indicators[timeframe]['rsi'] = rsi
    
    def calculate_bollinger_bands(self, timeframe: str, window: int = 20, num_std: float = 2.0) -> None:
        """
        Calculate Bollinger Bands for a specific timeframe.
        
        Args:
            timeframe (str): The timeframe to calculate Bollinger Bands for
            window (int, optional): Window size for moving average. Defaults to 20.
            num_std (float, optional): Number of standard deviations. Defaults to 2.0.
        """
        if timeframe not in self.timeframe_data:
            self.logger.warning(f"Cannot calculate Bollinger Bands for {timeframe} - timeframe not available")
            return
        
        df = self.timeframe_data[timeframe]
        if len(df) < window:
            self.logger.warning(f"Not enough data for Bollinger Bands on {timeframe} - need at least {window} candles")
            return
        
        # Calculate middle band (SMA)
        mid_band = df['close'].rolling(window=window).mean()
        
        # Calculate standard deviation
        std = df['close'].rolling(window=window).std()
        
        # Calculate upper and lower bands
        upper_band = mid_band + (std * num_std)
        lower_band = mid_band - (std * num_std)
        
        # Store in indicators dictionary
        if timeframe not in self.indicators:
            self.indicators[timeframe] = {}
        
        bb_prefix = f'bb_{window}_{int(num_std) if num_std.is_integer() else num_std}'
        self.indicators[timeframe][f'{bb_prefix}_upper'] = upper_band
        self.indicators[timeframe][f'{bb_prefix}_middle'] = mid_band
        self.indicators[timeframe][f'{bb_prefix}_lower'] = lower_band
    
    def get_indicator(self, timeframe: str, indicator: str) -> Optional[pd.Series]:
        """
        Get a calculated indicator for a specific timeframe.
        
        Args:
            timeframe (str): The timeframe of the indicator
            indicator (str): The indicator name (e.g., 'ema_20', 'atr')
            
        Returns:
            Optional[pd.Series]: Indicator data or None if not available
        """
        if timeframe in self.indicators and indicator in self.indicators[timeframe]:
            return self.indicators[timeframe][indicator]
        return None
    
    def get_latest_indicator_value(self, timeframe: str, indicator: str) -> Optional[float]:
        """
        Get the latest value of a specific indicator.
        
        Args:
            timeframe (str): The timeframe of the indicator
            indicator (str): The indicator name
            
        Returns:
            Optional[float]: Latest indicator value or None if not available
        """
        indicator_data = self.get_indicator(timeframe, indicator)
        if indicator_data is not None and len(indicator_data) > 0:
            return indicator_data.iloc[-1]
        return None
    
    def _recalculate_indicators(self, timeframe: str) -> None:
        """
        Recalculate all existing indicators for a specific timeframe.
        
        Args:
            timeframe (str): The timeframe to recalculate indicators for
        """
        if timeframe not in self.indicators:
            return
        
        # Get existing indicators and recalculate them
        for indicator, _ in self.indicators[timeframe].items():
            # EMAs
            if indicator.startswith('ema_'):
                window = int(indicator.split('_')[1])
                self.calculate_ema(timeframe, window)
            
            # ATR
            elif indicator == 'atr' or indicator == 'atr_percent':
                self.calculate_atr(timeframe)
                
            # RSI
            elif indicator == 'rsi':
                self.calculate_rsi(timeframe)
                
            # Bollinger Bands
            elif indicator.startswith('bb_'):
                parts = indicator.split('_')
                window = int(parts[1])
                # Standard deviation might be in parts[2]
                std_dev = float(parts[2]) if len(parts) > 2 and parts[2] in ['upper', 'middle', 'lower'] else 2.0
                self.calculate_bollinger_bands(timeframe, window, std_dev)
    
    def calculate_all_indicators(self, timeframe: str) -> None:
        """
        Calculate all standard indicators for a timeframe.
        
        Args:
            timeframe (str): The timeframe to calculate indicators for
        """
        # EMAs with different windows
        self.calculate_ema(timeframe, 9)
        self.calculate_ema(timeframe, 20)
        self.calculate_ema(timeframe, 50)
        self.calculate_ema(timeframe, 200)
        
        # ATR with default window (14)
        self.calculate_atr(timeframe)
        
        # RSI with default window (14)
        self.calculate_rsi(timeframe)
        
        # Bollinger Bands with default parameters (20, 2.0)
        self.calculate_bollinger_bands(timeframe)
    
    def get_all_timeframes(self) -> List[str]:
        """
        Get all available timeframes for this crypto.
        
        Returns:
            List[str]: List of available timeframes
        """
        return list(self.timeframe_data.keys())
    
    def get_indicators_dataframe(self, timeframe: str) -> pd.DataFrame:
        """
        Get all indicators for a timeframe as a DataFrame.
        
        Args:
            timeframe (str): The timeframe to get indicators for
            
        Returns:
            pd.DataFrame: DataFrame containing all indicators for this timeframe
        """
        if timeframe not in self.timeframe_data or timeframe not in self.indicators:
            return pd.DataFrame()
        
        df = self.timeframe_data[timeframe].copy()
        
        # Add each indicator as a column
        for ind_name, ind_series in self.indicators[timeframe].items():
            df[ind_name] = ind_series
            
        return df
