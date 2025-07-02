#!/usr/bin/env python3

import sys
from utils.data_stream import DataStream
from config.config_loader import ConfigLoader


def main():
    """Main function - load configuration and fetch multi-timeframe data"""
    
    print("🚀 Crypto Auto-Trader - Multi-Timeframe Data Analysis")
    print("=" * 60)
    
    # Load configuration
    print("\n📋 Loading configuration...")
    try:
        config_loader = ConfigLoader(interactive=True)
        config = config_loader.config
        print("✅ Configuration loaded successfully!")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Override symbol from command line if provided
    symbols = config.symbols.copy()
    if len(sys.argv) > 1:
        symbol_arg = sys.argv[1].upper()
        print(f"🔄 Overriding symbols with command line argument: {symbol_arg}")
        symbols = [symbol_arg]
    
    print(f"\n🎯 Target symbols: {', '.join(symbols)}")
    print(f"📊 Timeframes: {', '.join(config.timeframes)}")
    print(f"� History count: {config.history_count}")
    
    # Create DataStream and load symbol data
    data_stream = DataStream()
    
    try:
        # Process each symbol
        for symbol in symbols:
            print(f"\n{'='*60}")
            print(f"💰 Processing {symbol}")
            print(f"{'='*60}")
            
            # Load historical data for multiple timeframes
            if data_stream.load_symbol(symbol, timeframes=config.timeframes, history_count=config.history_count):
                print(f"\n✅ Successfully loaded data for {symbol}")
                
                # Display summary for each timeframe
                for timeframe in config.timeframes:
                    df = data_stream.get_data(symbol, timeframe)
                    if df is not None:
                        latest_candle = data_stream.get_latest_candle(symbol, timeframe)
                        
                        print(f"\n📊 {timeframe.upper()} Timeframe:")
                        print(f"   • Candles loaded: {len(df):,}")
                        print(f"   • Latest price: ${latest_candle['close']:.2f}")
                        print(f"   • Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
                        print(f"   • Volume range: {df['volume'].min():.0f} - {df['volume'].max():.0f}")
                        print(f"   • Data from: {df['timestamp'].min()} to {df['timestamp'].max()}")
                        
                        # Calculate basic metrics
                        price_change = latest_candle['close'] - df['close'][0]
                        price_change_pct = (price_change / df['close'][0]) * 100
                        volatility = df['close'].std()
                        
                        print(f"   • Price change: ${price_change:+.2f} ({price_change_pct:+.2f}%)")
                        print(f"   • Volatility (σ): ${volatility:.2f}")
                    else:
                        print(f"\n❌ No data available for {symbol} {timeframe}")
                
                # Show which timeframes were successfully loaded
                loaded_timeframes = data_stream.get_loaded_timeframes(symbol)
                print(f"\n📈 Successfully loaded timeframes: {', '.join(loaded_timeframes)}")
                
                # Summary statistics
                if loaded_timeframes:
                    print(f"\n📊 Summary for {symbol}:")
                    all_data = data_stream.get_all_data(symbol)
                    
                    print(f"   • Total timeframes loaded: {len(loaded_timeframes)}")
                    total_candles = sum(len(df) for df in all_data.values())
                    print(f"   • Total candles across all timeframes: {total_candles:,}")
                    
                    # Find most volatile timeframe
                    volatilities = {}
                    for tf in loaded_timeframes:
                        df = all_data[tf]
                        volatilities[tf] = df['close'].std()
                    
                    if volatilities:
                        most_volatile = max(volatilities, key=volatilities.get)
                        least_volatile = min(volatilities, key=volatilities.get)
                        print(f"   • Most volatile timeframe: {most_volatile} (σ=${volatilities[most_volatile]:.2f})")
                        print(f"   • Least volatile timeframe: {least_volatile} (σ=${volatilities[least_volatile]:.2f})")
                
            else:
                print(f"❌ Failed to load data for {symbol}")
        
        print(f"\n{'='*60}")
        print("✨ Multi-timeframe analysis complete!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        
    finally:
        data_stream.close()
        print("👋 Done!")


if __name__ == "__main__":
    main()
