#!/usr/bin/env python3

import sys
import time
from datetime import datetime
from typing import Dict, List, Callable, Optional, Any

import polars as pl

from modules.data_ingestion.data_manager import DataIngestionManager
from utils.symbol_manager import SymbolManager


class DataStream:
    """
    Unified data stream manager that handles both historical and live data.
    Provides event-driven callbacks and maintains rolling OHLCV data for symbols across multiple timeframes.
    """
    
    # Supported timeframes mapping: user_friendly -> kraken_interval_minutes
    TIMEFRAMES = {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '1h': 60
    }
    
    def __init__(self, data_manager: DataIngestionManager = None):
        self.data_manager = data_manager or DataIngestionManager(websocket_callback=self._websocket_callback)
        self.symbol_manager = SymbolManager(self.data_manager)
        
        # Data storage: (symbol, timeframe) -> polars DataFrame
        self._candles_data: Dict[tuple, pl.DataFrame] = {}
        
        # Symbol tracking: user_symbol -> pair_info
        self._tracked_symbols: Dict[str, Dict] = {}
        
        # Event callbacks
        self._data_callbacks: List[Callable] = []
        self._error_callbacks: List[Callable] = []
        
        # Configuration
        self._max_candles = 1000  # Default rolling window
        
    def add_data_callback(self, callback: Callable[[str, str, pl.DataFrame], None]):
        """Add a callback for data updates. Callback receives (symbol, timeframe, updated_dataframe)"""
        self._data_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable[[str, str], None]):
        """Add a callback for errors. Callback receives (symbol, error_message)"""
        self._error_callbacks.append(callback)
    
    def _websocket_callback(self, channel: str, data: Dict):
        """Internal websocket callback that processes live data"""
        if channel == "ohlc" and 'data' in data and data['data']:
            ohlc = data['data'][0]
            
            # Find which symbol this update belongs to
            ws_pair = ohlc.get('pair', '')
            user_symbol = None
            
            for symbol, pair_info in self._tracked_symbols.items():
                if pair_info['websocket_pair'] == ws_pair:
                    user_symbol = symbol
                    break
            
            if user_symbol:
                self._process_live_candle(user_symbol, ohlc)
    
    def _process_live_candle(self, symbol: str, ohlc: Dict):
        """Process a live candle update for a symbol (only 1m timeframe from websocket)"""
        try:
            new_row = pl.DataFrame({
                'timestamp': [datetime.now()],
                'open': [float(ohlc.get('open', 0))],
                'high': [float(ohlc.get('high', 0))],
                'low': [float(ohlc.get('low', 0))],
                'close': [float(ohlc.get('close', 0))],
                'volume': [float(ohlc.get('volume', 0))]
            })
            
            # Only update 1m timeframe from websocket
            key = (symbol, '1m')
            if key in self._candles_data:
                # Append new candle and maintain rolling window
                self._candles_data[key] = pl.concat([self._candles_data[key], new_row]).tail(self._max_candles)
            else:
                self._candles_data[key] = new_row
            
            # Notify callbacks
            for callback in self._data_callbacks:
                try:
                    callback(symbol, '1m', self._candles_data[key])
                except Exception as e:
                    print(f"Error in data callback: {e}")
                    
        except Exception as e:
            error_msg = f"Error processing live candle: {e}"
            print(error_msg)
            for callback in self._error_callbacks:
                try:
                    callback(symbol, error_msg)
                except:
                    pass
    
    def load_symbol(self, symbol: str, timeframes: List[str] = None, history_count: int = 200) -> bool:
        """
        Load historical data for a symbol across multiple timeframes and prepare it for live tracking.
        
        Args:
            symbol: The trading symbol (e.g., 'BTC', 'ETH')
            timeframes: List of timeframes to load (e.g., ['1m', '5m', '15m', '1h']). If None, loads all supported timeframes.
            history_count: Number of historical candles to load per timeframe
            
        Returns:
            True if successful for at least one timeframe, False otherwise.
        """
        symbol = symbol.upper()
        
        if timeframes is None:
            timeframes = list(self.TIMEFRAMES.keys())
        
        # Validate timeframes
        invalid_timeframes = [tf for tf in timeframes if tf not in self.TIMEFRAMES]
        if invalid_timeframes:
            print(f"Warning: Invalid timeframes {invalid_timeframes}. Supported: {list(self.TIMEFRAMES.keys())}")
            timeframes = [tf for tf in timeframes if tf in self.TIMEFRAMES]
        
        if not timeframes:
            print("No valid timeframes specified")
            return False
        
        # Find symbol info
        pair_info = self.symbol_manager.find_pair(symbol)
        if not pair_info:
            error_msg = f"Symbol {symbol} not found"
            print(error_msg)
            for callback in self._error_callbacks:
                try:
                    callback(symbol, error_msg)
                except:
                    pass
            return False
        
        kraken_pair = pair_info['kraken_pair']
        ws_pair = pair_info['websocket_pair']
        
        print(f"Loading {symbol}: {kraken_pair} (WS: {ws_pair}) - Timeframes: {timeframes}")
        
        success_count = 0
        
        # Load historical data for each timeframe
        for timeframe in timeframes:
            interval = self.TIMEFRAMES[timeframe]
            try:
                ohlc_data = self.data_manager.get_ohlc_data(kraken_pair, interval=interval)
                if not ohlc_data or kraken_pair not in ohlc_data:
                    print(f"No historical data available for {symbol} {timeframe}")
                    continue
                
                candles = ohlc_data[kraken_pair][-history_count:]
                
                key = (symbol, timeframe)
                self._candles_data[key] = pl.DataFrame({
                    'timestamp': [datetime.fromtimestamp(float(c[0])) for c in candles],
                    'open': [float(c[1]) for c in candles],
                    'high': [float(c[2]) for c in candles],
                    'low': [float(c[3]) for c in candles],
                    'close': [float(c[4]) for c in candles],
                    'volume': [float(c[6]) for c in candles]
                })
                
                print(f"Loaded {len(self._candles_data[key])} candles for {symbol} {timeframe}")
                success_count += 1
                
                # Notify callbacks of initial data
                for callback in self._data_callbacks:
                    try:
                        callback(symbol, timeframe, self._candles_data[key])
                    except Exception as e:
                        print(f"Error in data callback: {e}")
                        
            except Exception as e:
                error_msg = f"Error loading {symbol} {timeframe}: {e}"
                print(error_msg)
                for callback in self._error_callbacks:
                    try:
                        callback(symbol, error_msg)
                    except:
                        pass
        
        if success_count > 0:
            self._tracked_symbols[symbol] = pair_info
            self._max_candles = max(self._max_candles, history_count * 2)  # Allow for growth
            return True
        
        return False
    
    def start_live_data(self, symbols: List[str] = None) -> bool:
        """
        Start live data streaming for tracked symbols or specified symbols.
        Returns True if successful, False otherwise.
        """
        if symbols is None:
            symbols = list(self._tracked_symbols.keys())
        
        if not symbols:
            print("No symbols to track")
            return False
        
        # Start websocket
        print("Starting websocket connection...")
        self.data_manager.start_websocket()
        time.sleep(2)  # Allow connection to establish
        
        # Subscribe to each symbol
        ws_pairs = []
        for symbol in symbols:
            if symbol in self._tracked_symbols:
                ws_pairs.append(self._tracked_symbols[symbol]['websocket_pair'])
            else:
                print(f"Warning: {symbol} not loaded, skipping live data")
        
        if ws_pairs:
            success = self.data_manager.subscribe_ohlc(ws_pairs, interval=1)
            if success:
                print(f"Subscribed to live data: {', '.join(symbols)}")
                return True
            else:
                print("Failed to subscribe to live data")
                return False
        
        return False
    
    def get_data(self, symbol: str, timeframe: str = '1m') -> Optional[pl.DataFrame]:
        """Get the current data for a symbol and timeframe"""
        key = (symbol.upper(), timeframe)
        return self._candles_data.get(key)
    
    def get_latest_candle(self, symbol: str, timeframe: str = '1m') -> Optional[Dict]:
        """Get the latest candle for a symbol and timeframe as a dictionary"""
        df = self.get_data(symbol, timeframe)
        if df is not None and len(df) > 0:
            latest = df.tail(1)
            return {
                'timestamp': latest['timestamp'][0],
                'open': latest['open'][0],
                'high': latest['high'][0],
                'low': latest['low'][0],
                'close': latest['close'][0],
                'volume': latest['volume'][0]
            }
        return None
    
    def get_all_data(self, symbol: str) -> Dict[str, pl.DataFrame]:
        """Get all timeframe data for a symbol"""
        symbol = symbol.upper()
        result = {}
        for timeframe in self.TIMEFRAMES.keys():
            key = (symbol, timeframe)
            if key in self._candles_data:
                result[timeframe] = self._candles_data[key]
        return result
    
    def get_loaded_timeframes(self, symbol: str) -> List[str]:
        """Get list of loaded timeframes for a symbol"""
        symbol = symbol.upper()
        timeframes = []
        for timeframe in self.TIMEFRAMES.keys():
            key = (symbol, timeframe)
            if key in self._candles_data:
                timeframes.append(timeframe)
        return timeframes
    
    def get_tracked_symbols(self) -> List[str]:
        """Get list of currently tracked symbols"""
        return list(self._tracked_symbols.keys())
    
    def get_available_symbols(self, limit: int = 50) -> List[str]:
        """Get list of available symbols from the exchange"""
        return self.symbol_manager.get_available_symbols()[:limit]
    
    def close(self):
        """Clean shutdown"""
        print("Closing DataStream...")
        if self.data_manager:
            self.data_manager.close()
