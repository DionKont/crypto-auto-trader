"""
Kraken WebSocket Client for Real-time Market Data

This module provides WebSocket connectivity to Kraken's real-time market data feeds
including ticker, order book, trades, OHLC, and spread data streams.
"""

import json
import logging
import asyncio
import websockets
import ssl
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
import threading
from dataclasses import dataclass
from enum import Enum


class SubscriptionType(Enum):
    """WebSocket subscription types."""
    TICKER = "ticker"
    OHLC = "ohlc"
    TRADE = "trade"
    BOOK = "book"
    SPREAD = "spread"


@dataclass
class Subscription:
    """WebSocket subscription configuration."""
    name: SubscriptionType
    pairs: List[str]
    depth: Optional[int] = None  # For book subscriptions
    interval: Optional[int] = None  # For OHLC subscriptions (1, 5, 15, 30, 60, 240, 1440, 10080, 21600)


class KrakenWebSocketClient:
    """
    Real-time WebSocket client for Kraken market data.
    
    Provides access to all public WebSocket feeds:
    - Ticker: Real-time price updates
    - Order Book: Live order book updates with configurable depth
    - Trades: Real-time trade execution data
    - OHLC: Real-time OHLC/candlestick data
    - Spread: Real-time bid/ask spread data
    
    Features:
    - Automatic reconnection
    - Subscription management
    - Event-driven callbacks
    - Error handling and logging
    - Rate limiting compliance
    """
    
    WEBSOCKET_URL = "wss://ws.kraken.com/v2"
    
    def __init__(self, callback: Optional[Callable[[str, Dict], None]] = None):
        """
        Initialize the WebSocket client.
        
        Args:
            callback: Optional callback function for handling messages
        """
        self.callback = callback
        self.logger = logging.getLogger(__name__)
        
        # Connection state
        self.websocket = None
        self.connected = False
        self.reconnecting = False
        
        # Subscription management
        self.subscriptions: Dict[str, Subscription] = {}
        self.subscription_status: Dict[str, str] = {}
        
        # Event loop and thread management
        self.loop = None
        self.thread = None
        self.stop_event = threading.Event()
        
        # Message handlers
        self.message_handlers = {
            'heartbeat': self._handle_heartbeat,
            'systemStatus': self._handle_system_status,
            'subscriptionStatus': self._handle_subscription_status,
        }
        
        self.logger.info("🔧 Kraken WebSocket client initialized")
    
    def start(self) -> None:
        """Start the WebSocket client in a separate thread."""
        if self.thread and self.thread.is_alive():
            self.logger.warning("⚠️  WebSocket client already running")
            return
        
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
        self.logger.info("🚀 WebSocket client thread started")
    
    def stop(self) -> None:
        """Stop the WebSocket client."""
        self.logger.info("🛑 Stopping WebSocket client...")
        self.stop_event.set()
        
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._disconnect(), self.loop)
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        
        self.logger.info("✅ WebSocket client stopped")
    
    def _run_event_loop(self) -> None:
        """Run the event loop in a separate thread."""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._connect_with_retry())
        except Exception as e:
            self.logger.error(f"❌ Event loop error: {e}")
        finally:
            if self.loop and not self.loop.is_closed():
                self.loop.close()
    
    async def _connect_with_retry(self) -> None:
        """Connect with automatic retry logic."""
        retry_count = 0
        max_retries = 5
        
        while not self.stop_event.is_set() and retry_count < max_retries:
            try:
                await self._connect()
                retry_count = 0  # Reset on successful connection
                
                # Keep connection alive
                while not self.stop_event.is_set() and self.connected:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                retry_count += 1
                wait_time = min(2 ** retry_count, 30)  # Exponential backoff, max 30s
                
                self.logger.error(f"❌ WebSocket connection error: {e}")
                
                if retry_count < max_retries:
                    self.logger.info(f"🔄 Retrying connection in {wait_time}s (attempt {retry_count + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"❌ Max retries ({max_retries}) exceeded. Giving up.")
                    break
    
    async def _connect(self) -> None:
        """Establish WebSocket connection."""
        self.logger.info(f"🔗 Connecting to {self.WEBSOCKET_URL}...")
        
        # Create SSL context that doesn't verify certificates (for development)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        self.websocket = await websockets.connect(
            self.WEBSOCKET_URL,
            ssl=ssl_context,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10
        )
        
        self.connected = True
        self.logger.info("✅ WebSocket connected successfully")
        
        # Start message handler
        await self._message_handler()
    
    async def _disconnect(self) -> None:
        """Disconnect WebSocket."""
        if self.websocket:
            self.connected = False
            await self.websocket.close()
            self.websocket = None
            self.logger.info("🔌 WebSocket disconnected")
    
    async def _message_handler(self) -> None:
        """Handle incoming WebSocket messages."""
        try:
            async for message in self.websocket:
                if self.stop_event.is_set():
                    break
                
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"⚠️  Invalid JSON received: {e}")
                except Exception as e:
                    self.logger.error(f"❌ Error processing message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("⚠️  WebSocket connection closed")
            self.connected = False
        except Exception as e:
            self.logger.error(f"❌ Message handler error: {e}")
            self.connected = False
    
    async def _process_message(self, data: Dict[str, Any]) -> None:
        """Process incoming WebSocket message."""
        if not isinstance(data, dict):
            return
        
        # Handle different message types based on Kraken v2 format
        if 'channel' in data:
            channel = data['channel']
            message_type = data.get('type', 'unknown')
            
            if self.callback:
                try:
                    self.callback(channel, data)
                except Exception as e:
                    self.logger.error(f"❌ Callback error: {e}")
            
            # Handle specific channels
            if channel in self.message_handlers:
                await self.message_handlers[channel](data)
        
        # Handle subscription responses
        elif 'method' in data:
            method = data['method']
            if method in ['subscribe', 'unsubscribe']:
                await self._handle_subscription_response(data)
        
        # Log unhandled messages
        else:
            self.logger.debug(f"📨 Unhandled message: {data}")
    
    async def _handle_heartbeat(self, data: Dict[str, Any]) -> None:
        """Handle heartbeat messages."""
        self.logger.debug("💓 Heartbeat received")
    
    async def _handle_system_status(self, data: Dict[str, Any]) -> None:
        """Handle system status messages."""
        status = data.get('data', {}).get('status', 'unknown')
        self.logger.info(f"🔔 System status: {status}")
    
    async def _handle_subscription_status(self, data: Dict[str, Any]) -> None:
        """Handle subscription status messages."""
        sub_data = data.get('data', {})
        channel = sub_data.get('channel', 'unknown')
        status = sub_data.get('status', 'unknown')
        self.subscription_status[channel] = status
        self.logger.info(f"📡 Subscription {channel}: {status}")
    
    async def _handle_subscription_response(self, data: Dict[str, Any]) -> None:
        """Handle subscription/unsubscription responses."""
        method = data.get('method', '')
        success = data.get('success', False)
        error = data.get('error', '')
        
        if success:
            self.logger.info(f"✅ {method.capitalize()} successful")
        else:
            self.logger.error(f"❌ {method.capitalize()} failed: {error}")
    
    async def _send_message(self, message: Dict[str, Any]) -> bool:
        """Send message to WebSocket."""
        if not self.connected or not self.websocket:
            self.logger.warning("⚠️  WebSocket not connected")
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            self.logger.debug(f"📤 Sent: {message}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Send error: {e}")
            return False
    
    def subscribe_ticker(self, pairs: List[str], event_trigger: str = "trades") -> bool:
        """Subscribe to ticker updates for the specified pairs."""
        if not self.connected:
            self.logger.warning("⚠️  WebSocket not connected")
            return False
        
        message = {
            "method": "subscribe",
            "params": {
                "channel": "ticker",
                "symbol": pairs,
                "event_trigger": event_trigger,
                "snapshot": True
            }
        }
        
        # Send in async context
        if self.loop:
            future = asyncio.run_coroutine_threadsafe(self._send_message(message), self.loop)
            try:
                return future.result(timeout=5.0)
            except:
                return False
        return False
    
    def subscribe_ohlc(self, pairs: List[str], interval: int = 1) -> bool:
        """Subscribe to OHLC updates for the specified pairs."""
        if not self.connected:
            self.logger.warning("⚠️  WebSocket not connected")
            return False
        
        message = {
            "method": "subscribe",
            "params": {
                "channel": "ohlc",
                "symbol": pairs,
                "interval": interval,
                "snapshot": True
            }
        }
        
        if self.loop:
            future = asyncio.run_coroutine_threadsafe(self._send_message(message), self.loop)
            try:
                return future.result(timeout=5.0)
            except:
                return False
        return False
    
    def subscribe_trades(self, pairs: List[str]) -> bool:
        """Subscribe to trade updates for the specified pairs."""
        if not self.connected:
            self.logger.warning("⚠️  WebSocket not connected")
            return False
        
        message = {
            "method": "subscribe",
            "params": {
                "channel": "trade",
                "symbol": pairs,
                "snapshot": True
            }
        }
        
        if self.loop:
            future = asyncio.run_coroutine_threadsafe(self._send_message(message), self.loop)
            try:
                return future.result(timeout=5.0)
            except:
                return False
        return False
    
    def subscribe_book(self, pairs: List[str], depth: int = 10) -> bool:
        """Subscribe to order book updates for the specified pairs."""
        if not self.connected:
            self.logger.warning("⚠️  WebSocket not connected")
            return False
        
        message = {
            "method": "subscribe",
            "params": {
                "channel": "book",
                "symbol": pairs,
                "depth": depth,
                "snapshot": True
            }
        }
        
        if self.loop:
            future = asyncio.run_coroutine_threadsafe(self._send_message(message), self.loop)
            try:
                return future.result(timeout=5.0)
            except:
                return False
        return False
    
    def subscribe_spread(self, pairs: List[str]) -> bool:
        """Subscribe to spread updates for the specified pairs."""
        if not self.connected:
            self.logger.warning("⚠️  WebSocket not connected")
            return False
        
        message = {
            "method": "subscribe",
            "params": {
                "channel": "spread",
                "symbol": pairs,
                "snapshot": True
            }
        }
        
        if self.loop:
            future = asyncio.run_coroutine_threadsafe(self._send_message(message), self.loop)
            try:
                return future.result(timeout=5.0)
            except:
                return False
        return False
    
    def unsubscribe_all(self) -> None:
        """Unsubscribe from all WebSocket feeds."""
        self.logger.info("🔄 Unsubscribing from all feeds...")
        # For simplicity, we'll just disconnect and reconnect
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._disconnect(), self.loop)
    
    def get_subscription_status(self) -> Dict[str, str]:
        """Get current WebSocket subscription status."""
        return self.subscription_status.copy()
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.connected
