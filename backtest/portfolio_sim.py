"""
Simulated Portfolio Module for Backtesting

This module provides a simulated portfolio that mirrors the interface of the real
Kraken Portfolio class, allowing seamless switching between live and backtest modes.
"""

import time
import logging
import json
import os
from typing import Dict, Optional, Any, List
from decimal import Decimal
from datetime import datetime


class PortfolioSim:
    """
    Simulated portfolio for backtesting that mirrors the Portfolio class interface.
    
    This class provides the same methods as the real Portfolio class but operates
    on simulated balances instead of making actual API calls to Kraken.
    """
    
    def __init__(self, initial_balances: Optional[Dict[str, Decimal]] = None, timeout: int = 30):
        """
        Initialize the simulated portfolio.
        
        Args:
            initial_balances: Starting balances as {asset: amount}. 
                            Defaults to 1 ETH and 1000 GBP
            timeout: Timeout parameter (kept for interface compatibility)
        """
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # Set default balances: 1 ETH and 1000 GBP
        if initial_balances is None:
            self._balances = {
                "ETH": Decimal("1.0"),
                "GBP": Decimal("1000.0")
            }
        else:
            # Convert all values to Decimal and filter out zero balances
            self._balances = {}
            for asset, balance in initial_balances.items():
                decimal_balance = Decimal(str(balance))
                if decimal_balance > 0:
                    self._balances[asset] = decimal_balance
        
        # Historical state tracking for backtesting
        self._historical_states: List[Dict[str, Any]] = []
        self._log_file_path = "backtest/logs/portfolio_sim.json"
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(self._log_file_path), exist_ok=True)
        
        # Save initial state
        self._save_portfolio_state("initialization", {})
        
        self.logger.info(f"💼 Simulated portfolio initialized with {len(self._balances)} assets")
        
    def get_balances(self) -> Dict[str, Decimal]:
        """
        Retrieve all simulated account balances.
        
        Returns:
            Dictionary mapping asset names to their balances as Decimal objects.
            Only returns assets with non-zero balances.
        """
        # Return a copy to prevent external modification
        balances_copy = self._balances.copy()
        self.logger.debug(f"Retrieved simulated balances for {len(balances_copy)} assets")
        return balances_copy
    
    def get_balance(self, asset: str) -> Optional[Decimal]:
        """
        Get balance for a specific asset.
        
        Args:
            asset: Asset symbol (e.g., 'BTC', 'ETH', 'GBP')
            
        Returns:
            Asset balance as Decimal, or None if asset not found or balance is zero
        """
        return self._balances.get(asset)
    
    def get_total_balance_gbp(self) -> Optional[Decimal]:
        """
        Get total portfolio balance in GBP equivalent.
        
        Note: This method currently returns the GBP balance only.
        For a complete GBP-equivalent calculation, you would need
        to fetch current market prices for all assets.
        
        Returns:
            GBP balance as Decimal, or None if no GBP balance exists
        """
        return self.get_balance("GBP") or self.get_balance("ZGBP")
    
    def get_total_balance_usd(self) -> Optional[Decimal]:
        """
        Get total portfolio balance in USD equivalent.
        
        Note: This method currently returns the USD balance only.
        For a complete USD-equivalent calculation, you would need
        to fetch current market prices for all assets.
        
        Returns:
            USD balance as Decimal, or None if no USD balance exists
        """
        return self.get_balance("USD") or self.get_balance("ZUSD")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive portfolio summary.
        
        Returns:
            Dictionary containing portfolio information including:
            - balances: All non-zero asset balances
            - asset_count: Number of different assets held
            - timestamp: When the data was retrieved
        """
        return {
            "balances": {asset: str(balance) for asset, balance in self._balances.items()},
            "asset_count": len(self._balances),
            "timestamp": time.time(),
            "total_assets": list(self._balances.keys())
        }
    
    def has_sufficient_balance(self, asset: str, required_amount: Decimal) -> bool:
        """
        Check if account has sufficient balance for a specific asset.
        
        Args:
            asset: Asset symbol to check
            required_amount: Required amount as Decimal
            
        Returns:
            True if sufficient balance exists, False otherwise
        """
        current_balance = self.get_balance(asset)
        if current_balance is None:
            return False
        return current_balance >= required_amount
    
    def __str__(self) -> str:
        """String representation of the simulated portfolio."""
        if not self._balances:
            return "Simulated Portfolio: No balances"
        
        balance_strs = [f"{asset}: {balance}" for asset, balance in self._balances.items()]
        return f"Simulated Portfolio: {', '.join(balance_strs)}"
    
    # Additional methods for backtesting functionality
    
    def update_balance(self, asset: str, new_balance: Decimal) -> None:
        """
        Update the balance of a specific asset.
        
        Args:
            asset: Asset symbol to update
            new_balance: New balance amount
        """
        old_balance = self._balances.get(asset, Decimal("0"))
        
        if new_balance <= 0:
            # Remove asset if balance becomes zero or negative
            self._balances.pop(asset, None)
            self.logger.debug(f"Removed {asset} from portfolio (balance: {new_balance})")
        else:
            self._balances[asset] = new_balance
            self.logger.debug(f"Updated {asset} balance to {new_balance}")
        
        # Track the balance change
        change_data = {
            "asset": asset,
            "old_balance": str(old_balance),
            "new_balance": str(new_balance),
            "change": str(new_balance - old_balance)
        }
        self._save_portfolio_state("balance_updated", change_data)
    
    def add_to_balance(self, asset: str, amount: Decimal) -> None:
        """
        Add to the balance of a specific asset.
        
        Args:
            asset: Asset symbol to update
            amount: Amount to add (can be negative to subtract)
        """
        current_balance = self.get_balance(asset) or Decimal("0")
        new_balance = current_balance + amount
        self.update_balance(asset, new_balance)
    
    def execute_trade(self, sell_asset: str, sell_amount: Decimal, 
                     buy_asset: str, buy_amount: Decimal) -> bool:
        """
        Execute a simulated trade between two assets.
        
        Args:
            sell_asset: Asset to sell
            sell_amount: Amount to sell
            buy_asset: Asset to buy
            buy_amount: Amount to buy
            
        Returns:
            True if trade was executed successfully, False otherwise
        """
        # Check if we have sufficient balance to sell
        if not self.has_sufficient_balance(sell_asset, sell_amount):
            self.logger.warning(f"Insufficient {sell_asset} balance for trade")
            return False
        
        # Execute the trade
        self.add_to_balance(sell_asset, -sell_amount)  # Subtract sold amount
        self.add_to_balance(buy_asset, buy_amount)     # Add bought amount
        
        self.logger.info(f"🔄 Executed trade: -{sell_amount} {sell_asset} → +{buy_amount} {buy_asset}")
        return True
    
    def reset_to_defaults(self) -> None:
        """Reset portfolio to default balances (1 ETH, 1000 GBP)."""
        self._balances = {
            "ETH": Decimal("1.0"),
            "GBP": Decimal("1000.0")
        }
        self._save_portfolio_state("portfolio_reset", {})
        self.logger.info("🔄 Portfolio reset to default balances")
    
    # Historical state tracking methods for backtesting
    
    def _save_portfolio_state(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Save the current portfolio state to historical tracking.
        
        Args:
            event_type: Type of event (e.g., 'balance_update', 'initialization')
            event_data: Additional data about the event
        """
        timestamp = time.time()
        datetime_str = datetime.fromtimestamp(timestamp).isoformat()
        
        state = {
            "timestamp": timestamp,
            "datetime": datetime_str,
            "event_type": event_type,
            "balances": {asset: str(balance) for asset, balance in self._balances.items()},
            "asset_count": len(self._balances),
            "event_data": event_data
        }
        
        # Add to historical states
        self._historical_states.append(state)
        
        # Save to JSON file
        self._write_to_json_log()
    
    def _write_to_json_log(self) -> None:
        """Write the historical data to JSON log file."""
        try:
            log_data = {
                "portfolio_states": self._historical_states,
                "summary": {
                    "total_states": len(self._historical_states),
                    "start_time": self._historical_states[0]["timestamp"] if self._historical_states else None,
                    "last_update": self._historical_states[-1]["timestamp"] if self._historical_states else None,
                    "current_balances": {asset: str(balance) for asset, balance in self._balances.items()}
                }
            }
            
            with open(self._log_file_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to write portfolio state to JSON log: {e}")
    
    def get_historical_states(self) -> List[Dict[str, Any]]:
        """
        Get all historical portfolio states.
        
        Returns:
            List of historical portfolio states
        """
        return self._historical_states.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a performance summary for backtesting analysis.
        
        Returns:
            Dictionary containing performance metrics
        """
        if not self._historical_states:
            return {}
        
        initial_state = self._historical_states[0]
        current_state = self._historical_states[-1]
        
        return {
            "initial_balances": initial_state["balances"],
            "current_balances": current_state["balances"],
            "total_states": len(self._historical_states),
            "duration_seconds": current_state["timestamp"] - initial_state["timestamp"],
            "start_datetime": initial_state["datetime"],
            "end_datetime": current_state["datetime"],
            "log_file_path": self._log_file_path
        }
    
    def save_manual_state(self, description: str, additional_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Manually save a portfolio state with custom description.
        
        Args:
            description: Description of the state
            additional_data: Optional additional data to save
        """
        event_data = {"description": description}
        if additional_data:
            event_data.update(additional_data)
        
        self._save_portfolio_state("manual_checkpoint", event_data)