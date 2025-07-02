"""
Trader Module

This module provides trading functionality for both live and simulated trading.
It includes Kraken trading integration and backtesting capabilities.
"""

from typing import Dict, Any, Union, Optional
from shared.auth import KrakenAuth
from shared.portfolio import Portfolio
from modules.trader.kraken.trade import KrakenTrader
from modules.trader.backtest.portfolio_sim import PortfolioSim
from config.config_loader import TradingConfig


class TraderManager:
    """
    Manager class for trading operations across live and simulated environments.
    
    This class provides a unified interface for trading operations that works
    with both live Kraken trading and simulated backtesting.
    """
    
    def __init__(self, config: TradingConfig):
        """
        Initialize the trader manager.
        
        Args:
            config: Trading configuration
        """
        self.config = config
        self.auth = None
        self.trader = None
        self.portfolio = None
        
        if config.mode == "live":
            self.auth = KrakenAuth(
                api_key=config.api_key,
                api_secret=config.api_secret
            )
            self.trader = KrakenTrader(self.auth)
            self.portfolio = Portfolio(self.auth)
        else:  # backtest mode
            self.portfolio = PortfolioSim()
    
    def get_portfolio(self) -> Union[Portfolio, PortfolioSim]:
        """Get the portfolio instance."""
        return self.portfolio
    
    def get_trader(self) -> Optional[KrakenTrader]:
        """Get the trader instance (None for backtest mode)."""
        return self.trader
    
    def is_live_mode(self) -> bool:
        """Check if running in live trading mode."""
        return self.config.mode == "live"
    
    def close(self) -> None:
        """Clean up resources."""
        if self.trader:
            self.trader.close()
