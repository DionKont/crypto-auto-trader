#!/usr/bin/env python3

import sys
import time
from datetime import datetime
from typing import Dict

from utils.data_stream import DataStream


class CryptoTrader:
    """Modern crypto trader using DataStream for unified data management"""
    
    def __init__(self):
        self.data_stream = DataStream()
        self.setup_callbacks()
        
        # Demo/Mock state
        self.last_price = {}
        self.price_alerts = {}  # symbol -> price threshold
        
    def setup_callbacks(self):
        """Setup event callbacks for data updates"""
        self.data_stream.add_data_callback(self.on_data_update)
        self.data_stream.add_error_callback(self.on_error)
    
    def on_data_update(self, symbol: str, df):
        """Handle data updates from DataStream"""
        if len(df) > 0:
            latest = df.tail(1)
            current_price = latest['close'][0]
            timestamp = latest['timestamp'][0]
            
            # Track price changes
            old_price = self.last_price.get(symbol, current_price)
            self.last_price[symbol] = current_price
            
            # Price change indicator
            change = ""
            if current_price > old_price:
                change = "📈"
            elif current_price < old_price:
                change = "📉"
            else:
                change = "➡️"
            
            print(f"{change} {symbol}: ${current_price:.2f} @ {timestamp.strftime('%H:%M:%S')}")
            
            # Check price alerts (mock strategy logic)
            self.check_price_alerts(symbol, current_price)
    
    def on_error(self, symbol: str, error_msg: str):
        """Handle errors from DataStream"""
        print(f"❌ Error for {symbol}: {error_msg}")
    
    def set_price_alert(self, symbol: str, price: float):
        """Demo: Set a price alert for a symbol"""
        self.price_alerts[symbol] = price
        print(f"🔔 Alert set for {symbol} at ${price:.2f}")
    
    def check_price_alerts(self, symbol: str, current_price: float):
        """Demo: Check if price alert should trigger"""
        if symbol in self.price_alerts:
            alert_price = self.price_alerts[symbol]
            if current_price >= alert_price:
                print(f"🚨 PRICE ALERT! {symbol} reached ${current_price:.2f} (target: ${alert_price:.2f})")
                # Remove the alert after triggering
                del self.price_alerts[symbol]
    
    def show_market_summary(self, symbols):
        """Demo: Show current market summary for loaded symbols"""
        print("\n" + "="*60)
        print("📊 MARKET SUMMARY")
        print("="*60)
        
        for symbol in symbols:
            candle = self.data_stream.get_latest_candle(symbol)
            if candle:
                print(f"{symbol:>6}: ${candle['close']:>8.2f} | Vol: {candle['volume']:>10.2f}")
        print("="*60)
    
    def simulate_strategy_signal(self, symbol: str):
        """Demo: Simulate a simple strategy signal"""
        df = self.data_stream.get_data(symbol)
        if df is None or len(df) < 20:
            print(f"⚠️  Not enough data for {symbol} strategy")
            return
        
        # Simple moving average crossover (demo)
        recent_data = df.tail(20)
        sma_5 = recent_data.tail(5)['close'].mean()
        sma_10 = recent_data.tail(10)['close'].mean()
        current_price = recent_data.tail(1)['close'][0]
        
        print(f"\n🧠 Strategy Analysis for {symbol}:")
        print(f"   Current Price: ${current_price:.2f}")
        print(f"   SMA(5): ${sma_5:.2f}")
        print(f"   SMA(10): ${sma_10:.2f}")
        
        if sma_5 > sma_10:
            print(f"   Signal: 🟢 BULLISH (SMA5 > SMA10)")
        else:
            print(f"   Signal: 🔴 BEARISH (SMA5 < SMA10)")
    
    def demo_actions(self, symbols):
        """Run various demo actions to showcase DataStream capabilities"""
        print("\n🎬 Running Demo Actions...")
        print("-" * 40)
        
        # 1. Show available symbols
        available = self.data_stream.get_available_symbols(limit=10)
        print(f"📋 Available symbols (sample): {', '.join(available[:5])}...")
        
        # 2. Set some price alerts
        for symbol in symbols[:2]:  # Only for first 2 symbols
            candle = self.data_stream.get_latest_candle(symbol)
            if candle:
                # Set alert 1% above current price
                alert_price = candle['close'] * 1.01
                self.set_price_alert(symbol, alert_price)
        
        # 3. Show market summary
        self.show_market_summary(symbols)
        
        # 4. Run strategy analysis
        for symbol in symbols:
            self.simulate_strategy_signal(symbol)
        
        print("\n✅ Demo actions completed!")
    
    def run(self, symbols=None):
        """Main trading loop"""
        if symbols is None:
            symbols = ["BTC", "ETH"]
        
        # Convert to list if single symbol
        if isinstance(symbols, str):
            symbols = [symbols]
        
        symbols = [s.upper() for s in symbols]
        
        print(f"🚀 Starting Crypto Trader for: {', '.join(symbols)}")
        print("=" * 60)
        
        # Load historical data for each symbol
        loaded_symbols = []
        for symbol in symbols:
            print(f"\n📊 Loading {symbol}...")
            if self.data_stream.load_symbol(symbol, history_count=200):
                loaded_symbols.append(symbol)
                # Show latest candle
                candle = self.data_stream.get_latest_candle(symbol)
                if candle:
                    print(f"   Latest: ${candle['close']:.2f} @ {candle['timestamp'].strftime('%Y-%m-%d %H:%M')}")
            else:
                print(f"   ❌ Failed to load {symbol}")
        
        if not loaded_symbols:
            print("❌ No symbols loaded successfully")
            return
        
        print(f"\n✅ Successfully loaded: {', '.join(loaded_symbols)}")
        
        # Start live data streaming
        print("\n🔌 Starting live data...")
        if not self.data_stream.start_live_data(loaded_symbols):
            print("❌ Failed to start live data")
            return
        
        # Run demo actions after a short delay
        time.sleep(3)
        self.demo_actions(loaded_symbols)
        
        # Main loop
        print("\n📊 Live monitoring active... Press Ctrl+C to stop")
        print("-" * 50)
        
        try:
            loop_count = 0
            while True:
                time.sleep(10)  # Update every 10 seconds
                loop_count += 1
                
                # Every 30 seconds, show market summary
                if loop_count % 3 == 0:
                    self.show_market_summary(loaded_symbols)
                
                # Every 60 seconds, run strategy analysis
                if loop_count % 6 == 0:
                    for symbol in loaded_symbols:
                        self.simulate_strategy_signal(symbol)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping trader...")
        finally:
            self.data_stream.close()
            print("👋 Shutdown complete!")


def main():
    """Main function"""
    symbols = ["BTC", "ETH"]  # Default symbols
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        symbols = [arg.upper() for arg in sys.argv[1:]]
    
    print(f"🎯 Target symbols: {', '.join(symbols)}")
    print("💡 Tip: Run with symbols as arguments: python main.py BTC ETH ADA")
    
    trader = CryptoTrader()
    trader.run(symbols)


if __name__ == "__main__":
    main()
