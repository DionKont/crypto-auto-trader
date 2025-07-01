# main.py

from config.config_loader import ConfigLoader
from logger import Logger
from utils.portfolio_factory import PortfolioFactory

def main():
    """Main entry point for the crypto auto-trader."""
    logger = Logger("main", log_to_file=True)
    
    try:
        # Initialize configuration
        config_loader = ConfigLoader(interactive=True)
        
        logger.info("🚀 Crypto Auto-Trader starting...")
        logger.info(f"📊 Trading mode: {config_loader.config.mode}")
        
        if config_loader.config.timeframe:
            logger.info(f"⏱️  Timeframe: {config_loader.config.timeframe} minutes")
        
        # Validate API credentials
        if config_loader.validate_api_credentials():
            logger.info("🔐 API credentials validation passed")
            
            # Create the appropriate portfolio
            try:
                portfolio = PortfolioFactory.create_portfolio(config_loader.config)
                
                if config_loader.config.mode == "live":
                    logger.info("💰 Live portfolio initialized")
                else:
                    logger.info("📊 Simulated portfolio initialized for backtesting")
                
                # Simple balance check to verify portfolio is working
                try:
                    summary = portfolio.get_portfolio_summary()
                    asset_count = summary.get('asset_count', 0)
                    logger.info(f"✅ Portfolio verified: {asset_count} assets found")
                    
                    # Log basic portfolio info
                    balances = portfolio.get_balances()
                    if balances:
                        logger.info("💼 Portfolio balances:")
                        for asset, balance in balances.items():
                            logger.info(f"   {asset}: {balance}")
                    else:
                        logger.info("💼 No asset balances found")
                        
                except Exception as e:
                    logger.warning(f"⚠️  Portfolio verification failed: {e}")
                
                # Test trading functionality for live mode
                if config_loader.config.mode == "live":
                    try:
                        from kraken.trade import KrakenTrader
                        from kraken.auth import KrakenAuth
                        
                        # Initialize trader for testing
                        auth = KrakenAuth(
                            api_key=config_loader.config.api_key,
                            api_secret=config_loader.config.api_secret
                        )
                        trader = KrakenTrader(auth, timeout=30, max_retries=3)
                        
                        logger.info("🔍 Testing trading functionality...")
                        
                        # Get past orders (closed orders)
                        logger.info("📚 Retrieving past orders...")
                        closed_orders = trader.get_closed_orders(
                            trades=True,
                            without_count=True  # Faster for accounts with many orders
                        )
                        
                        order_count = len(closed_orders.get('closed', {}))
                        logger.info(f"📋 Found {order_count} past orders")
                        
                        # Show a few recent orders if any exist
                        if order_count > 0:
                            recent_orders = list(closed_orders['closed'].items())[:3]
                            logger.info("🔍 Recent past orders:")
                            for order_id, order_info in recent_orders:
                                pair = order_info['descr']['pair']
                                order_type = order_info['descr']['type']
                                volume = order_info['vol']
                                price = order_info.get('price', 'market')
                                status = order_info['status']
                                logger.info(f"   {order_id[:8]}... {order_type} {volume} {pair} @ {price} ({status})")
                        
                        # Get open orders
                        logger.info("📖 Retrieving open orders...")
                        open_orders = trader.get_open_orders(trades=True)
                        open_count = len(open_orders.get('open', {}))
                        logger.info(f"📋 Found {open_count} open orders")
                        
                        if open_count > 0:
                            logger.info("🔍 Current open orders:")
                            for order_id, order_info in open_orders['open'].items():
                                pair = order_info['descr']['pair']
                                order_type = order_info['descr']['type']
                                volume = order_info['vol']
                                price = order_info.get('price', 'market')
                                logger.info(f"   {order_id[:8]}... {order_type} {volume} {pair} @ {price}")
                        
                        # Get trade history
                        logger.info("📊 Retrieving recent trade history...")
                        trades_history = trader.get_trades_history(
                            trade_type="all",
                            trades=True,
                            without_count=True
                        )
                        
                        trade_count = len(trades_history.get('trades', {}))
                        logger.info(f"📈 Found {trade_count} past trades")
                        
                        if trade_count > 0:
                            recent_trades = list(trades_history['trades'].items())[:3]
                            logger.info("🔍 Recent trades:")
                            for trade_id, trade_info in recent_trades:
                                pair = trade_info['pair']
                                trade_type = trade_info['type']
                                volume = trade_info['vol']
                                price = trade_info['price']
                                fee = trade_info['fee']
                                logger.info(f"   {trade_id[:8]}... {trade_type} {volume} {pair} @ {price} (fee: {fee})")
                        
                        # Clean up trader session
                        trader.close()
                        logger.info("✅ Trading functionality test completed")
                        
                    except Exception as e:
                        logger.warning(f"⚠️  Trading functionality test failed: {e}")
                        if 'trader' in locals():
                            trader.close()
                
                logger.info("💼 Trading system initialized successfully")
                
            except Exception as e:
                logger.error(f"❌ Portfolio initialization failed: {e}")
                return 1
                
        else:
            logger.warning("⚠️  API credentials validation failed - check your keys")
            return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Failed to start trader: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
