"""
Kraken REST API Client for Market Data

This module provides comprehensive access to Kraken's REST API endpoints for
market data retrieval including assets, trading pairs, ticker information,
OHLC data, order books, and recent trades.
"""

import time
import logging
from typing import Dict, List, Optional, Any, Union
import requests
from decimal import Decimal
from datetime import datetime


class KrakenRESTClient:
    """
    Comprehensive Kraken REST API client for market data.
    
    Provides access to all public market data endpoints including:
    - Server time
    - System status  
    - Asset information
    - Tradeable asset pairs
    - Ticker information
    - OHLC data
    - Order book data
    - Recent trades
    - Recent spread data
    """
    
    BASE_URL = "https://api.kraken.com"
    API_VERSION = "0"
    
    # Public endpoints
    ENDPOINTS = {
        'time': '/0/public/Time',
        'system_status': '/0/public/SystemStatus',
        'assets': '/0/public/Assets',
        'asset_pairs': '/0/public/AssetPairs', 
        'ticker': '/0/public/Ticker',
        'ohlc': '/0/public/OHLC',
        'depth': '/0/public/Depth',
        'trades': '/0/public/Trades',
        'spread': '/0/public/Spread'
    }
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the Kraken REST client.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts (default: 3)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
        self._session = requests.Session()
        
        # Set up session headers
        self._session.headers.update({
            "User-Agent": "Kraken-Data-Ingestion/1.0"
        })
        
        self.logger.info("🔧 Kraken REST client initialized")
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the Kraken REST API with retries and error handling.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            API response data
            
        Raises:
            Exception: For API errors or network issues
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(f"📡 Making request to {endpoint} (attempt {attempt + 1})")
                
                response = self._session.get(
                    url,
                    params=params or {},
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
    
    def get_server_time(self) -> Dict[str, Any]:
        """
        Get the server's time.
        
        Returns:
            Dictionary containing unixtime and rfc1123 timestamps
        """
        try:
            result = self._make_request(self.ENDPOINTS['time'])
            self.logger.debug("⏰ Retrieved server time")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get server time: {e}")
            raise
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the current system status or trading mode.
        
        Returns:
            Dictionary containing status and timestamp
        """
        try:
            result = self._make_request(self.ENDPOINTS['system_status'])
            self.logger.debug("🟢 Retrieved system status")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get system status: {e}")
            raise
    
    def get_assets(self, assets: Optional[List[str]] = None, asset_class: str = "currency") -> Dict[str, Any]:
        """
        Get information about the assets that are available for deposit, withdrawal, trading and earn.
        
        Args:
            assets: List of assets to query (default: all)
            asset_class: Asset class (default: currency)
            
        Returns:
            Dictionary mapping asset names to their information
        """
        params = {"aclass": asset_class}
        if assets:
            params["asset"] = ",".join(assets)
        
        try:
            result = self._make_request(self.ENDPOINTS['assets'], params)
            asset_count = len(result)
            self.logger.info(f"📊 Retrieved information for {asset_count} assets")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get assets: {e}")
            raise
    
    def get_asset_pairs(self, pairs: Optional[List[str]] = None, info: str = "info") -> Dict[str, Any]:
        """
        Get tradeable asset pairs.
        
        Args:
            pairs: List of asset pairs to query (default: all)
            info: Info to retrieve (info, leverage, fees, margin)
            
        Returns:
            Dictionary mapping pair names to their information
        """
        params = {"info": info}
        if pairs:
            params["pair"] = ",".join(pairs)
        
        try:
            result = self._make_request(self.ENDPOINTS['asset_pairs'], params)
            pair_count = len(result)
            self.logger.info(f"📊 Retrieved information for {pair_count} trading pairs")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get asset pairs: {e}")
            raise
    
    def get_ticker(self, pairs: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get ticker information for asset pairs.
        
        Args:
            pairs: List of asset pairs to query (default: all)
            
        Returns:
            Dictionary mapping pair names to their ticker data
        """
        params = {}
        if pairs:
            params["pair"] = ",".join(pairs)
        
        try:
            result = self._make_request(self.ENDPOINTS['ticker'], params)
            ticker_count = len(result)
            self.logger.info(f"📈 Retrieved ticker data for {ticker_count} pairs")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get ticker data: {e}")
            raise
    
    def get_ohlc(self, pair: str, interval: int = 1, since: Optional[int] = None) -> Dict[str, Any]:
        """
        Get OHLC (candlestick) data for a pair.
        
        Args:
            pair: Asset pair to get OHLC data for
            interval: Time frame interval in minutes (1, 5, 15, 30, 60, 240, 1440, 10080, 21600)
            since: Return data since this timestamp
            
        Returns:
            Dictionary containing OHLC data and last timestamp
        """
        params = {"pair": pair, "interval": interval}
        if since:
            params["since"] = since
        
        try:
            result = self._make_request(self.ENDPOINTS['ohlc'], params)
            if pair in result:
                candle_count = len(result[pair])
                self.logger.info(f"📊 Retrieved {candle_count} OHLC candles for {pair}")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get OHLC data for {pair}: {e}")
            raise
    
    def get_order_book(self, pair: str, count: int = 100) -> Dict[str, Any]:
        """
        Get order book (market depth) for a pair.
        
        Args:
            pair: Asset pair to get order book for
            count: Maximum number of asks/bids (default: 100)
            
        Returns:
            Dictionary containing asks, bids arrays
        """
        params = {"pair": pair, "count": count}
        
        try:
            result = self._make_request(self.ENDPOINTS['depth'], params)
            if pair in result:
                asks_count = len(result[pair].get('asks', []))
                bids_count = len(result[pair].get('bids', []))
                self.logger.info(f"📖 Retrieved order book for {pair}: {asks_count} asks, {bids_count} bids")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get order book for {pair}: {e}")
            raise
    
    def get_recent_trades(self, pair: str, since: Optional[int] = None, count: Optional[int] = None) -> Dict[str, Any]:
        """
        Get recent trades for a pair.
        
        Args:
            pair: Asset pair to get trade data for
            since: Return trade data since this timestamp  
            count: Return only this many trades (optional)
            
        Returns:
            Dictionary containing trades array and last timestamp
        """
        params = {"pair": pair}
        if since:
            params["since"] = since
        if count:
            params["count"] = count
        
        try:
            result = self._make_request(self.ENDPOINTS['trades'], params)
            if pair in result:
                trade_count = len(result[pair])
                self.logger.info(f"💱 Retrieved {trade_count} recent trades for {pair}")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get recent trades for {pair}: {e}")
            raise
    
    def get_recent_spreads(self, pair: str, since: Optional[int] = None) -> Dict[str, Any]:
        """
        Get recent spread data for a pair.
        
        Args:
            pair: Asset pair to get spread data for
            since: Return spread data since this timestamp
            
        Returns:
            Dictionary containing spreads array and last timestamp
        """
        params = {"pair": pair}
        if since:
            params["since"] = since
        
        try:
            result = self._make_request(self.ENDPOINTS['spread'], params)
            if pair in result:
                spread_count = len(result[pair])
                self.logger.info(f"📏 Retrieved {spread_count} spread entries for {pair}")
            return result
        except Exception as e:
            self.logger.error(f"❌ Failed to get spread data for {pair}: {e}")
            raise
    
    def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            self._session.close()
            self.logger.info("🔒 Kraken REST client session closed")
