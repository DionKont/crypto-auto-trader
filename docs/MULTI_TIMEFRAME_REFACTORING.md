# Multi-Timeframe Data Ingestion Refactoring

## Overview

The DataStream class has been refactored to support multiple timeframes simultaneously, allowing traders to analyze crypto data across different time horizons (1m, 5m, 15m, 1h) within a single application instance.

## Key Changes

### 1. DataStream Class Enhancements

#### New Timeframe Support
```python
# Supported timeframes mapping: user_friendly -> kraken_interval_minutes
TIMEFRAMES = {
    '1m': 1,     # 1 minute
    '5m': 5,     # 5 minutes  
    '15m': 15,   # 15 minutes
    '1h': 60     # 1 hour
}
```

#### Updated Data Storage
- **Before**: `Dict[str, pl.DataFrame]` - symbol -> DataFrame
- **After**: `Dict[tuple, pl.DataFrame]` - (symbol, timeframe) -> DataFrame

This allows storing multiple timeframes for the same symbol simultaneously.

#### Enhanced Methods

**`load_symbol()` - New Signature**
```python
def load_symbol(self, symbol: str, timeframes: List[str] = None, history_count: int = 200) -> bool
```

- `timeframes`: List of timeframes to load (e.g., `['1m', '5m', '15m', '1h']`)
- If `None`, loads all supported timeframes
- Returns `True` if at least one timeframe loads successfully

**`get_data()` - Updated Signature** 
```python
def get_data(self, symbol: str, timeframe: str = '1m') -> Optional[pl.DataFrame]
```

- Now requires specifying timeframe
- Defaults to '1m' for backward compatibility

**`get_latest_candle()` - Updated Signature**
```python
def get_latest_candle(self, symbol: str, timeframe: str = '1m') -> Optional[Dict]
```

- Now requires specifying timeframe
- Defaults to '1m' for backward compatibility

**New Methods Added**
```python
def get_all_data(self, symbol: str) -> Dict[str, pl.DataFrame]
def get_loaded_timeframes(self, symbol: str) -> List[str]
```

### 2. Updated Callback System

**Data Callbacks** now receive three parameters:
```python
callback(symbol: str, timeframe: str, dataframe: pl.DataFrame)
```

### 3. Main Application Updates

The `main.py` has been updated to demonstrate multi-timeframe functionality:

```python
# Define timeframes to load
timeframes = ['1m', '5m', '15m', '1h']

# Load data for multiple timeframes
if data_stream.load_symbol(symbol, timeframes=timeframes, history_count=1000):
    # Display summary for each timeframe
    for timeframe in timeframes:
        df = data_stream.get_data(symbol, timeframe)
        latest_candle = data_stream.get_latest_candle(symbol, timeframe)
        # ... display logic
```

## Usage Examples

### Basic Multi-Timeframe Loading
```python
from utils.data_stream import DataStream

data_stream = DataStream()

# Load BTC data for multiple timeframes
timeframes = ['1m', '5m', '15m', '1h']
if data_stream.load_symbol('BTC', timeframes=timeframes):
    
    # Access specific timeframe data
    df_1m = data_stream.get_data('BTC', '1m')
    df_1h = data_stream.get_data('BTC', '1h')
    
    # Get latest candle for specific timeframe
    latest_1m = data_stream.get_latest_candle('BTC', '1m')
    latest_1h = data_stream.get_latest_candle('BTC', '1h')
    
    # Get all timeframes at once
    all_data = data_stream.get_all_data('BTC')
    for timeframe, df in all_data.items():
        print(f"{timeframe}: {len(df)} candles")

data_stream.close()
```

### Selective Timeframe Loading
```python
# Load only specific timeframes
data_stream.load_symbol('ETH', timeframes=['5m', '1h'])

# Check which timeframes were loaded
loaded = data_stream.get_loaded_timeframes('ETH')
print(f"Loaded timeframes: {loaded}")  # ['5m', '1h']
```

### Multi-Symbol, Multi-Timeframe Analysis
```python
symbols = ['BTC', 'ETH', 'ADA']
timeframes = ['15m', '1h']

for symbol in symbols:
    if data_stream.load_symbol(symbol, timeframes=timeframes):
        for timeframe in timeframes:
            df = data_stream.get_data(symbol, timeframe)
            latest = data_stream.get_latest_candle(symbol, timeframe)
            
            print(f"{symbol} {timeframe}: ${latest['close']:.2f}")
```

## API Mapping

The Kraken API timeframe intervals (in minutes) map to user-friendly names:

| User Format | Kraken Interval | Description |
|-------------|----------------|-------------|
| `'1m'`      | 1             | 1 minute    |
| `'5m'`      | 5             | 5 minutes   |
| `'15m'`     | 15            | 15 minutes  |
| `'1h'`      | 60            | 1 hour      |

Additional Kraken intervals available but not currently included:
- 30 minutes (30)
- 4 hours (240) 
- 1 day (1440)
- 1 week (10080)
- 15 days (21600)

## Backward Compatibility

The refactored code maintains backward compatibility:

- `get_data(symbol)` still works (defaults to '1m')
- `get_latest_candle(symbol)` still works (defaults to '1m')
- Existing callback signatures will receive an extra `timeframe` parameter

## Performance Considerations

- Each timeframe requires a separate API call
- Memory usage scales with number of symbols × timeframes × history_count
- WebSocket updates currently only support 1-minute timeframe
- Larger timeframes (15m, 1h) provide longer historical ranges for the same candle count

## Error Handling

- Invalid timeframes are filtered out with warnings
- If no valid timeframes are specified, `load_symbol()` returns `False`
- Individual timeframe failures don't prevent other timeframes from loading
- Success is determined by at least one timeframe loading successfully

## Testing

Run the updated application:
```bash
python main.py BTC
```

Run the comprehensive example:
```bash
python example_multi_timeframe.py ETH
```

This refactoring enables sophisticated multi-timeframe trading strategies while maintaining the simplicity and reliability of the original design.
