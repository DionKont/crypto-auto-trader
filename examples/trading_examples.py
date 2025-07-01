#!/usr/bin/env python3
"""
Kraken Trading Module Example

This script demonstrates the comprehensive trading functionality of the KrakenTrader class.
It includes examples of all order types, query methods, and advanced features.

WARNING: This script contains real trading examples. Make sure to use it carefully
and understand each operation before running with real API credentials.
"""

from decimal import Decimal
from kraken.auth import KrakenAuth
from kraken.trade import KrakenTrader, OrderType, OrderSide, OrderFlags, TriggerType
from logger import Logger

def main():
    """Demonstrate KrakenTrader functionality."""
    logger = Logger("trading_example", log_to_file=True)
    
    # IMPORTANT: Use demo/paper trading credentials for testing
    # Never run this with real trading credentials without understanding the implications
    api_key = "your_api_key_here"
    api_secret = "your_api_secret_here"
    
    if api_key == "your_api_key_here":
        logger.warning("⚠️  Please set your API credentials before running this example")
        return
    
    try:
        # Initialize authentication and trader
        auth = KrakenAuth(api_key, api_secret)
        trader = KrakenTrader(auth, timeout=30, max_retries=3)
        
        logger.info("🚀 Starting Kraken trading examples...")
        
        # =================================================================
        # BASIC ORDER EXAMPLES
        # =================================================================
        
        # Example 1: Market Orders
        logger.info("📈 Example 1: Market Orders")
        
        # Validate a market buy order (doesn't execute)
        market_buy_validation = trader.market_buy(
            pair="XXBTZEUR",
            volume=Decimal("0.001"),
            validate=True,  # Only validates, doesn't execute
            user_ref=12345
        )
        logger.info(f"Market buy validation result: {market_buy_validation}")
        
        # Example 2: Limit Orders
        logger.info("📊 Example 2: Limit Orders")
        
        # Place a limit sell order with post-only flag
        limit_sell_result = trader.limit_sell(
            pair="XETHZEUR",
            volume=Decimal("0.01"),
            price=Decimal("2000.00"),
            order_flags=[OrderFlags.POST],  # Post-only order
            client_order_id="my-limit-sell-001",
            validate=True  # Only validate for this example
        )
        logger.info(f"Limit sell result: {limit_sell_result}")
        
        # Example 3: Stop Loss Orders
        logger.info("🛑 Example 3: Stop Loss Orders")
        
        # Stop loss with trigger on last price
        stop_loss_result = trader.stop_loss_sell(
            pair="XXBTZEUR",
            volume=Decimal("0.005"),
            stop_price=Decimal("30000.00"),
            trigger=TriggerType.LAST,
            validate=True
        )
        logger.info(f"Stop loss result: {stop_loss_result}")
        
        # Example 4: Take Profit Orders
        logger.info("🎯 Example 4: Take Profit Orders")
        
        take_profit_result = trader.take_profit_sell(
            pair="XETHZEUR",
            volume=Decimal("0.02"),
            profit_price=Decimal("3000.00"),
            validate=True
        )
        logger.info(f"Take profit result: {take_profit_result}")
        
        # Example 5: Advanced Order with Conditional Close
        logger.info("🔗 Example 5: Advanced Order with Conditional Close")
        
        advanced_order_result = trader.limit_buy(
            pair="XXBTZEUR",
            volume=Decimal("0.001"),
            price=Decimal("35000.00"),
            close_order_type=OrderType.TAKE_PROFIT,
            close_price=Decimal("40000.00"),
            user_ref=54321,
            validate=True
        )
        logger.info(f"Advanced order result: {advanced_order_result}")
        
        # =================================================================
        # QUERY EXAMPLES
        # =================================================================
        
        # Example 6: Query Open Orders
        logger.info("📋 Example 6: Query Open Orders")
        
        open_orders = trader.get_open_orders(trades=True)
        logger.info(f"Open orders count: {len(open_orders.get('open', {}))}")
        
        # Example 7: Query Closed Orders
        logger.info("📚 Example 7: Query Closed Orders")
        
        closed_orders = trader.get_closed_orders(
            trades=True,
            close_time="both",
            offset=0
        )
        logger.info(f"Closed orders count: {len(closed_orders.get('closed', {}))}")
        
        # Example 8: Get Trade History
        logger.info("📊 Example 8: Get Trade History")
        
        trades_history = trader.get_trades_history(
            trade_type="all",
            trades=True
        )
        logger.info(f"Trades in history: {len(trades_history.get('trades', {}))}")
        
        # Example 9: Get Open Positions
        logger.info("📍 Example 9: Get Open Positions")
        
        open_positions = trader.get_open_positions(do_calcs=True)
        logger.info(f"Open positions: {len(open_positions)}")
        
        # Example 10: Get Trade Volume
        logger.info("📈 Example 10: Get Trade Volume")
        
        trade_volume = trader.get_trade_volume(pairs=["XXBTZEUR", "XETHZEUR"])
        logger.info(f"Trade volume info: {trade_volume.get('currency', 'N/A')}")
        
        # Example 11: Get Ledger Information
        logger.info("📖 Example 11: Get Ledger Information")
        
        ledgers = trader.get_ledgers(
            ledger_type="trade",
            without_count=True
        )
        logger.info(f"Ledger entries: {len(ledgers.get('ledger', {}))}")
        
        # =================================================================
        # ORDER MANAGEMENT EXAMPLES
        # =================================================================
        
        # Example 12: Dead Man's Switch
        logger.info("⏰ Example 12: Dead Man's Switch")
        
        # Set dead man's switch for 60 seconds
        dms_result = trader.cancel_all_orders_after(timeout=60)
        logger.info(f"Dead man's switch set: {dms_result}")
        
        # Disable dead man's switch
        dms_disable = trader.cancel_all_orders_after(timeout=0)
        logger.info(f"Dead man's switch disabled: {dms_disable}")
        
        # =================================================================
        # ADVANCED TRADING STRATEGIES EXAMPLES
        # =================================================================
        
        logger.info("🎯 Example 13: OCO (One-Cancels-Other) Strategy")
        
        # Simulate OCO by placing orders with specific user references
        # This would require custom logic to cancel the other order when one fills
        
        # Buy limit order
        oco_buy = trader.limit_buy(
            pair="XXBTZEUR",
            volume=Decimal("0.001"),
            price=Decimal("32000.00"),
            user_ref=99001,
            client_order_id="oco-buy-001",
            validate=True
        )
        
        # Sell limit order
        oco_sell = trader.limit_sell(
            pair="XXBTZEUR",
            volume=Decimal("0.001"),
            price=Decimal("38000.00"),
            user_ref=99002,
            client_order_id="oco-sell-001",
            validate=True
        )
        
        logger.info("OCO orders validated successfully")
        
        logger.info("✅ All examples completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Example failed: {e}")
        raise
    finally:
        # Always close the trading session
        if 'trader' in locals():
            trader.close()

def demonstrate_error_handling():
    """Demonstrate the robust error handling capabilities."""
    logger = Logger("error_handling_demo", log_to_file=True)
    
    try:
        # Initialize with invalid credentials to show error handling
        auth = KrakenAuth("invalid_key", "aW52YWxpZF9zZWNyZXQ=")  # Invalid base64 secret
        trader = KrakenTrader(auth)
        
        # This will fail and demonstrate error handling
        trader.market_buy("INVALID_PAIR", Decimal("0.001"))
        
    except Exception as e:
        logger.info(f"✅ Error handling working correctly: {e}")

def demonstrate_input_validation():
    """Demonstrate input validation features."""
    logger = Logger("validation_demo", log_to_file=True)
    
    try:
        auth = KrakenAuth("test_key", "dGVzdF9zZWNyZXQ=")
        trader = KrakenTrader(auth)
        
        # These will raise ValueError due to validation
        test_cases = [
            lambda: trader.add_order("", OrderSide.BUY, OrderType.MARKET, "0.001"),  # Empty pair
            lambda: trader.add_order("XXBTZEUR", "invalid_side", OrderType.MARKET, "0.001"),  # Invalid side
            lambda: trader.add_order("XXBTZEUR", OrderSide.BUY, "invalid_type", "0.001"),  # Invalid order type
            lambda: trader.add_order("XXBTZEUR", OrderSide.BUY, OrderType.MARKET, "-0.001"),  # Negative volume
            lambda: trader.cancel_order(),  # No order identifier
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                test_case()
                logger.warning(f"❌ Test case {i} should have failed but didn't")
            except ValueError as e:
                logger.info(f"✅ Test case {i} validation working: {e}")
            except Exception as e:
                logger.info(f"✅ Test case {i} caught other error: {type(e).__name__}")
                
    except Exception as e:
        logger.error(f"❌ Validation demo failed: {e}")

if __name__ == "__main__":
    print("🔧 Kraken Trading Module Examples")
    print("=" * 50)
    print()
    print("⚠️  WARNING: This script contains real trading examples!")
    print("⚠️  Make sure to understand each operation before running with real credentials.")
    print("⚠️  Consider using Kraken's sandbox/demo environment for testing.")
    print()
    
    # Run demonstrations
    try:
        main()
        print("\n" + "=" * 50)
        print("🧪 Running error handling demonstration...")
        demonstrate_error_handling()
        
        print("\n" + "=" * 50)
        print("✅ Running input validation demonstration...")
        demonstrate_input_validation()
        
    except Exception as e:
        print(f"❌ Examples failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ All demonstrations completed!")
