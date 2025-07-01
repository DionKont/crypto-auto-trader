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
