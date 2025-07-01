"""
Kraken Portfolio Management Module

This module provides functionality to retrieve and manage portfolio data
from the Kraken cryptocurrency exchange API.
"""

import time
import logging
from typing import Dict, Optional, Any
from decimal import Decimal
import requests

from .auth import KrakenAuth


class Portfolio:
    """
    Manages portfolio data retrieval from Kraken API.
    
    This class provides methods to fetch account balances and portfolio information
    using the Kraken REST API with proper authentication and error handling.
    """
    
    BASE_URL = "https://api.kraken.com"
    BALANCE_ENDPOINT = "/0/private/Balance"
    
    def __init__(self, auth: KrakenAuth, timeout: int = 30):
        """
        Initialize the Portfolio manager.
        
        Args:
            auth: KrakenAuth instance for API authentication
            timeout: Request timeout in seconds (default: 30)
        """
        self.auth = auth
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self._session = requests.Session()
        
    def get_balances(self) -> Dict[str, Decimal]:
        """
        Retrieve all account balances from Kraken.
        
        Returns:
            Dictionary mapping asset names to their balances as Decimal objects.
            Only returns assets with non-zero balances.
            
        Raises:
            requests.RequestException: For network or HTTP errors
            ValueError: For invalid API responses
            Exception: For API errors returned by Kraken
        """
        try:
            # Prepare the request
            nonce = str(int(time.time() * 1000))
            data = {"nonce": nonce}
            
            # Sign the request - get the headers dict
            auth_headers = self.auth.sign_request(self.BALANCE_ENDPOINT, data)
            
            # Prepare headers
            headers = {
                **auth_headers,  # Include API-Key and API-Sign from auth
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Kraken-Portfolio-Manager/1.0"
            }
            
            # Make the request
            url = f"{self.BASE_URL}{self.BALANCE_ENDPOINT}"
            response = self._session.post(
                url,
                headers=headers,
                data=data,
                timeout=self.timeout
            )
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse JSON response
            try:
                result = response.json()
            except ValueError as e:
                raise ValueError(f"Invalid JSON response from Kraken API: {e}")
            
            # Check for API errors
            if "error" in result and result["error"]:
                error_messages = ", ".join(result["error"])
                raise Exception(f"Kraken API error: {error_messages}")
            
            # Extract and process balances
            if "result" not in result:
                raise ValueError("Missing 'result' field in API response")
            
            raw_balances = result["result"]
            if not isinstance(raw_balances, dict):
                raise ValueError("Expected 'result' to be a dictionary")
            
            # Convert to Decimal and filter out zero balances
            balances = {}
            for asset, balance_str in raw_balances.items():
                try:
                    balance = Decimal(str(balance_str))
                    # Only include non-zero balances
                    if balance > 0:
                        balances[asset] = balance
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Could not parse balance for {asset}: {balance_str} - {e}")
                    continue
            
            self.logger.info(f"Retrieved balances for {len(balances)} assets")
            return balances
            
        except requests.RequestException as e:
            self.logger.error(f"Network error retrieving balances: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving balances: {e}")
            raise
    
    def get_balance(self, asset: str) -> Optional[Decimal]:
        """
        Get balance for a specific asset.
        
        Args:
            asset: Asset symbol (e.g., 'BTC', 'ETH', 'USD')
            
        Returns:
            Asset balance as Decimal, or None if asset not found or balance is zero
        """
        balances = self.get_balances()
        return balances.get(asset)
    
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
        balances = self.get_balances()
        
        return {
            "balances": {asset: str(balance) for asset, balance in balances.items()},
            "asset_count": len(balances),
            "timestamp": time.time(),
            "total_assets": list(balances.keys())
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
        """String representation of the portfolio."""
        try:
            balances = self.get_balances()
            if not balances:
                return "Portfolio: No balances"
            
            balance_strs = [f"{asset}: {balance}" for asset, balance in balances.items()]
            return f"Portfolio: {', '.join(balance_strs)}"
        except Exception as e:
            return f"Portfolio: Error retrieving balances - {e}"