# Configuration System

## Overview

The Crypto Auto-Trader now features a comprehensive configuration system that centralizes all settings, allowing you to:

1. Configure application settings via environment variables or `.env` file
2. Set timeframes, symbols, and other trading parameters in one place
3. Override configuration via command-line arguments
4. Receive interactive prompts for missing required values

## Configuration Options

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `MODE` | Application mode | `data` | `data`, `backtest`, `live` |
| `SYMBOLS` | Trading symbols (comma-separated) | `BTC` | `BTC,ETH,ADA` |
| `TIMEFRAMES` | Analysis timeframes (comma-separated) | `1m,5m,15m,1h` | `5m,1h` |
| `HISTORY_COUNT` | Number of historical candles to load | `1000` | `500` |
| `MAX_CANDLES` | Maximum candles to store in memory | `2000` | `1000` |
| `CACHE_TTL` | Cache time-to-live in seconds | `60` | `30` |
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `INFO`, `WARNING` |
| `LOG_TO_FILE` | Whether to log to file | `true` | `true`, `false` |
| `API_KEY` | Kraken API key (live mode only) | - | `your-api-key` |
| `API_SECRET` | Kraken API secret (live mode only) | - | `your-api-secret` |

## Setting Up Configuration

### Method 1: Using a .env File

Create a file named `.env` in the project root:

```
# Application mode
MODE=data

# Symbols and timeframes
SYMBOLS=BTC,ETH,ADA
TIMEFRAMES=5m,1h

# Data settings
HISTORY_COUNT=500
MAX_CANDLES=1000
CACHE_TTL=30

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=true
```

### Method 2: Environment Variables

Set environment variables in your shell:

```bash
# Bash/Zsh
export MODE=data
export SYMBOLS=BTC,ETH
export TIMEFRAMES=5m,1h,4h

# Run the application
python main.py
```

### Method 3: Interactive Prompts

If required values are missing, the application will prompt for input:

```
⚙️  Enter MODE (backtest/data/live): data
💰 Enter SYMBOLS (comma-separated) (default: BTC): BTC,ETH
📊 Enter TIMEFRAMES (comma-separated) (default: 1m,5m,15m,1h): 5m,1h
```

## Command-Line Override

You can override the configured symbols by providing them as command-line arguments:

```bash
# Override with a single symbol
python main.py ETH

# Use configured symbols
python main.py
```

## Supported Values

### Modes
- `data`: Data analysis mode (no trading)
- `backtest`: Backtesting mode
- `live`: Live trading mode

### Timeframes
- `1m`: 1 minute
- `5m`: 5 minutes
- `15m`: 15 minutes
- `30m`: 30 minutes
- `1h`: 1 hour
- `4h`: 4 hours
- `1d`: 1 day

### Symbols
Supported symbols include: BTC, ETH, ADA, DOT, LINK, UNI, AAVE, MATIC, SOL, AVAX

Custom symbols will also work if they are supported by the exchange.

## Implementation Details

The configuration system uses:

1. **Python dotenv**: Loads variables from `.env` file
2. **Dataclass validation**: Ensures configuration integrity
3. **Interactive prompts**: User-friendly configuration
4. **Default values**: Sensible defaults for optional settings
5. **Command-line overrides**: Flexibility for testing

## Usage Example

```python
from config.config_loader import ConfigLoader

# Load configuration
config_loader = ConfigLoader()
config = config_loader.config

# Access configuration values
symbols = config.symbols
timeframes = config.timeframes
history_count = config.history_count

print(f"Analyzing {', '.join(symbols)} with timeframes: {', '.join(timeframes)}")
```

## Technical Notes

- Configuration is validated upon loading
- API credentials are only required for live mode
- Invalid timeframes or symbols will trigger warnings
- Command-line arguments take precedence over config values
- Use `DEFAULT_` class variables in `ConfigLoader` to change system defaults
