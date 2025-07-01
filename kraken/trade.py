"""
Kraken Trading Module

This module provides comprehensive trading functionality for the Kraken cryptocurrency exchange API.
It supports all Kraken trading operations with robust error handling, logging, and validation.
"""

import time
import logging
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from enum import Enum
import requests

from .auth import KrakenAuth


class OrderType(Enum):
    """Supported Kraken order types."""
    MARKET = "market"
    LIMIT = "limit"
    ICEBERG = "iceberg"
    STOP_LOSS = "stop-loss"
    TAKE_PROFIT = "take-profit"
    TRAILING_STOP = "trailing-stop"
    STOP_LOSS_LIMIT = "stop-loss-limit"
    TAKE_PROFIT_LIMIT = "take-profit-limit"
    TRAILING_STOP_LIMIT = "trailing-stop-limit"
    SETTLE_POSITION = "settle-position"


class OrderSide(Enum):
    """Order sides (buy/sell)."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status values."""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELED = "canceled"
    EXPIRED = "expired"


class TriggerType(Enum):
    """Price trigger types for stop orders."""
    LAST = "last"
    INDEX = "index"


class OrderFlags(Enum):
    """Order flags for special order behavior."""
    POST = "post"  # post-only order (limit orders only)
    FCIB = "fcib"  # prefer fee in base currency
    FCIQ = "fciq"  # prefer fee in quote currency
    NOMPP = "nompp"  # disable market price protection
    VIQC = "viqc"  # order volume in quote currency


class KrakenTrader:
    """
    Comprehensive Kraken trading interface with full API coverage.
    
    This class provides access to all Kraken trading functionality including:
    - Order placement (all order types)
    - Order management (cancel, amend, query)
    - Position management
    - Trade history
    - Account information
    - Advanced order features (conditional close, leverage, etc.)
    
    Features:
    - Robust error handling and retries
    - Comprehensive logging
    - Input validation
    - Rate limiting awareness
    - Fail-safe mechanisms
    """
    
    BASE_URL = "https://api.kraken.com"
    API_VERSION = "0"
    
    # Trading endpoints
    ADD_ORDER_ENDPOINT = "/0/private/AddOrder"
    AMEND_ORDER_ENDPOINT = "/0/private/AmendOrder"
    CANCEL_ORDER_ENDPOINT = "/0/private/CancelOrder"
    CANCEL_ALL_ORDERS_ENDPOINT = "/0/private/CancelAll"
    CANCEL_ALL_ORDERS_AFTER_ENDPOINT = "/0/private/CancelAllOrdersAfter"
    
    # Query endpoints
    OPEN_ORDERS_ENDPOINT = "/0/private/OpenOrders"
    CLOSED_ORDERS_ENDPOINT = "/0/private/ClosedOrders"
    QUERY_ORDERS_ENDPOINT = "/0/private/QueryOrders"
    TRADES_HISTORY_ENDPOINT = "/0/private/TradesHistory"
    QUERY_TRADES_ENDPOINT = "/0/private/QueryTrades"
    OPEN_POSITIONS_ENDPOINT = "/0/private/OpenPositions"
    LEDGERS_ENDPOINT = "/0/private/Ledgers"
    QUERY_LEDGERS_ENDPOINT = "/0/private/QueryLedgers"
    TRADE_VOLUME_ENDPOINT = "/0/private/TradeVolume"
    
    # Export endpoints
    ADD_EXPORT_ENDPOINT = "/0/private/AddExport"
    EXPORT_STATUS_ENDPOINT = "/0/private/ExportStatus"
    RETRIEVE_EXPORT_ENDPOINT = "/0/private/RetrieveExport"
    REMOVE_EXPORT_ENDPOINT = "/0/private/RemoveExport"
    
    def __init__(self, auth: KrakenAuth, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the Kraken trader.
        
        Args:
            auth: KrakenAuth instance for API authentication
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts for failed requests (default: 3)
        """
        self.auth = auth
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
        self._session = requests.Session()
        
        # Set up session headers
        self._session.headers.update({
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Kraken-Auto-Trader/1.0"
        })
        
        self.logger.info("🔧 Kraken trader initialized")
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an authenticated request to the Kraken API with retries and error handling.
        
        Args:
            endpoint: API endpoint path
            data: Request parameters
            
        Returns:
            API response data
            
        Raises:
            Exception: For API errors or network issues
        """
        nonce = str(int(time.time() * 1000))
        data["nonce"] = nonce
        
        # Get authentication headers
        auth_headers = self.auth.sign_request(endpoint, data)
        headers = {**self._session.headers, **auth_headers}
        
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"📡 Making request to {endpoint} (attempt {attempt + 1})")
                
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
                    raise Exception(f"Invalid JSON response from Kraken API: {e}")
                
                # Check for API errors
                if "error" in result and result["error"]:
                    error_messages = ", ".join(result["error"])
                    raise Exception(f"Kraken API error: {error_messages}")
                
                if "result" not in result:
                    raise Exception("Missing 'result' field in API response")
                
                return result["result"]
                
            except requests.RequestException as e:
                if attempt == self.max_retries:
                    self.logger.error(f"❌ Request failed after {self.max_retries + 1} attempts: {e}")
                    raise Exception(f"Network error after {self.max_retries + 1} attempts: {e}")
                
                wait_time = 2 ** attempt  # Exponential backoff
                self.logger.warning(f"⚠️  Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            
            except Exception as e:
                self.logger.error(f"❌ API request failed: {e}")
                raise
    
    def add_order(
        self,
        pair: str,
        side: Union[OrderSide, str],
        order_type: Union[OrderType, str],
        volume: Union[Decimal, str, float],
        price: Optional[Union[Decimal, str, float]] = None,
        price2: Optional[Union[Decimal, str, float]] = None,
        trigger: Optional[Union[TriggerType, str]] = None,
        leverage: Optional[Union[int, str]] = None,
        reduce_only: bool = False,
        start_time: Optional[int] = None,
        expire_time: Optional[int] = None,
        deadline: Optional[str] = None,
        user_ref: Optional[int] = None,
        client_order_id: Optional[str] = None,
        validate: bool = False,
        order_flags: Optional[List[Union[OrderFlags, str]]] = None,
        time_in_force: Optional[str] = None,
        close_order_type: Optional[Union[OrderType, str]] = None,
        close_price: Optional[Union[Decimal, str, float]] = None,
        close_price2: Optional[Union[Decimal, str, float]] = None
    ) -> Dict[str, Any]:
        """
        Place a new order with comprehensive parameter support.
        
        Args:
            pair: Asset pair (e.g., 'XXBTZUSD', 'XETHZEUR')
            side: Order side ('buy' or 'sell')
            order_type: Order type (market, limit, stop-loss, etc.)
            volume: Order volume in base currency
            price: Order price (required for limit orders)
            price2: Secondary price (for stop-loss-limit, take-profit-limit)
            trigger: Price trigger ('last' or 'index') for stop orders
            leverage: Leverage amount (e.g., '2:1', '5:1')
            reduce_only: Whether order should only reduce position
            start_time: Scheduled start time (unix timestamp)
            expire_time: Order expiration time (unix timestamp)
            deadline: Self-trade prevention deadline
            user_ref: User reference ID (32-bit signed integer)
            client_order_id: Client order ID (alphanumeric, max 64 chars)
            validate: If true, validates order without placing it
            order_flags: List of order flags (post, fcib, fciq, nompp, viqc)
            time_in_force: Time in force ('IOC', 'GTC')
            close_order_type: Conditional close order type
            close_price: Conditional close order price
            close_price2: Conditional close order secondary price
            
        Returns:
            Order placement result with order IDs and transaction details
            
        Raises:
            ValueError: For invalid parameters
            Exception: For API errors
        """
        # Input validation
        if not pair:
            raise ValueError("Asset pair is required")
        
        # Convert enums to strings
        side_str = side.value if isinstance(side, OrderSide) else str(side)
        order_type_str = order_type.value if isinstance(order_type, OrderType) else str(order_type)
        
        if side_str not in ["buy", "sell"]:
            raise ValueError(f"Invalid order side: {side_str}")
        
        # Validate order type
        valid_order_types = [ot.value for ot in OrderType]
        if order_type_str not in valid_order_types:
            raise ValueError(f"Invalid order type: {order_type_str}")
        
        # Validate volume
        try:
            volume_decimal = Decimal(str(volume))
            if volume_decimal <= 0:
                raise ValueError("Volume must be positive")
        except (ValueError, TypeError):
            raise ValueError(f"Invalid volume: {volume}")
        
        # Build request data
        data = {
            "pair": pair,
            "type": side_str,
            "ordertype": order_type_str,
            "volume": str(volume)
        }
        
        # Add optional parameters
        if price is not None:
            data["price"] = str(price)
        
        if price2 is not None:
            data["price2"] = str(price2)
        
        if trigger:
            trigger_str = trigger.value if isinstance(trigger, TriggerType) else str(trigger)
            data["trigger"] = trigger_str
        
        if leverage:
            data["leverage"] = str(leverage)
        
        if reduce_only:
            data["reduce_only"] = "true"
        
        if start_time:
            data["starttm"] = str(start_time)
        
        if expire_time:
            data["expiretm"] = str(expire_time)
        
        if deadline:
            data["deadline"] = deadline
        
        if user_ref:
            data["userref"] = str(user_ref)
        
        if client_order_id:
            data["cl_ord_id"] = client_order_id
        
        if validate:
            data["validate"] = "true"
        
        if order_flags:
            flags = []
            for flag in order_flags:
                flag_str = flag.value if isinstance(flag, OrderFlags) else str(flag)
                flags.append(flag_str)
            data["oflags"] = ",".join(flags)
        
        if time_in_force:
            data["timeinforce"] = time_in_force
        
        # Conditional close parameters
        if close_order_type:
            close_type_str = close_order_type.value if isinstance(close_order_type, OrderType) else str(close_order_type)
            data["close[ordertype]"] = close_type_str
        
        if close_price:
            data["close[price]"] = str(close_price)
        
        if close_price2:
            data["close[price2]"] = str(close_price2)
        
        self.logger.info(f"📝 Placing {side_str} order: {volume} {pair} @ {price if price else 'market'}")
        
        try:
            result = self._make_request(self.ADD_ORDER_ENDPOINT, data)
            
            if validate:
                self.logger.info("✅ Order validation successful")
            else:
                order_ids = result.get("txid", [])
                self.logger.info(f"✅ Order placed successfully. Order IDs: {', '.join(order_ids)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Failed to place order: {e}")
            raise
    
    def cancel_order(
        self,
        order_id: Optional[str] = None,
        user_ref: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel a specific order by ID, user reference, or client order ID.
        
        Args:
            order_id: Order transaction ID
            user_ref: User reference ID
            client_order_id: Client order ID
            
        Returns:
            Cancellation result
            
        Raises:
            ValueError: If no identifier is provided
            Exception: For API errors
        """
        if not any([order_id, user_ref, client_order_id]):
            raise ValueError("Must provide order_id, user_ref, or client_order_id")
        
        data = {}
        
        if order_id:
            data["txid"] = order_id
        elif user_ref:
            data["userref"] = str(user_ref)
        elif client_order_id:
            data["cl_ord_id"] = client_order_id
        
        self.logger.info(f"🗑️  Cancelling order: {order_id or user_ref or client_order_id}")
        
        try:
            result = self._make_request(self.CANCEL_ORDER_ENDPOINT, data)
            self.logger.info("✅ Order cancelled successfully")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to cancel order: {e}")
            raise
    
    def cancel_all_orders(self) -> Dict[str, Any]:
        """
        Cancel all open orders.
        
        Returns:
            Cancellation result with count of cancelled orders
        """
        self.logger.info("🗑️  Cancelling all open orders")
        
        try:
            result = self._make_request(self.CANCEL_ALL_ORDERS_ENDPOINT, {})
            count = result.get("count", 0)
            self.logger.info(f"✅ Cancelled {count} orders")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to cancel all orders: {e}")
            raise
    
    def cancel_all_orders_after(self, timeout: int) -> Dict[str, Any]:
        """
        Cancel all orders after a specified timeout (dead man's switch).
        
        Args:
            timeout: Timeout in seconds (0 to disable)
            
        Returns:
            Dead man's switch confirmation
        """
        data = {"timeout": str(timeout)}
        
        if timeout > 0:
            self.logger.info(f"⏰ Setting dead man's switch: cancel all orders after {timeout}s")
        else:
            self.logger.info("⏰ Disabling dead man's switch")
        
        try:
            result = self._make_request(self.CANCEL_ALL_ORDERS_AFTER_ENDPOINT, data)
            self.logger.info("✅ Dead man's switch configured")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to configure dead man's switch: {e}")
            raise
    
    def get_open_orders(
        self,
        trades: bool = False,
        user_ref: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get information about open orders.
        
        Args:
            trades: Whether to include trades in output
            user_ref: Restrict results to given user reference
            client_order_id: Restrict results to given client order ID
            
        Returns:
            Open orders information
        """
        data = {}
        
        if trades:
            data["trades"] = "true"
        
        if user_ref:
            data["userref"] = str(user_ref)
        
        if client_order_id:
            data["cl_ord_id"] = client_order_id
        
        try:
            result = self._make_request(self.OPEN_ORDERS_ENDPOINT, data)
            order_count = len(result.get("open", {}))
            self.logger.info(f"📋 Retrieved {order_count} open orders")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get open orders: {e}")
            raise
    
    def get_closed_orders(
        self,
        trades: bool = False,
        user_ref: Optional[int] = None,
        client_order_id: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        offset: Optional[int] = None,
        close_time: str = "both",
        consolidate_taker: bool = True,
        without_count: bool = False
    ) -> Dict[str, Any]:
        """
        Get information about closed orders.
        
        Args:
            trades: Whether to include trades in output
            user_ref: Restrict results to given user reference
            client_order_id: Restrict results to given client order ID
            start: Starting unix timestamp or order tx ID
            end: Ending unix timestamp or order tx ID
            offset: Result offset for pagination
            close_time: Which time to use ('open', 'close', 'both')
            consolidate_taker: Whether to consolidate trades by taker
            without_count: Whether to exclude page count (faster for many orders)
            
        Returns:
            Closed orders information
        """
        data = {"closetime": close_time}
        
        if trades:
            data["trades"] = "true"
        
        if user_ref:
            data["userref"] = str(user_ref)
        
        if client_order_id:
            data["cl_ord_id"] = client_order_id
        
        if start:
            data["start"] = str(start)
        
        if end:
            data["end"] = str(end)
        
        if offset:
            data["ofs"] = str(offset)
        
        if not consolidate_taker:
            data["consolidate_taker"] = "false"
        
        if without_count:
            data["without_count"] = "true"
        
        try:
            result = self._make_request(self.CLOSED_ORDERS_ENDPOINT, data)
            order_count = len(result.get("closed", {}))
            self.logger.info(f"📋 Retrieved {order_count} closed orders")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get closed orders: {e}")
            raise
    
    def query_orders_info(self, order_ids: List[str], trades: bool = False, user_ref: Optional[int] = None) -> Dict[str, Any]:
        """
        Query information about specific orders.
        
        Args:
            order_ids: List of order transaction IDs
            trades: Whether to include trades in output
            user_ref: Restrict results to given user reference
            
        Returns:
            Order information
        """
        data = {"txid": ",".join(order_ids)}
        
        if trades:
            data["trades"] = "true"
        
        if user_ref:
            data["userref"] = str(user_ref)
        
        try:
            result = self._make_request(self.QUERY_ORDERS_ENDPOINT, data)
            self.logger.info(f"📋 Retrieved info for {len(order_ids)} orders")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to query orders: {e}")
            raise
    
    def get_trades_history(
        self,
        trade_type: str = "all",
        trades: bool = False,
        start: Optional[int] = None,
        end: Optional[int] = None,
        offset: Optional[int] = None,
        consolidate_taker: bool = True,
        without_count: bool = False
    ) -> Dict[str, Any]:
        """
        Get trade history.
        
        Args:
            trade_type: Type of trade ('all', 'any position', 'closed position', 'closing position', 'no position')
            trades: Whether to include trades in output
            start: Starting unix timestamp or trade ID
            end: Ending unix timestamp or trade ID
            offset: Result offset for pagination
            consolidate_taker: Whether to consolidate trades by taker
            without_count: Whether to exclude page count
            
        Returns:
            Trade history
        """
        data = {"type": trade_type}
        
        if trades:
            data["trades"] = "true"
        
        if start:
            data["start"] = str(start)
        
        if end:
            data["end"] = str(end)
        
        if offset:
            data["ofs"] = str(offset)
        
        if not consolidate_taker:
            data["consolidate_taker"] = "false"
        
        if without_count:
            data["without_count"] = "true"
        
        try:
            result = self._make_request(self.TRADES_HISTORY_ENDPOINT, data)
            trade_count = len(result.get("trades", {}))
            self.logger.info(f"📊 Retrieved {trade_count} trades from history")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get trades history: {e}")
            raise
    
    def get_open_positions(
        self,
        transaction_ids: Optional[List[str]] = None,
        do_calcs: bool = False,
        consolidation: str = "market"
    ) -> Dict[str, Any]:
        """
        Get information about open positions.
        
        Args:
            transaction_ids: List of transaction IDs to query
            do_calcs: Whether to include profit/loss calculations
            consolidation: Position consolidation type ('market' or 'position')
            
        Returns:
            Open positions information
        """
        data = {"consolidation": consolidation}
        
        if transaction_ids:
            data["txid"] = ",".join(transaction_ids)
        
        if do_calcs:
            data["docalcs"] = "true"
        
        try:
            result = self._make_request(self.OPEN_POSITIONS_ENDPOINT, data)
            position_count = len(result)
            self.logger.info(f"📊 Retrieved {position_count} open positions")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get open positions: {e}")
            raise
    
    def get_trade_volume(self, pairs: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get trade volume and fees information.
        
        Args:
            pairs: List of asset pairs to query
            
        Returns:
            Trade volume and fee information
        """
        data = {}
        
        if pairs:
            data["pair"] = ",".join(pairs)
        
        try:
            result = self._make_request(self.TRADE_VOLUME_ENDPOINT, data)
            self.logger.info("📊 Retrieved trade volume information")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get trade volume: {e}")
            raise
    
    def get_ledgers(
        self,
        asset: Optional[str] = None,
        asset_class: str = "currency",
        ledger_type: str = "all",
        start: Optional[int] = None,
        end: Optional[int] = None,
        offset: Optional[int] = None,
        without_count: bool = False
    ) -> Dict[str, Any]:
        """
        Get ledger information.
        
        Args:
            asset: Asset to query (default: all)
            asset_class: Asset class filter
            ledger_type: Type of ledger entry
            start: Starting unix timestamp or ledger ID
            end: Ending unix timestamp or ledger ID
            offset: Result offset for pagination
            without_count: Whether to exclude page count
            
        Returns:
            Ledger information
        """
        data = {
            "aclass": asset_class,
            "type": ledger_type
        }
        
        if asset:
            data["asset"] = asset
        
        if start:
            data["start"] = str(start)
        
        if end:
            data["end"] = str(end)
        
        if offset:
            data["ofs"] = str(offset)
        
        if without_count:
            data["without_count"] = "true"
        
        try:
            result = self._make_request(self.LEDGERS_ENDPOINT, data)
            ledger_count = len(result.get("ledger", {}))
            self.logger.info(f"📊 Retrieved {ledger_count} ledger entries")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get ledgers: {e}")
            raise
    
    # Market order helpers
    def market_buy(self, pair: str, volume: Union[Decimal, str, float], **kwargs) -> Dict[str, Any]:
        """Place a market buy order."""
        return self.add_order(pair, OrderSide.BUY, OrderType.MARKET, volume, **kwargs)
    
    def market_sell(self, pair: str, volume: Union[Decimal, str, float], **kwargs) -> Dict[str, Any]:
        """Place a market sell order."""
        return self.add_order(pair, OrderSide.SELL, OrderType.MARKET, volume, **kwargs)
    
    # Limit order helpers
    def limit_buy(self, pair: str, volume: Union[Decimal, str, float], price: Union[Decimal, str, float], **kwargs) -> Dict[str, Any]:
        """Place a limit buy order."""
        return self.add_order(pair, OrderSide.BUY, OrderType.LIMIT, volume, price=price, **kwargs)
    
    def limit_sell(self, pair: str, volume: Union[Decimal, str, float], price: Union[Decimal, str, float], **kwargs) -> Dict[str, Any]:
        """Place a limit sell order."""
        return self.add_order(pair, OrderSide.SELL, OrderType.LIMIT, volume, price=price, **kwargs)
    
    # Stop loss helpers
    def stop_loss_buy(self, pair: str, volume: Union[Decimal, str, float], stop_price: Union[Decimal, str, float], **kwargs) -> Dict[str, Any]:
        """Place a stop loss buy order."""
        return self.add_order(pair, OrderSide.BUY, OrderType.STOP_LOSS, volume, price=stop_price, **kwargs)
    
    def stop_loss_sell(self, pair: str, volume: Union[Decimal, str, float], stop_price: Union[Decimal, str, float], **kwargs) -> Dict[str, Any]:
        """Place a stop loss sell order."""
        return self.add_order(pair, OrderSide.SELL, OrderType.STOP_LOSS, volume, price=stop_price, **kwargs)
    
    # Take profit helpers
    def take_profit_buy(self, pair: str, volume: Union[Decimal, str, float], profit_price: Union[Decimal, str, float], **kwargs) -> Dict[str, Any]:
        """Place a take profit buy order."""
        return self.add_order(pair, OrderSide.BUY, OrderType.TAKE_PROFIT, volume, price=profit_price, **kwargs)
    
    def take_profit_sell(self, pair: str, volume: Union[Decimal, str, float], profit_price: Union[Decimal, str, float], **kwargs) -> Dict[str, Any]:
        """Place a take profit sell order."""
        return self.add_order(pair, OrderSide.SELL, OrderType.TAKE_PROFIT, volume, price=profit_price, **kwargs)
    
    def __str__(self) -> str:
        """String representation of the trader."""
        return f"KrakenTrader(timeout={self.timeout}, max_retries={self.max_retries})"
    
    def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            self._session.close()
            self.logger.info("🔒 Kraken trader session closed")
