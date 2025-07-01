# Kraken Trading Module Documentation

## Overview

The `KrakenTrader` class provides a comprehensive, production-ready interface to the Kraken cryptocurrency exchange API with full trading functionality. It supports all Kraken order types, advanced features, and includes robust error handling, logging, and validation.

## Features

### ✅ Complete API Coverage
- **All Order Types**: Market, Limit, Iceberg, Stop-Loss, Take-Profit, Trailing-Stop, Stop-Loss-Limit, Take-Profit-Limit, Trailing-Stop-Limit, Settle-Position
- **Order Management**: Place, Cancel, Amend, Query orders
- **Position Management**: Open positions, trade history, ledger information
- **Advanced Features**: Conditional close orders, leverage, dead man's switch
- **Account Information**: Trade volume, fees, balances

### 🛡️ Robust & Fail-Safe
- **Comprehensive Error Handling**: Network errors, API errors, validation errors
- **Retry Logic**: Exponential backoff for failed requests
- **Input Validation**: Validates all parameters before sending requests
- **Rate Limiting Awareness**: Built-in delays and retry mechanisms
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

### 🚀 Developer Friendly
- **Type Hints**: Full type annotations for better IDE support
- **Enums**: Type-safe enums for order types, sides, flags, etc.
- **Helper Methods**: Convenient shortcuts for common operations
- **Documentation**: Comprehensive docstrings and examples

## Installation & Setup

```python
from kraken.auth import KrakenAuth
from kraken.trade import KrakenTrader

# Initialize authentication
auth = KrakenAuth(api_key="your_api_key", api_secret="your_api_secret")

# Initialize trader
trader = KrakenTrader(auth, timeout=30, max_retries=3)
```

## Basic Usage Examples

### Market Orders

```python
from decimal import Decimal
from kraken.trade import OrderSide, OrderType

# Market buy
result = trader.market_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001")
)

# Market sell
result = trader.market_sell(
    pair="XETHZEUR", 
    volume=Decimal("0.01")
)
```

### Limit Orders

```python
# Limit buy
result = trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    price=Decimal("35000.00")
)

# Limit sell with post-only flag
result = trader.limit_sell(
    pair="XETHZEUR",
    volume=Decimal("0.01"),
    price=Decimal("2500.00"),
    order_flags=[OrderFlags.POST]
)
```

### Stop Loss & Take Profit

```python
# Stop loss sell
result = trader.stop_loss_sell(
    pair="XXBTZEUR",
    volume=Decimal("0.005"),
    stop_price=Decimal("30000.00"),
    trigger=TriggerType.LAST
)

# Take profit sell
result = trader.take_profit_sell(
    pair="XETHZEUR",
    volume=Decimal("0.02"),
    profit_price=Decimal("3000.00")
)
```

## Advanced Features

### Conditional Close Orders

```python
# Buy with automatic take profit
result = trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    price=Decimal("35000.00"),
    close_order_type=OrderType.TAKE_PROFIT,
    close_price=Decimal("40000.00")
)
```

### Order Validation

```python
# Validate order without placing it
result = trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    price=Decimal("35000.00"),
    validate=True  # Only validates, doesn't execute
)
```

### Dead Man's Switch

```python
# Cancel all orders after 60 seconds if no heartbeat
trader.cancel_all_orders_after(timeout=60)

# Disable dead man's switch
trader.cancel_all_orders_after(timeout=0)
```

## Order Management

### Query Orders

```python
# Get open orders
open_orders = trader.get_open_orders(trades=True)

# Get closed orders with pagination
closed_orders = trader.get_closed_orders(
    trades=True,
    start=1640995200,  # Unix timestamp
    end=1641081600,
    offset=0
)

# Query specific orders
order_info = trader.query_orders_info(
    order_ids=["ORDER_ID_1", "ORDER_ID_2"],
    trades=True
)
```

### Cancel Orders

```python
# Cancel specific order
trader.cancel_order(order_id="ORDER_ID")

# Cancel by client order ID
trader.cancel_order(client_order_id="my-order-001")

# Cancel all orders
trader.cancel_all_orders()
```

## Position & History Management

### Open Positions

```python
# Get open positions with P&L calculations
positions = trader.get_open_positions(do_calcs=True)

# Get specific positions
positions = trader.get_open_positions(
    transaction_ids=["TXN_ID_1", "TXN_ID_2"]
)
```

### Trade History

```python
# Get all trades
trades = trader.get_trades_history(
    trade_type="all",
    trades=True
)

# Get trades for a specific period
trades = trader.get_trades_history(
    start=1640995200,
    end=1641081600,
    offset=0
)
```

### Account Information

```python
# Get trade volume and fees
volume_info = trader.get_trade_volume(
    pairs=["XXBTZEUR", "XETHZEUR"]
)

# Get ledger information
ledgers = trader.get_ledgers(
    asset="XBT",
    ledger_type="trade"
)
```

## Error Handling

The trader includes comprehensive error handling:

```python
try:
    result = trader.market_buy("XXBTZEUR", Decimal("0.001"))
except ValueError as e:
    # Input validation error
    print(f"Invalid input: {e}")
except Exception as e:
    # API or network error
    print(f"Trading error: {e}")
```

## Order Types Reference

### Supported Order Types
- `MARKET`: Execute immediately at best available price
- `LIMIT`: Execute only at specified price or better
- `ICEBERG`: Large order split into smaller visible chunks
- `STOP_LOSS`: Market order triggered when price hits stop level
- `TAKE_PROFIT`: Market order triggered when price hits profit level
- `TRAILING_STOP`: Stop loss that follows price at fixed distance
- `STOP_LOSS_LIMIT`: Limit order triggered when price hits stop level
- `TAKE_PROFIT_LIMIT`: Limit order triggered when price hits profit level
- `TRAILING_STOP_LIMIT`: Trailing stop that places limit order when triggered
- `SETTLE_POSITION`: Close position at market price

### Order Flags
- `POST`: Post-only order (maker only, no taker fees)
- `FCIB`: Prefer fee in base currency
- `FCIQ`: Prefer fee in quote currency  
- `NOMPP`: Disable market price protection
- `VIQC`: Order volume in quote currency

### Trigger Types
- `LAST`: Trigger on last traded price (default)
- `INDEX`: Trigger on index price

## Configuration Options

```python
trader = KrakenTrader(
    auth=auth,
    timeout=30,        # Request timeout in seconds
    max_retries=3      # Maximum retry attempts
)
```

## Logging

The trader provides comprehensive logging:

```python
import logging

# Set logging level
logging.getLogger("kraken.trade").setLevel(logging.DEBUG)

# All operations are logged with appropriate levels:
# - INFO: Successful operations
# - WARNING: Retries and recoverable errors  
# - ERROR: Failed operations
# - DEBUG: Detailed request/response information
```

## Best Practices

### 1. Always Use Validation First
```python
# Validate before placing real orders
result = trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    price=Decimal("35000.00"),
    validate=True
)
```

### 2. Use Client Order IDs
```python
# Track orders with custom IDs
result = trader.limit_buy(
    pair="XXBTZEUR",
    volume=Decimal("0.001"),
    price=Decimal("35000.00"),
    client_order_id="strategy-1-buy-001"
)
```

### 3. Handle Errors Appropriately
```python
try:
    result = trader.market_buy("XXBTZEUR", Decimal("0.001"))
except Exception as e:
    logger.error(f"Order failed: {e}")
    # Implement appropriate error handling strategy
```

### 4. Use Dead Man's Switch for Safety
```python
# Set safety timeout
trader.cancel_all_orders_after(timeout=300)  # 5 minutes
```

### 5. Clean Up Resources
```python
try:
    # Your trading logic here
    pass
finally:
    trader.close()  # Close HTTP session
```

## Security Considerations

1. **API Permissions**: Ensure your API key has only necessary permissions
2. **Credential Storage**: Store credentials securely, never in source code
3. **Network Security**: Use HTTPS and validate certificates
4. **Rate Limiting**: Respect API rate limits to avoid bans
5. **Error Logging**: Be careful not to log sensitive information

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify API key and secret are correct
   - Check API key permissions
   - Ensure proper base64 encoding of secret

2. **Order Rejected**
   - Check minimum order sizes
   - Verify account balance
   - Validate order parameters

3. **Network Errors**
   - Check internet connectivity
   - Verify Kraken API status
   - Increase timeout if needed

4. **Rate Limiting**
   - Reduce request frequency
   - Implement proper delays
   - Use bulk operations when possible

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.getLogger("kraken.trade").setLevel(logging.DEBUG)
```

## API Reference

For complete API reference, see the docstrings in the `KrakenTrader` class. Each method includes:
- Parameter descriptions
- Return value documentation  
- Exception information
- Usage examples

## Examples

See `examples/trading_examples.py` for comprehensive usage examples including:
- All order types
- Advanced features
- Error handling
- Input validation
- Real-world trading strategies

## Support

For issues or questions:
1. Check the logs for detailed error information
2. Verify API credentials and permissions
3. Consult Kraken's official API documentation
4. Review the examples and test your setup
