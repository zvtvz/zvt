# -*- coding: utf-8 -*-
"""
Crypto Live Data Stream Service
Handles real-time WebSocket streams from multiple exchanges
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set
from concurrent.futures import ThreadPoolExecutor
import websocket
import pandas as pd
from threading import Thread, Lock
from queue import Queue, Empty

from zvt.contract import IntervalLevel
from zvt.domain.crypto import CryptoPair, CryptoPerp
from zvt.utils.time_utils import to_pd_timestamp

logger = logging.getLogger(__name__)


class StreamManager:
    """Manages WebSocket connections for a single exchange"""
    
    def __init__(self, exchange: str, config: Dict):
        self.exchange = exchange
        self.config = config
        self.ws: Optional[websocket.WebSocketApp] = None
        self.is_connected = False
        self.subscriptions: Set[str] = set()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5.0
        
        # Message handling
        self.message_queue: Queue = Queue(maxsize=10000)
        self.message_handlers: Dict[str, Callable] = {}
        
        # Statistics
        self.stats = {
            "messages_received": 0,
            "messages_processed": 0,
            "connection_failures": 0,
            "last_message_time": None
        }

    def connect(self):
        """Establish WebSocket connection"""
        if self.is_connected:
            return
            
        try:
            ws_url = self.config.get("ws_url")
            if not ws_url:
                raise ValueError(f"No WebSocket URL configured for {self.exchange}")
                
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Run WebSocket in separate thread
            ws_thread = Thread(target=self.ws.run_forever, daemon=True)
            ws_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.exchange}: {e}")
            self.stats["connection_failures"] += 1

    def _on_open(self, ws):
        """WebSocket connection opened"""
        logger.info(f"Connected to {self.exchange}")
        self.is_connected = True
        self.reconnect_attempts = 0
        
        # Resubscribe to all channels
        for subscription in self.subscriptions:
            self._send_subscription(subscription)

    def _on_message(self, ws, message):
        """WebSocket message received"""
        try:
            self.stats["messages_received"] += 1
            self.stats["last_message_time"] = datetime.now()
            
            # Queue message for processing
            if not self.message_queue.full():
                self.message_queue.put(message)
            else:
                logger.warning(f"Message queue full for {self.exchange}, dropping message")
                
        except Exception as e:
            logger.error(f"Error handling message from {self.exchange}: {e}")

    def _on_error(self, ws, error):
        """WebSocket error occurred"""
        logger.error(f"WebSocket error for {self.exchange}: {error}")
        self.stats["connection_failures"] += 1

    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket connection closed"""
        logger.warning(f"Connection closed for {self.exchange}: {close_status_code} - {close_msg}")
        self.is_connected = False
        
        # Attempt reconnection
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"Attempting reconnection {self.reconnect_attempts}/{self.max_reconnect_attempts}")
            time.sleep(self.reconnect_delay)
            self.connect()

    def subscribe(self, channel: str, symbols: List[str]):
        """Subscribe to a data stream"""
        subscription = f"{channel}:{','.join(symbols)}"
        self.subscriptions.add(subscription)
        
        if self.is_connected:
            self._send_subscription(subscription)

    def _send_subscription(self, subscription: str):
        """Send subscription message to exchange"""
        channel, symbols_str = subscription.split(":", 1)
        symbols = symbols_str.split(",")
        
        # Format subscription based on exchange
        if self.exchange == "binance":
            sub_message = {
                "method": "SUBSCRIBE",
                "params": [f"{symbol.lower().replace('/', '')}@{channel}" for symbol in symbols],
                "id": int(time.time())
            }
        elif self.exchange == "okx":
            sub_message = {
                "op": "subscribe",
                "args": [{"channel": channel, "instId": symbol} for symbol in symbols]
            }
        else:
            # Generic format
            sub_message = {
                "subscribe": channel,
                "symbols": symbols
            }
        
        if self.ws and self.is_connected:
            self.ws.send(json.dumps(sub_message))
            logger.info(f"Subscribed to {subscription} on {self.exchange}")

    def get_message(self, timeout: float = 1.0) -> Optional[str]:
        """Get message from queue"""
        try:
            return self.message_queue.get(timeout=timeout)
        except Empty:
            return None

    def process_messages(self, processor: Callable[[str], Any]):
        """Process messages continuously"""
        while True:
            message = self.get_message()
            if message:
                try:
                    processor(message)
                    self.stats["messages_processed"] += 1
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

    def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            self.ws.close()
        self.is_connected = False


class CryptoStreamService:
    """
    Multi-exchange cryptocurrency data streaming service
    
    Features:
    - Real-time price feeds (ticker, kline, trades)
    - Order book depth streams  
    - Funding rate and liquidation data
    - Multi-exchange aggregation
    - Connection management and failover
    - Data validation and buffering
    """
    
    def __init__(
        self,
        exchanges: List[str] = None,
        buffer_size: int = 10000,
        enable_heartbeat: bool = True,
        heartbeat_interval: float = 30.0
    ):
        self.exchanges = exchanges or ["binance", "okx", "bybit"]
        self.buffer_size = buffer_size
        self.enable_heartbeat = enable_heartbeat
        self.heartbeat_interval = heartbeat_interval
        
        # Exchange configurations
        self.exchange_configs = {
            "binance": {
                "ws_url": "wss://stream.binance.com:9443/ws/!ticker@arr",
                "channels": {
                    "ticker": "ticker",
                    "kline": "kline_1m", 
                    "trades": "trade",
                    "depth": "depth20@100ms"
                }
            },
            "okx": {
                "ws_url": "wss://ws.okx.com:8443/ws/v5/public",
                "channels": {
                    "ticker": "tickers",
                    "kline": "candle1m",
                    "trades": "trades", 
                    "depth": "books5"
                }
            },
            "bybit": {
                "ws_url": "wss://stream.bybit.com/v5/public/spot",
                "channels": {
                    "ticker": "tickers",
                    "kline": "kline.1",
                    "trades": "publicTrade",
                    "depth": "orderbook.50"
                }
            }
        }
        
        # Stream managers
        self.stream_managers: Dict[str, StreamManager] = {}
        self._initialize_managers()
        
        # Data handlers
        self.data_handlers: Dict[str, List[Callable]] = {
            "ticker": [],
            "kline": [],
            "trades": [],
            "depth": [],
            "funding": []
        }
        
        # Data buffers
        self.data_buffers: Dict[str, pd.DataFrame] = {}
        self.buffer_lock = Lock()
        
        # Processing threads
        self.processing_threads: List[Thread] = []
        self.is_running = False
        
        # Statistics
        self.global_stats = {
            "total_messages": 0,
            "messages_per_second": 0.0,
            "active_connections": 0,
            "start_time": None
        }

    def _initialize_managers(self):
        """Initialize stream managers for each exchange"""
        for exchange in self.exchanges:
            config = self.exchange_configs.get(exchange, {})
            if config:
                self.stream_managers[exchange] = StreamManager(exchange, config)
            else:
                logger.warning(f"No configuration found for exchange: {exchange}")

    def start(self):
        """Start all stream connections and processing"""
        logger.info("Starting crypto stream service")
        self.is_running = True
        self.global_stats["start_time"] = datetime.now()
        
        # Connect to all exchanges
        for exchange, manager in self.stream_managers.items():
            try:
                manager.connect()
                time.sleep(1)  # Stagger connections
            except Exception as e:
                logger.error(f"Failed to start {exchange} stream: {e}")
        
        # Start message processing threads
        for exchange, manager in self.stream_managers.items():
            thread = Thread(
                target=self._process_exchange_messages,
                args=(exchange, manager),
                daemon=True
            )
            thread.start()
            self.processing_threads.append(thread)
        
        # Start heartbeat monitoring
        if self.enable_heartbeat:
            heartbeat_thread = Thread(target=self._heartbeat_monitor, daemon=True)
            heartbeat_thread.start()
            self.processing_threads.append(heartbeat_thread)
        
        logger.info(f"Stream service started with {len(self.stream_managers)} exchanges")

    def stop(self):
        """Stop all streams and processing"""
        logger.info("Stopping crypto stream service")
        self.is_running = False
        
        # Disconnect all managers
        for manager in self.stream_managers.values():
            manager.disconnect()
        
        # Wait for processing threads to finish
        for thread in self.processing_threads:
            thread.join(timeout=5.0)
        
        logger.info("Stream service stopped")

    def subscribe_ticker(self, symbols: List[str], exchanges: List[str] = None):
        """Subscribe to ticker (price) updates"""
        exchanges = exchanges or list(self.stream_managers.keys())
        
        for exchange in exchanges:
            if exchange in self.stream_managers:
                manager = self.stream_managers[exchange]
                channel = self.exchange_configs[exchange]["channels"]["ticker"]
                manager.subscribe(channel, symbols)
                logger.info(f"Subscribed to ticker for {symbols} on {exchange}")

    def subscribe_klines(
        self,
        symbols: List[str], 
        intervals: List[str] = None,
        exchanges: List[str] = None
    ):
        """Subscribe to candlestick/kline data"""
        intervals = intervals or ["1m"]
        exchanges = exchanges or list(self.stream_managers.keys())
        
        for exchange in exchanges:
            if exchange in self.stream_managers:
                manager = self.stream_managers[exchange]
                for interval in intervals:
                    channel = f"kline_{interval}"
                    manager.subscribe(channel, symbols)
                    logger.info(f"Subscribed to {interval} klines for {symbols} on {exchange}")

    def subscribe_trades(self, symbols: List[str], exchanges: List[str] = None):
        """Subscribe to trade updates"""
        exchanges = exchanges or list(self.stream_managers.keys())
        
        for exchange in exchanges:
            if exchange in self.stream_managers:
                manager = self.stream_managers[exchange]
                channel = self.exchange_configs[exchange]["channels"]["trades"]
                manager.subscribe(channel, symbols)
                logger.info(f"Subscribed to trades for {symbols} on {exchange}")

    def subscribe_orderbook(
        self,
        symbols: List[str],
        depth: int = 20,
        exchanges: List[str] = None
    ):
        """Subscribe to order book depth updates"""
        exchanges = exchanges or list(self.stream_managers.keys())
        
        for exchange in exchanges:
            if exchange in self.stream_managers:
                manager = self.stream_managers[exchange]
                channel = f"depth{depth}"
                manager.subscribe(channel, symbols)
                logger.info(f"Subscribed to depth-{depth} for {symbols} on {exchange}")

    def add_data_handler(self, data_type: str, handler: Callable[[Dict], None]):
        """Add handler for specific data type"""
        if data_type in self.data_handlers:
            self.data_handlers[data_type].append(handler)
            logger.info(f"Added handler for {data_type} data")
        else:
            logger.warning(f"Unknown data type: {data_type}")

    def _process_exchange_messages(self, exchange: str, manager: StreamManager):
        """Process messages from a specific exchange"""
        logger.info(f"Started message processor for {exchange}")
        
        while self.is_running:
            try:
                message = manager.get_message(timeout=1.0)
                if message:
                    self._handle_message(exchange, message)
                    self.global_stats["total_messages"] += 1
            except Exception as e:
                logger.error(f"Error in {exchange} message processor: {e}")
                time.sleep(1)
        
        logger.info(f"Message processor for {exchange} stopped")

    def _handle_message(self, exchange: str, message: str):
        """Parse and route message to appropriate handlers"""
        try:
            data = json.loads(message)
            message_type = self._determine_message_type(exchange, data)
            
            if message_type and message_type in self.data_handlers:
                parsed_data = self._parse_message(exchange, message_type, data)
                if parsed_data:
                    # Store in buffer
                    self._buffer_data(message_type, parsed_data)
                    
                    # Call handlers
                    for handler in self.data_handlers[message_type]:
                        try:
                            handler(parsed_data)
                        except Exception as e:
                            logger.error(f"Handler error for {message_type}: {e}")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON from {exchange}: {e}")
        except Exception as e:
            logger.error(f"Message handling error for {exchange}: {e}")

    def _determine_message_type(self, exchange: str, data: Dict) -> Optional[str]:
        """Determine the type of message based on exchange format"""
        if exchange == "binance":
            if "e" in data:
                event_type = data["e"]
                type_map = {
                    "24hrTicker": "ticker",
                    "kline": "kline", 
                    "trade": "trades",
                    "depthUpdate": "depth"
                }
                return type_map.get(event_type)
        elif exchange == "okx":
            if "arg" in data and "channel" in data["arg"]:
                channel = data["arg"]["channel"]
                type_map = {
                    "tickers": "ticker",
                    "candle1m": "kline",
                    "trades": "trades",
                    "books5": "depth"
                }
                return type_map.get(channel)
        
        return None

    def _parse_message(self, exchange: str, message_type: str, data: Dict) -> Optional[Dict]:
        """Parse message data into standardized format"""
        try:
            if message_type == "ticker":
                return self._parse_ticker(exchange, data)
            elif message_type == "kline":
                return self._parse_kline(exchange, data)
            elif message_type == "trades":
                return self._parse_trade(exchange, data)
            elif message_type == "depth":
                return self._parse_depth(exchange, data)
        except Exception as e:
            logger.error(f"Error parsing {message_type} from {exchange}: {e}")
        
        return None

    def _parse_ticker(self, exchange: str, data: Dict) -> Dict:
        """Parse ticker data"""
        if exchange == "binance":
            return {
                "exchange": exchange,
                "symbol": data.get("s"),
                "price": float(data.get("c", 0)),
                "volume": float(data.get("v", 0)),
                "high": float(data.get("h", 0)),
                "low": float(data.get("l", 0)),
                "change": float(data.get("P", 0)),
                "timestamp": pd.Timestamp.now()
            }
        elif exchange == "okx":
            ticker_data = data.get("data", [{}])[0]
            return {
                "exchange": exchange,
                "symbol": ticker_data.get("instId"),
                "price": float(ticker_data.get("last", 0)),
                "volume": float(ticker_data.get("vol24h", 0)),
                "high": float(ticker_data.get("high24h", 0)),
                "low": float(ticker_data.get("low24h", 0)),
                "timestamp": pd.Timestamp.now()
            }
        
        return {}

    def _parse_kline(self, exchange: str, data: Dict) -> Dict:
        """Parse kline/candlestick data"""
        if exchange == "binance":
            k = data.get("k", {})
            return {
                "exchange": exchange,
                "symbol": k.get("s"),
                "timestamp": pd.Timestamp(int(k.get("t", 0)), unit="ms"),
                "open": float(k.get("o", 0)),
                "high": float(k.get("h", 0)),
                "low": float(k.get("l", 0)),
                "close": float(k.get("c", 0)),
                "volume": float(k.get("v", 0)),
                "is_closed": k.get("x", False)
            }
        elif exchange == "okx":
            candle_data = data.get("data", [{}])[0]
            return {
                "exchange": exchange,
                "symbol": data.get("arg", {}).get("instId"),
                "timestamp": pd.Timestamp(int(candle_data[0]), unit="ms"),
                "open": float(candle_data[1]),
                "high": float(candle_data[2]),
                "low": float(candle_data[3]),
                "close": float(candle_data[4]),
                "volume": float(candle_data[5])
            }
        
        return {}

    def _parse_trade(self, exchange: str, data: Dict) -> Dict:
        """Parse trade data"""
        if exchange == "binance":
            return {
                "exchange": exchange,
                "symbol": data.get("s"),
                "trade_id": data.get("t"),
                "price": float(data.get("p", 0)),
                "quantity": float(data.get("q", 0)),
                "timestamp": pd.Timestamp(int(data.get("T", 0)), unit="ms"),
                "is_buyer_maker": data.get("m", False)
            }
        
        return {}

    def _parse_depth(self, exchange: str, data: Dict) -> Dict:
        """Parse order book depth data"""
        if exchange == "binance":
            return {
                "exchange": exchange,
                "symbol": data.get("s"),
                "bids": [[float(p), float(q)] for p, q in data.get("b", [])],
                "asks": [[float(p), float(q)] for p, q in data.get("a", [])],
                "timestamp": pd.Timestamp.now()
            }
        
        return {}

    def _buffer_data(self, data_type: str, data: Dict):
        """Store data in buffer for later retrieval"""
        with self.buffer_lock:
            if data_type not in self.data_buffers:
                self.data_buffers[data_type] = pd.DataFrame()
            
            # Convert to DataFrame and append
            df = pd.DataFrame([data])
            self.data_buffers[data_type] = pd.concat([
                self.data_buffers[data_type], df
            ], ignore_index=True)
            
            # Limit buffer size
            if len(self.data_buffers[data_type]) > self.buffer_size:
                excess = len(self.data_buffers[data_type]) - self.buffer_size
                self.data_buffers[data_type] = self.data_buffers[data_type].iloc[excess:]

    def get_buffered_data(self, data_type: str, limit: int = None) -> pd.DataFrame:
        """Get buffered data of specific type"""
        with self.buffer_lock:
            df = self.data_buffers.get(data_type, pd.DataFrame())
            if limit:
                return df.tail(limit).copy()
            return df.copy()

    def clear_buffer(self, data_type: str = None):
        """Clear data buffer"""
        with self.buffer_lock:
            if data_type:
                if data_type in self.data_buffers:
                    self.data_buffers[data_type] = pd.DataFrame()
            else:
                self.data_buffers.clear()

    def _heartbeat_monitor(self):
        """Monitor connection health and statistics"""
        logger.info("Started heartbeat monitor")
        
        last_message_count = 0
        
        while self.is_running:
            try:
                time.sleep(self.heartbeat_interval)
                
                # Update statistics
                current_messages = self.global_stats["total_messages"]
                messages_in_period = current_messages - last_message_count
                self.global_stats["messages_per_second"] = messages_in_period / self.heartbeat_interval
                last_message_count = current_messages
                
                # Count active connections
                active_connections = sum(
                    1 for manager in self.stream_managers.values() 
                    if manager.is_connected
                )
                self.global_stats["active_connections"] = active_connections
                
                # Log health status
                logger.info(
                    f"Stream health: {active_connections}/{len(self.stream_managers)} connections, "
                    f"{self.global_stats['messages_per_second']:.1f} msg/s, "
                    f"{current_messages} total messages"
                )
                
                # Check for stale connections
                for exchange, manager in self.stream_managers.items():
                    if manager.stats["last_message_time"]:
                        time_since_last = datetime.now() - manager.stats["last_message_time"]
                        if time_since_last > timedelta(minutes=5):
                            logger.warning(f"No messages from {exchange} for {time_since_last}")
                
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
        
        logger.info("Heartbeat monitor stopped")

    def get_stream_stats(self) -> Dict:
        """Get comprehensive streaming statistics"""
        stats = self.global_stats.copy()
        stats["exchange_stats"] = {}
        
        for exchange, manager in self.stream_managers.items():
            stats["exchange_stats"][exchange] = {
                "connected": manager.is_connected,
                "subscriptions": len(manager.subscriptions),
                **manager.stats
            }
        
        # Buffer statistics
        stats["buffer_stats"] = {}
        for data_type, df in self.data_buffers.items():
            stats["buffer_stats"][data_type] = len(df)
        
        return stats