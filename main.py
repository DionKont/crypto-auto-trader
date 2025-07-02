#!/usr/bin/env python3

import sys
from utils.data_stream import DataStream


def main():
    """Simplified main function - just load historical data and print message"""
    
    # Get symbol from command line or use BTC as default
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
    else:
        symbol = "BTC"
    
    print(f"� Loading historical data for {symbol}...")
    
    # Create DataStream and load symbol data
    data_stream = DataStream()
    
    try:
        # Load historical data
        if data_stream.load_symbol(symbol, history_count=1000):
            # Get the loaded data
            df = data_stream.get_data(symbol)
            latest_candle = data_stream.get_latest_candle(symbol)
            
            print(f"✅ Successfully loaded {len(df)} candles for {symbol}")
            print(f"📊 Latest price: ${latest_candle['close']:.2f}")
            print(f"📈 Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
            print(f"📅 Data from: {df['timestamp'].min()} to {df['timestamp'].max()}")
            
        else:
            print(f"❌ Failed to load data for {symbol}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        data_stream.close()
        print("👋 Done!")


if __name__ == "__main__":
    main()
