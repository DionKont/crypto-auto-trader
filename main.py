#!/usr/bin/env python3

import sys
import time
import signal
from datetime import datetime
from modules.data_ingestion.data_manager import DataIngestionManager
from utils.symbol_manager import SymbolManager

try:
    import polars as pl
except ImportError:
    print("Installing polars...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "polars"])
    import polars as pl


class SimpleTrader:
    def __init__(self, symbol, history_count=200):
        self.symbol = symbol.upper()
        self.history_count = history_count
        self.running = True
        self.data_manager = None
        self.symbol_manager = None
        self.candles_df = None
        
        signal.signal(signal.SIGINT, self._shutdown)
    
    def _shutdown(self, sig, frame):
        print(f"\nShutting down...")
        self.running = False
        if self.data_manager:
            self.data_manager.close()
        sys.exit(0)
    
    def _websocket_callback(self, channel, data):
        if channel == "ohlc" and 'data' in data and data['data']:
            ohlc = data['data'][0]
            new_row = pl.DataFrame({
                'timestamp': [datetime.now()],
                'open': [float(ohlc.get('open', 0))],
                'high': [float(ohlc.get('high', 0))],
                'low': [float(ohlc.get('low', 0))],
                'close': [float(ohlc.get('close', 0))],
                'volume': [float(ohlc.get('volume', 0))]
            })
            
            if self.candles_df is not None:
                self.candles_df = pl.concat([self.candles_df, new_row]).tail(self.history_count)
            else:
                self.candles_df = new_row
            
            print(f"Updated: {self.symbol} C:{ohlc.get('close')} | Total candles: {len(self.candles_df)}")
    
    def load_historical_data(self):
        print(f"Loading {self.history_count} historical 1m candles for {self.symbol}...")
        
        pair_info = self.symbol_manager.find_pair(self.symbol)
        if not pair_info:
            print(f"Symbol {self.symbol} not found")
            available = self.symbol_manager.get_available_symbols()[:10]
            print(f"Available symbols: {', '.join(available)}...")
            return False
        
        kraken_pair = pair_info['kraken_pair']
        ws_pair = pair_info['websocket_pair']
        
        print(f"Found: {self.symbol} -> {kraken_pair} (WS: {ws_pair})")
        
        ohlc_data = self.data_manager.get_ohlc_data(kraken_pair, interval=1)
        if not ohlc_data or kraken_pair not in ohlc_data:
            print("No historical data available")
            return False
        
        candles = ohlc_data[kraken_pair][-self.history_count:]
        
        self.candles_df = pl.DataFrame({
            'timestamp': [datetime.fromtimestamp(float(c[0])) for c in candles],
            'open': [float(c[1]) for c in candles],
            'high': [float(c[2]) for c in candles],
            'low': [float(c[3]) for c in candles],
            'close': [float(c[4]) for c in candles],
            'volume': [float(c[6]) for c in candles]
        })
        
        print(f"Loaded {len(self.candles_df)} candles")
        print(f"Latest: O:{self.candles_df['open'][-1]} H:{self.candles_df['high'][-1]} L:{self.candles_df['low'][-1]} C:{self.candles_df['close'][-1]}")
        
        return ws_pair
    
    def start_live_updates(self, ws_pair):
        print(f"Starting live updates for {ws_pair}...")
        
        self.data_manager.start_websocket()
        time.sleep(2)
        
        if self.data_manager.subscribe_ohlc([ws_pair], interval=1):
            print(f"Subscribed to {ws_pair} live updates")
        else:
            print("Subscription failed")
            return False
        
        print(f"\nLive monitoring {ws_pair} - Press Ctrl+C to stop")
        
        while self.running:
            time.sleep(1)
        
        return True
    
    def run(self):
        self.data_manager = DataIngestionManager(websocket_callback=self._websocket_callback)
        self.symbol_manager = SymbolManager(self.data_manager)
        
        ws_pair = self.load_historical_data()
        if ws_pair:
            self.start_live_updates(ws_pair)


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <SYMBOL> [HISTORY_COUNT]")
        print("Example: python main.py BTC 200")
        return 1
    
    symbol = sys.argv[1]
    history_count = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    
    trader = SimpleTrader(symbol, history_count)
    trader.run()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
