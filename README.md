# 🚀 Crypto Auto-Trader - Modular Trading System

## 🎯 Overview

A comprehensive, production-ready Python trading system for cryptocurrency exchanges with a modular architecture. The system supports both live trading and backtesting with enterprise-grade error handling, comprehensive logging, and fail-safe mechanisms.

## 🏗️ Architecture

The system is built with a modular architecture consisting of three main modules:

- **📊 DataIngestion**: Handles market data ingestion and price feeds
- **🧠 StrategyExecutor**: Manages trading strategies and signal generation  
- **💼 Trader**: Executes trades in both live and simulated environments

```
modules/
├── data_ingestion/     # Market data and price feeds
├── strategy_executor/  # Trading strategies and signals
└── trader/            # Live and simulated trading
    ├── kraken/        # Kraken exchange integration
    └── backtest/      # Portfolio simulation
shared/                # Shared components (auth, portfolio)
```

## 📦 Installation & Quick Start

```bash
pip install -r requirements.txt
python3 main.py
```

### Live Trading
```python
from modules.trader.trader_manager import TraderManager
from config.config_loader import TradingConfig

# Configure for live trading
config = TradingConfig(
    api_key="your_key", 
    api_secret="your_secret", 
    mode="live"
)

# Initialize trader manager
trader_manager = TraderManager(config)
portfolio = trader_manager.get_portfolio()
trader = trader_manager.get_trader()

# Execute trades
trader.market_buy("XXBTZEUR", Decimal("0.001"))
```

### Backtesting
```python
# Configure for backtesting
config = TradingConfig(mode="backtest", timeframe="5")
trader_manager = TraderManager(config)
portfolio = trader_manager.get_portfolio()

# Simulate trades
portfolio.execute_trade("GBP", Decimal("100"), "ETH", Decimal("0.05"))
```

---

## ✨ Key Features

- 🔥 **Complete API Coverage**: All 10 order types, advanced features, position management
- 🛡️ **Bulletproof Error Handling**: Retry logic, validation, comprehensive logging
- 🎯 **Production Ready**: Rate limiting, dead man's switch, session management
- 📊 **Real-time Trading**: Market data, order management, position tracking
- 🧪 **Backtesting**: Full portfolio simulation with historical tracking
- 🏗️ **Modular Design**: Extensible architecture for multiple strategies and exchanges
- 🔒 **Shared Components**: Reusable authentication and portfolio management

## 🔥 Complete Order Types & Trading Capabilities

### 💰 Market Orders
Execute immediately at best available price.

```python
# Market Buy
trader.market_buy("XXBTZEUR", Decimal("0.001"))

# Market Sell  
trader.market_sell("XETHZEUR", Decimal("0.01"))

# Advanced market order with custom parameters
trader.add_order(
    pair="XXBTZEUR",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    volume=Decimal("0.001"),
    user_ref=12345,
    client_order_id="my-market-buy-001"
)
```

### 📊 Limit Orders
Execute only at specified price or better.

```python
# Basic limit orders
trader.limit_buy("XXBTZEUR", Decimal("0.001"), Decimal("35000.00"))
trader.limit_sell("XETHZEUR", Decimal("0.01"), Decimal("2500.00"))

# Post-only limit order (maker only)
trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    price=Decimal("35000.00"),
    order_flags=[OrderFlags.POST]  # No taker fees
)

# Limit order with time restrictions
trader.limit_sell(
    pair="XETHZEUR",
    volume=Decimal("0.01"),
    price=Decimal("2500.00"),
    start_time=int(time.time() + 3600),  # Start in 1 hour
    expire_time=int(time.time() + 86400)  # Expire in 24 hours
)
```

### 🧊 Iceberg Orders
Large orders split into smaller visible chunks to hide true order size.

```python
trader.add_order(
    pair="XXBTZEUR",
    side=OrderSide.BUY,
    order_type=OrderType.ICEBERG,
    volume=Decimal("1.0"),  # Total volume
    price=Decimal("35000.00")
    # Only small portions visible in order book
)
```

### 🛑 Stop Loss Orders
Market orders triggered when price hits stop level.

```python
# Basic stop loss
trader.stop_loss_sell("XXBTZEUR", Decimal("0.001"), Decimal("30000.00"))

# Stop loss with index price trigger
trader.stop_loss_sell(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    stop_price=Decimal("30000.00"),
    trigger=TriggerType.INDEX  # Use index price instead of last
)

# Stop loss with reduce-only flag
trader.add_order(
    pair="XXBTZEUR",
    side=OrderSide.SELL,
    order_type=OrderType.STOP_LOSS,
    volume=Decimal("0.001"),
    price=Decimal("30000.00"),
    reduce_only=True  # Only reduce existing position
)
```

### 🎯 Take Profit Orders
Market orders triggered when price hits profit level.

```python
# Basic take profit
trader.take_profit_sell("XETHZEUR", Decimal("0.01"), Decimal("3000.00"))

# Take profit buy (for short positions)
trader.take_profit_buy("XXBTZEUR", Decimal("0.001"), Decimal("40000.00"))

# Advanced take profit with validation
trader.add_order(
    pair="XETHZEUR",
    side=OrderSide.SELL,
    order_type=OrderType.TAKE_PROFIT,
    volume=Decimal("0.01"),
    price=Decimal("3000.00"),
    validate=True,  # Validate without executing
    trigger=TriggerType.LAST
)
```

### 📈 Trailing Stop Orders
Stop loss that follows price at fixed distance.

```python
# Trailing stop sell
trader.add_order(
    pair="XXBTZEUR",
    side=OrderSide.SELL,
    order_type=OrderType.TRAILING_STOP,
    volume=Decimal("0.001"),
    price=Decimal("1000.00")  # Trail distance
)

# Trailing stop with percentage distance
trader.add_order(
    pair="XETHZEUR",
    side=OrderSide.SELL,
    order_type=OrderType.TRAILING_STOP,
    volume=Decimal("0.01"),
    price=Decimal("100.00")  # $100 trail distance
)
```

### 🎯 Stop Loss Limit Orders
Limit orders triggered when price hits stop level.

```python
trader.add_order(
    pair="XXBTZEUR",
    side=OrderSide.SELL,
    order_type=OrderType.STOP_LOSS_LIMIT,
    volume=Decimal("0.001"),
    price=Decimal("30000.00"),    # Stop trigger price
    price2=Decimal("29900.00")    # Limit order price
)
```

### 💎 Take Profit Limit Orders
Limit orders triggered when price hits profit level.

```python
trader.add_order(
    pair="XETHZEUR",
    side=OrderSide.SELL,
    order_type=OrderType.TAKE_PROFIT_LIMIT,
    volume=Decimal("0.01"),
    price=Decimal("3000.00"),     # Profit trigger price
    price2=Decimal("2990.00")     # Limit order price
)
```

### 📊 Trailing Stop Limit Orders
Trailing stop that places limit order when triggered.

```python
trader.add_order(
    pair="XXBTZEUR",
    side=OrderSide.SELL,
    order_type=OrderType.TRAILING_STOP_LIMIT,
    volume=Decimal("0.001"),
    price=Decimal("1000.00"),     # Trail distance
    price2=Decimal("100.00")      # Limit offset from trigger
)
```

### ⚖️ Settle Position Orders
Close position at market price.

```python
trader.add_order(
    pair="XXBTZEUR",
    side=OrderSide.SELL,
    order_type=OrderType.SETTLE_POSITION,
    volume=Decimal("0.001")  # Volume to close
)
```

---

## 🎛️ Advanced Trading Features

### 🔗 Conditional Close Orders
Automatically place orders when initial order fills.

```python
# Buy with automatic take profit
trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    price=Decimal("35000.00"),
    close_order_type=OrderType.TAKE_PROFIT,
    close_price=Decimal("40000.00")
)

# Buy with stop loss protection
trader.market_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    close_order_type=OrderType.STOP_LOSS,
    close_price=Decimal("30000.00")
)

# Complex conditional close with limit order
trader.limit_buy(
    pair="XETHZEUR",
    volume=Decimal("0.01"),
    price=Decimal("2000.00"),
    close_order_type=OrderType.TAKE_PROFIT_LIMIT,
    close_price=Decimal("2500.00"),    # Trigger price
    close_price2=Decimal("2490.00")    # Limit price
)
```

### ⚡ Leverage Trading
Trade with up to 5x leverage on supported pairs.

```python
# Leveraged long position
trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.01"),
    price=Decimal("35000.00"),
    leverage="3:1"  # 3x leverage
)

# Leveraged short position  
trader.limit_sell(
    pair="XETHZEUR", 
    volume=Decimal("0.1"),
    price=Decimal("2500.00"),
    leverage="2:1"  # 2x leverage
)

# Maximum leverage pairs:
# BTC/USD, BTC/EUR: up to 5x
# ETH/USD, ETH/EUR: up to 5x
# XRP/USD, XRP/EUR: up to 5x
# And 100+ other pairs with 2-5x leverage
```

### 🚩 Order Flags & Special Behavior

```python
# Post-only (maker only) orders
trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    price=Decimal("35000.00"),
    order_flags=[OrderFlags.POST]
)

# Prefer fees in base currency
trader.limit_sell(
    pair="XETHZEUR",
    volume=Decimal("0.01"),
    price=Decimal("2500.00"),
    order_flags=[OrderFlags.FCIB]
)

# Prefer fees in quote currency
trader.market_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    order_flags=[OrderFlags.FCIQ]
)

# Volume in quote currency
trader.market_buy(
    pair="XXBTZEUR",
    volume=Decimal("1000.00"),  # $1000 worth
    order_flags=[OrderFlags.VIQC]
)

# Disable market price protection
trader.market_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    order_flags=[OrderFlags.NOMPP]
)

# Multiple flags
trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    price=Decimal("35000.00"),
    order_flags=[OrderFlags.POST, OrderFlags.FCIB]
)
```

### ⏰ Time Management Features

```python
# Scheduled orders
future_time = int(time.time() + 3600)  # 1 hour from now
trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    price=Decimal("35000.00"),
    start_time=future_time
)

# Expiring orders
expire_time = int(time.time() + 86400)  # 24 hours from now
trader.limit_sell(
    pair="XETHZEUR",
    volume=Decimal("0.01"),
    price=Decimal("2500.00"),
    expire_time=expire_time
)

# Time in force
trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    price=Decimal("35000.00"),
    time_in_force="IOC"  # Immediate or Cancel
)
```

---

## 🎛️ Order Management & Control

### 📋 Query Orders & Positions

```python
# Get open orders
open_orders = trader.get_open_orders(trades=True)
print(f"Open orders: {len(open_orders.get('open', {}))}")

# Get recent closed orders
closed_orders = trader.get_closed_orders(
    trades=True,
    start=1640995200,  # Unix timestamp
    end=1641081600,
    without_count=True  # Faster for many orders
)

# Query specific orders
order_info = trader.query_orders_info(
    order_ids=["ORDER_ID_1", "ORDER_ID_2"],
    trades=True
)

# Get open positions with P&L
positions = trader.get_open_positions(do_calcs=True)

# Get trade history
trades = trader.get_trades_history(
    trade_type="all",
    start=1640995200,
    end=1641081600
)
```

### 🗑️ Cancel Orders

```python
# Cancel specific order
trader.cancel_order(order_id="ORDER_TX_ID")

# Cancel by client order ID
trader.cancel_order(client_order_id="my-order-001")

# Cancel by user reference
trader.cancel_order(user_ref=12345)

# Cancel all orders
trader.cancel_all_orders()
```

### ⏰ Dead Man's Switch (Safety Feature)

```python
# Cancel all orders if no heartbeat for 60 seconds
trader.cancel_all_orders_after(timeout=60)

# Cancel all orders if no heartbeat for 5 minutes
trader.cancel_all_orders_after(timeout=300)

# Disable dead man's switch
trader.cancel_all_orders_after(timeout=0)
```

---

## 📊 Account & Trading Information

### 💼 Account Data

```python
# Get trade volume and fee information
volume_info = trader.get_trade_volume(
    pairs=["XXBTZEUR", "XETHZEUR"]
)

# Get ledger information
ledgers = trader.get_ledgers(
    asset="XBT",
    ledger_type="trade",
    start=1640995200,
    end=1641081600
)

# Query specific ledger entries
ledger_info = trader.query_ledgers_info(
    ledger_ids=["LEDGER_ID_1", "LEDGER_ID_2"]
)
```

### 📈 Trading Pairs & Market Data

All major cryptocurrency pairs supported with leverage:

**Maximum 5x Leverage:**
- BTC/USD, BTC/EUR, BTC/GBP, BTC/CAD, BTC/AUD, BTC/CHF
- ETH/USD, ETH/EUR, ETH/GBP, ETH/CAD, ETH/AUD, ETH/CHF
- XRP/USD, XRP/EUR, XRP/GBP, XRP/CAD, XRP/AUD
- DOGE/USD with up to 5x leverage

**Up to 4x Leverage:**
- MANA/EUR, MANA/USD
- USDC/CAD, USDC/CHF
- Many stablecoin pairs

**Up to 3x Leverage:**
- 100+ pairs including:
- ADA, DOT, SOL, MATIC, LINK, UNI, AAVE, COMP
- LTC, BCH, ETC, XMR, ZEC
- And many more altcoins

**2x Leverage Available:**
- Nearly all supported trading pairs

---

## 🛡️ Security & Risk Management

### ✅ Input Validation

```python
# All parameters are validated before API calls
try:
    trader.market_buy("", Decimal("0.001"))  # Empty pair
except ValueError as e:
    print(f"Validation error: {e}")

try:
    trader.limit_buy("XXBTZEUR", Decimal("-0.001"), Decimal("35000"))  # Negative volume
except ValueError as e:
    print(f"Validation error: {e}")
```

### 🔄 Retry Logic & Error Handling

```python
# Automatic retries with exponential backoff
trader = KrakenTrader(
    auth=auth,
    timeout=30,        # Request timeout
    max_retries=3      # Retry failed requests
)

# Comprehensive error handling
try:
    result = trader.market_buy("XXBTZEUR", Decimal("0.001"))
except Exception as e:
    logger.error(f"Trading error: {e}")
    # Handle error appropriately
```

### 🔐 Order Validation

```python
# Validate orders without placing them
result = trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    price=Decimal("35000.00"),
    validate=True  # Only validates, doesn't execute
)
print(f"Order validation: {result}")
```

---

## 🎯 Trading Strategies & Examples

### 📈 Dollar Cost Averaging (DCA)

```python
def dca_strategy(trader, pair, amount_usd, frequency_hours):
    """Implement dollar cost averaging strategy."""
    
    # Calculate volume in quote currency
    volume = Decimal(str(amount_usd))
    
    # Place market buy order with volume in USD
    result = trader.market_buy(
        pair=pair,
        volume=volume,
        order_flags=[OrderFlags.VIQC],  # Volume in quote currency
        client_order_id=f"dca-{int(time.time())}"
    )
    
    logger.info(f"DCA order placed: {result}")
    return result

# Execute DCA
dca_strategy(trader, "XXBTZUSD", 100, 24)  # $100 every 24 hours
```

### 🎯 OCO (One-Cancels-Other) Strategy

```python
def place_oco_orders(trader, pair, volume, buy_price, sell_price):
    """Place OCO-style orders using user references."""
    
    user_ref = int(time.time())
    
    # Place buy order
    buy_result = trader.limit_buy(
        pair=pair,
        volume=volume,
        price=buy_price,
        user_ref=user_ref + 1,
        client_order_id=f"oco-buy-{user_ref}"
    )
    
    # Place sell order
    sell_result = trader.limit_sell(
        pair=pair,
        volume=volume,
        price=sell_price,
        user_ref=user_ref + 2,
        client_order_id=f"oco-sell-{user_ref}"
    )
    
    return buy_result, sell_result

# Custom logic needed to cancel the other order when one fills
```

### 🛡️ Risk-Managed Position

```python
def open_protected_position(trader, pair, volume, entry_price, stop_loss, take_profit):
    """Open position with automatic stop loss and take profit."""
    
    # Place main order with conditional close
    result = trader.limit_buy(
        pair=pair,
        volume=volume,
        price=entry_price,
        close_order_type=OrderType.STOP_LOSS,
        close_price=stop_loss,
        client_order_id=f"protected-{int(time.time())}"
    )
    
    # Manually place take profit (since only one conditional close allowed)
    if result.get('txid'):
        tp_result = trader.take_profit_sell(
            pair=pair,
            volume=volume,
            profit_price=take_profit,
            client_order_id=f"tp-{int(time.time())}"
        )
        return result, tp_result
    
    return result, None

# Example usage
entry_result, tp_result = open_protected_position(
    trader=trader,
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    entry_price=Decimal("35000.00"),
    stop_loss=Decimal("33000.00"),
    take_profit=Decimal("38000.00")
)
```

### 📊 Grid Trading Strategy

```python
def create_grid_orders(trader, pair, base_price, grid_size, num_levels, volume_per_level):
    """Create grid trading orders."""
    
    orders = []
    
    # Create buy orders below current price
    for i in range(1, num_levels + 1):
        buy_price = base_price - (Decimal(str(grid_size)) * i)
        result = trader.limit_buy(
            pair=pair,
            volume=volume_per_level,
            price=buy_price,
            user_ref=1000 + i,
            client_order_id=f"grid-buy-{i}"
        )
        orders.append(result)
    
    # Create sell orders above current price
    for i in range(1, num_levels + 1):
        sell_price = base_price + (Decimal(str(grid_size)) * i)
        result = trader.limit_sell(
            pair=pair,
            volume=volume_per_level,
            price=sell_price,
            user_ref=2000 + i,
            client_order_id=f"grid-sell-{i}"
        )
        orders.append(result)
    
    return orders

# Create 5-level grid around $35,000
grid_orders = create_grid_orders(
    trader=trader,
    pair="XXBTZUSD",
    base_price=Decimal("35000.00"),
    grid_size=500,  # $500 between levels
    num_levels=5,
    volume_per_level=Decimal("0.001")
)
```

---

## 🔧 Configuration & Best Practices

### ⚙️ Initialization Options

```python
# Basic initialization
trader = KrakenTrader(auth)

# Advanced configuration
trader = KrakenTrader(
    auth=auth,
    timeout=60,        # Longer timeout for slow connections
    max_retries=5      # More retries for unstable networks
)
```

### 📝 Logging Configuration

```python
import logging

# Enable debug logging
logging.getLogger("kraken.trade").setLevel(logging.DEBUG)

# All operations logged with levels:
# INFO: Successful operations
# WARNING: Retries and recoverable errors
# ERROR: Failed operations  
# DEBUG: Detailed request/response info
```

### 🏷️ Order Tracking

```python
# Use client order IDs for tracking
client_id = f"strategy-{strategy_name}-{int(time.time())}"
result = trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    price=Decimal("35000.00"),
    client_order_id=client_id
)

# Later query by client ID
orders = trader.get_open_orders()
for order_id, order_info in orders.get('open', {}).items():
    if order_info.get('userref') == client_id:
        print(f"Found our order: {order_id}")
```

### 🔒 Resource Management

```python
try:
    # Your trading logic
    trader = KrakenTrader(auth)
    
    # ... trading operations ...
    
finally:
    # Always close the session
    trader.close()
```

---

## 🚨 Important Notes & Disclaimers

### ⚠️ Risk Warnings

- **High Risk**: Cryptocurrency trading involves substantial risk of loss
- **Leverage Risk**: Leveraged positions can be liquidated quickly
- **API Limits**: Respect rate limits to avoid temporary bans
- **Order Validation**: Always validate orders in paper trading first

### 🔐 Security Best Practices

- **API Permissions**: Grant only necessary permissions to API keys
- **Credential Storage**: Never hardcode credentials in source code
- **Network Security**: Use secure connections and validate certificates
- **Dead Man's Switch**: Always set timeouts for automated trading

### 📊 Trading Pair Information

- **Minimum Orders**: Check minimum order sizes for each pair
- **Price Precision**: Different pairs have different price/volume precision
- **Trading Hours**: Most crypto markets are 24/7, but some features may have maintenance windows
- **Leverage Availability**: Not all pairs support all leverage levels

### 🔄 Error Handling

- **Network Errors**: Implement proper retry logic for network issues
- **API Errors**: Handle various API error codes appropriately
- **Order Validation**: Always validate parameters before submission
- **Rate Limiting**: Implement delays to respect API rate limits

---

## 📚 Complete API Reference

For detailed parameter information, error codes, and advanced features, see the comprehensive documentation in `docs/TRADING_MODULE.md` and examples in `examples/trading_examples.py`.

The KrakenTrader class provides access to every aspect of Kraken's trading functionality while maintaining the highest standards of safety, reliability, and ease of use for professional cryptocurrency trading.