"""
Data Ingestion Manager

This module provides a unified interface for all market data ingestion,
combining REST API calls and real-time WebSocket feeds from Kraken.
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime
import asyncio
import time

from .rest_client import KrakenRESTClient
from .websocket_client import KrakenWebSocketClient, SubscriptionType, Subscription


class DataIngestionManager:
    """
    Unified manager for Kraken market data ingestion.
    
    Provides comprehensive access to:
    - REST API endpoints (historical and current data)
    - Real-time WebSocket feeds
    - Market data caching and management
    - Event-driven data updates
    """
    
    def __init__(self, 
                 websocket_callback: Optional[Callable[[str, Dict], None]] = None,
                 rest_timeout: int = 30,
                 rest_max_retries: int = 3):
        """
        Initialize the data ingestion manager.
        
        Args:
            websocket_callback: Callback function for WebSocket messages
            rest_timeout: REST API request timeout in seconds
            rest_max_retries: Maximum number of REST API request retries
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize REST client
        self.rest_client = KrakenRESTClient(
            timeout=rest_timeout,
            max_retries=rest_max_retries
        )
        
        # Initialize WebSocket client
        self.websocket_client = KrakenWebSocketClient(callback=websocket_callback)
        
        # Data cache
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 60  # Cache TTL in seconds
        
        self.logger.info("🔧 Data Ingestion Manager initialized")
    
    # REST API Methods
    def get_server_time(self) -> Optional[Dict[str, Any]]:
        """Get Kraken server time."""
        return self.rest_client.get_server_time()
    
    def get_system_status(self) -> Optional[Dict[str, Any]]:
        """Get Kraken system status."""
        return self.rest_client.get_system_status()
    
    def get_assets(self, assets: Optional[List[str]] = None, asset_class: str = "currency") -> Optional[Dict[str, Any]]:
        """Get asset information."""
        return self.rest_client.get_assets(assets=assets, asset_class=asset_class)
    
    def get_tradeable_pairs(self, pairs: Optional[List[str]] = None, 
                           info: str = "info") -> Optional[Dict[str, Any]]:
        """Get tradeable asset pairs."""
        return self.rest_client.get_asset_pairs(pairs=pairs, info=info)
    
    def get_ticker_information(self, pairs: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Get ticker information for one or more pairs."""
        return self.rest_client.get_ticker(pairs=pairs)
    
    def get_ohlc_data(self, pair: str, interval: int = 1, 
                      since: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get OHLC data for a trading pair."""
        return self.rest_client.get_ohlc(pair=pair, interval=interval, since=since)
    
    def get_order_book(self, pair: str, count: int = 100) -> Optional[Dict[str, Any]]:
        """Get order book for a trading pair."""
        return self.rest_client.get_order_book(pair=pair, count=count)
    
    def get_recent_trades(self, pair: str, since: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get recent trades for a trading pair."""
        return self.rest_client.get_recent_trades(pair=pair, since=since)
    
    def get_recent_spreads(self, pair: str, since: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get recent spread data for a trading pair."""
        return self.rest_client.get_recent_spreads(pair=pair, since=since)
    
    # Convenience methods for common operations
    def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive market data for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'XBTUSD', 'ETHUSD')
            
        Returns:
            Combined market data including ticker, order book, and recent trades
        """
        cache_key = f"market_data_{symbol}"
        
        # Check cache first
        if self._is_cached(cache_key):
            return self._cache[cache_key]
        
        try:
            market_data = {}
            
            # Get ticker information
            ticker_data = self.get_ticker_information([symbol])
            if ticker_data:
                market_data['ticker'] = ticker_data
            
            # Get order book (limited to top 10 levels for performance)
            order_book = self.get_order_book(symbol, count=10)
            if order_book:
                market_data['order_book'] = order_book
            
            # Get recent trades
            recent_trades = self.get_recent_trades(symbol)
            if recent_trades:
                market_data['recent_trades'] = recent_trades
            
            # Cache the result
            self._cache[cache_key] = market_data
            self._cache_timestamps[cache_key] = time.time()
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get market data for {symbol}: {e}")
            return None
    
    def get_price_feed(self, symbol: str) -> Optional[float]:
        """
        Get current price for a specific symbol.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Current last trade price or None if not available
        """
        try:
            ticker_data = self.get_ticker_information([symbol])
            
            if ticker_data and symbol in ticker_data:
                # Get last trade price from ticker
                last_trade = ticker_data[symbol].get('c', [])
                if last_trade and len(last_trade) > 0:
                    return float(last_trade[0])
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get price for {symbol}: {e}")
            return None
    
    # WebSocket Methods
    def start_websocket(self) -> None:
        """Start the WebSocket connection."""
        self.websocket_client.start()
    
    def stop_websocket(self) -> None:
        """Stop the WebSocket connection."""
        self.websocket_client.stop()
    
    def subscribe_ticker(self, pairs: List[str], event_trigger: str = "trades") -> bool:
        """Subscribe to ticker updates for the specified pairs."""
        return self.websocket_client.subscribe_ticker(pairs, event_trigger=event_trigger)
    
    def subscribe_ohlc(self, pairs: List[str], interval: int = 1) -> bool:
        """Subscribe to OHLC updates for the specified pairs."""
        return self.websocket_client.subscribe_ohlc(pairs, interval=interval)
    
    def subscribe_trades(self, pairs: List[str]) -> bool:
        """Subscribe to trade updates for the specified pairs."""
        return self.websocket_client.subscribe_trades(pairs)
    
    def subscribe_book(self, pairs: List[str], depth: int = 10) -> bool:
        """Subscribe to order book updates for the specified pairs."""
        return self.websocket_client.subscribe_book(pairs, depth=depth)
    
    def subscribe_spread(self, pairs: List[str]) -> bool:
        """Subscribe to spread updates for the specified pairs."""
        return self.websocket_client.subscribe_spread(pairs)
    
    def unsubscribe_all(self) -> None:
        """Unsubscribe from all WebSocket feeds."""
        self.websocket_client.unsubscribe_all()
    
    def get_subscription_status(self) -> Dict[str, str]:
        """Get current WebSocket subscription status."""
        return self.websocket_client.get_subscription_status()
    
    # Utility methods
    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still valid."""
        if key not in self._cache or key not in self._cache_timestamps:
            return False
        
        age = time.time() - self._cache_timestamps[key]
        return age < self._cache_ttl
    
    def clear_cache(self) -> None:
        """Clear the data cache."""
        self._cache.clear()
        self._cache_timestamps.clear()
        self.logger.info("🗑️  Data cache cleared")
    
    def set_cache_ttl(self, ttl: int) -> None:
        """Set cache time-to-live in seconds."""
        self._cache_ttl = ttl
        self.logger.info(f"⏰ Cache TTL set to {ttl} seconds")
    
    def close(self) -> None:
        """Clean up resources."""
        self.logger.info("🔄 Closing Data Ingestion Manager...")
        self.stop_websocket()
        self.clear_cache()
        self.logger.info("✅ Data Ingestion Manager closed")
