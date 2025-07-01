"""
Portfolio Factory Utility

Simple utility to create the appropriate portfolio based on configuration.
"""

from typing import Union
from config.config_loader import TradingConfig
from kraken.auth import KrakenAuth
from kraken.portfolio import Portfolio
from backtest.portfolio_sim import PortfolioSim


class PortfolioFactory:
    """Factory class to create the appropriate portfolio based on mode."""
    
    @staticmethod
    def create_portfolio(config: TradingConfig) -> Union[Portfolio, PortfolioSim]:
        """
        Create and return the appropriate portfolio based on configuration.
        
        Args:
            config: Trading configuration
            
        Returns:
            Portfolio instance (either live or simulated)
            
        Raises:
            Exception: If portfolio creation fails
        """
        if config.mode == "live":
            auth = KrakenAuth(
                api_key=config.api_key,
                api_secret=config.api_secret
            )
            return Portfolio(auth)
        else:  # backtest mode
            return PortfolioSim()
