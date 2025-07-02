#!/usr/bin/env python3

import sys
from utils.data_stream import DataStream


def main():
    """Main function - load historical data for multiple timeframes and display summary"""
    
    # Get symbol from command line or use BTC as default
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
    else:
        symbol = "BTC"
    
    # Define timeframes to load
    timeframes = ['1m', '5m', '15m', '1h']
    
    print(f"🚀 Loading historical data for {symbol} across multiple timeframes...")
    
    # Create DataStream and load symbol data
    data_stream = DataStream()
    
    try:
        # Load historical data for multiple timeframes
        if data_stream.load_symbol(symbol, timeframes=timeframes, history_count=1000):
            print(f"\n✅ Successfully loaded data for {symbol}")
            
            # Display summary for each timeframe
            for timeframe in timeframes:
                df = data_stream.get_data(symbol, timeframe)
                if df is not None:
                    latest_candle = data_stream.get_latest_candle(symbol, timeframe)
                    
                    print(f"\n📊 {timeframe.upper()} Timeframe:")
                    print(f"   • Candles loaded: {len(df)}")
                    print(f"   • Latest price: ${latest_candle['close']:.2f}")
                    print(f"   • Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
                    print(f"   • Data from: {df['timestamp'].min()} to {df['timestamp'].max()}")
                else:
                    print(f"\n❌ No data available for {symbol} {timeframe}")
            
            # Show which timeframes were successfully loaded
            loaded_timeframes = data_stream.get_loaded_timeframes(symbol)
            print(f"\n📈 Loaded timeframes: {', '.join(loaded_timeframes)}")
            
        else:
            print(f"❌ Failed to load data for {symbol}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        data_stream.close()
        print("\n👋 Done!")


if __name__ == "__main__":
    main()
