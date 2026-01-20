# -*- coding: utf-8 -*-
"""
Tests for Crypto Stream Service
Comprehensive testing of real-time data streaming functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json
import time
from datetime import datetime
import pandas as pd
from threading import Thread
import websocket

from zvt.services.crypto.stream_service import CryptoStreamService, StreamManager


class TestStreamManager:
    """Test suite for StreamManager class"""

    @pytest.fixture
    def stream_manager(self):
        """Create StreamManager instance for testing"""
        config = {
            "ws_url": "wss://test.exchange.com/ws",
            "channels": {
                "ticker": "ticker",
                "trades": "trade"
            }
        }
        return StreamManager("test_exchange", config)

    def test_initialization(self, stream_manager):
        """Test StreamManager initialization"""
        assert stream_manager.exchange == "test_exchange"
        assert not stream_manager.is_connected
        assert stream_manager.reconnect_attempts == 0
        assert len(stream_manager.subscriptions) == 0
        assert stream_manager.stats["messages_received"] == 0

    @patch('websocket.WebSocketApp')
    def test_websocket_connection(self, mock_ws_app, stream_manager):
        """Test WebSocket connection establishment"""
        mock_ws_instance = Mock()
        mock_ws_app.return_value = mock_ws_instance

        stream_manager.connect()

        # Should create WebSocketApp with correct parameters
        mock_ws_app.assert_called_once_with(
            "wss://test.exchange.com/ws",
            on_open=stream_manager._on_open,
            on_message=stream_manager._on_message,
            on_error=stream_manager._on_error,
            on_close=stream_manager._on_close
        )

    def test_on_open_callback(self, stream_manager):
        """Test WebSocket on_open callback"""
        # Add a subscription before connection
        stream_manager.subscriptions.add("ticker:BTC/USDT")
        
        mock_ws = Mock()
        mock_ws.send = Mock()
        stream_manager.ws = mock_ws
        
        # Simulate connection opening
        stream_manager._on_open(mock_ws)
        
        assert stream_manager.is_connected is True
        assert stream_manager.reconnect_attempts == 0
        
        # Should attempt to resubscribe
        mock_ws.send.assert_called()

    def test_on_message_callback(self, stream_manager):
        """Test WebSocket message handling"""
        test_message = '{"test": "data"}'
        
        # Simulate receiving message
        stream_manager._on_message(None, test_message)
        
        assert stream_manager.stats["messages_received"] == 1
        assert stream_manager.stats["last_message_time"] is not None
        
        # Message should be queued
        queued_message = stream_manager.get_message(timeout=0.1)
        assert queued_message == test_message

    def test_message_queue_overflow(self, stream_manager):
        """Test message queue overflow handling"""
        # Fill up the queue (default size is 10000, we'll mock a smaller size)
        stream_manager.message_queue.maxsize = 2
        
        # Add messages beyond capacity
        stream_manager._on_message(None, "message1")
        stream_manager._on_message(None, "message2")
        stream_manager._on_message(None, "message3")  # Should be dropped
        
        # Should have received all messages but queue should not overflow
        assert stream_manager.stats["messages_received"] == 3
        assert stream_manager.message_queue.qsize() <= 2

    def test_subscription_management(self, stream_manager):
        """Test subscription and message sending"""
        mock_ws = Mock()
        mock_ws.send = Mock()
        stream_manager.ws = mock_ws
        stream_manager.is_connected = True
        
        # Test subscription
        stream_manager.subscribe("ticker", ["BTC/USDT", "ETH/USDT"])
        
        # Should add to subscriptions
        assert len(stream_manager.subscriptions) == 1
        assert "ticker:BTC/USDT,ETH/USDT" in stream_manager.subscriptions
        
        # Should send subscription message
        mock_ws.send.assert_called()

    def test_binance_subscription_format(self, stream_manager):
        """Test Binance-specific subscription format"""
        stream_manager.exchange = "binance"
        mock_ws = Mock()
        stream_manager.ws = mock_ws
        stream_manager.is_connected = True
        
        stream_manager._send_subscription("ticker:BTC/USDT,ETH/USDT")
        
        # Should format for Binance
        call_args = mock_ws.send.call_args[0][0]
        sub_message = json.loads(call_args)
        
        assert sub_message["method"] == "SUBSCRIBE"
        assert "params" in sub_message
        assert "id" in sub_message

    def test_okx_subscription_format(self, stream_manager):
        """Test OKX-specific subscription format"""
        stream_manager.exchange = "okx"
        mock_ws = Mock()
        stream_manager.ws = mock_ws
        stream_manager.is_connected = True
        
        stream_manager._send_subscription("ticker:BTC-USDT")
        
        # Should format for OKX
        call_args = mock_ws.send.call_args[0][0]
        sub_message = json.loads(call_args)
        
        assert sub_message["op"] == "subscribe"
        assert "args" in sub_message

    def test_reconnection_logic(self, stream_manager):
        """Test automatic reconnection on disconnect"""
        stream_manager.max_reconnect_attempts = 2
        
        with patch.object(stream_manager, 'connect') as mock_connect:
            # Simulate connection close
            stream_manager._on_close(None, 1000, "Normal closure")
            
            assert stream_manager.is_connected is False
            assert stream_manager.reconnect_attempts == 1
            
            # Should attempt reconnection
            time.sleep(0.1)  # Allow time for reconnection logic
            mock_connect.assert_called()

    def test_disconnect(self, stream_manager):
        """Test manual disconnection"""
        mock_ws = Mock()
        stream_manager.ws = mock_ws
        stream_manager.is_connected = True
        
        stream_manager.disconnect()
        
        mock_ws.close.assert_called_once()
        assert stream_manager.is_connected is False


class TestCryptoStreamService:
    """Test suite for CryptoStreamService class"""

    @pytest.fixture
    def stream_service(self):
        """Create CryptoStreamService instance for testing"""
        return CryptoStreamService(
            exchanges=["binance", "okx"],
            buffer_size=1000,
            enable_heartbeat=False,  # Disable for testing
            heartbeat_interval=1.0
        )

    def test_initialization(self, stream_service):
        """Test CryptoStreamService initialization"""
        assert stream_service.exchanges == ["binance", "okx"]
        assert stream_service.buffer_size == 1000
        assert not stream_service.is_running
        assert len(stream_service.stream_managers) == 2  # binance and okx

    def test_stream_manager_creation(self, stream_service):
        """Test that stream managers are created for each exchange"""
        assert "binance" in stream_service.stream_managers
        assert "okx" in stream_service.stream_managers
        
        binance_manager = stream_service.stream_managers["binance"]
        assert binance_manager.exchange == "binance"
        assert binance_manager.config["ws_url"] is not None

    @patch.object(StreamManager, 'connect')
    def test_service_start(self, mock_connect, stream_service):
        """Test starting the stream service"""
        stream_service.start()
        
        assert stream_service.is_running is True
        assert stream_service.global_stats["start_time"] is not None
        
        # Should attempt to connect to all exchanges
        assert mock_connect.call_count == len(stream_service.exchanges)

    def test_service_stop(self, stream_service):
        """Test stopping the stream service"""
        # Start first
        stream_service.is_running = True
        
        with patch.object(StreamManager, 'disconnect') as mock_disconnect:
            stream_service.stop()
            
            assert stream_service.is_running is False
            # Should disconnect all managers
            assert mock_disconnect.call_count == len(stream_service.stream_managers)

    def test_ticker_subscription(self, stream_service):
        """Test ticker data subscription"""
        symbols = ["BTC/USDT", "ETH/USDT"]
        exchanges = ["binance"]
        
        with patch.object(StreamManager, 'subscribe') as mock_subscribe:
            stream_service.subscribe_ticker(symbols, exchanges)
            
            # Should subscribe with correct parameters
            mock_subscribe.assert_called_with("ticker", symbols)

    def test_klines_subscription(self, stream_service):
        """Test klines data subscription"""
        symbols = ["BTC/USDT"]
        intervals = ["1m", "5m"]
        exchanges = ["binance"]
        
        with patch.object(StreamManager, 'subscribe') as mock_subscribe:
            stream_service.subscribe_klines(symbols, intervals, exchanges)
            
            # Should subscribe to each interval
            assert mock_subscribe.call_count == len(intervals)

    def test_trades_subscription(self, stream_service):
        """Test trades data subscription"""
        symbols = ["BTC/USDT"]
        exchanges = ["okx"]
        
        with patch.object(StreamManager, 'subscribe') as mock_subscribe:
            stream_service.subscribe_trades(symbols, exchanges)
            
            mock_subscribe.assert_called_with("trades", symbols)

    def test_orderbook_subscription(self, stream_service):
        """Test order book subscription"""
        symbols = ["BTC/USDT"]
        depth = 20
        exchanges = ["binance"]
        
        with patch.object(StreamManager, 'subscribe') as mock_subscribe:
            stream_service.subscribe_orderbook(symbols, depth, exchanges)
            
            mock_subscribe.assert_called_with("depth20", symbols)

    def test_data_handler_registration(self, stream_service):
        """Test data handler registration"""
        def test_handler(data):
            pass
        
        stream_service.add_data_handler("ticker", test_handler)
        
        assert len(stream_service.data_handlers["ticker"]) == 1
        assert test_handler in stream_service.data_handlers["ticker"]

    def test_message_type_determination_binance(self, stream_service):
        """Test message type determination for Binance"""
        # Binance ticker message
        binance_data = {"e": "24hrTicker", "s": "BTCUSD", "c": "45000"}
        message_type = stream_service._determine_message_type("binance", binance_data)
        assert message_type == "ticker"
        
        # Binance kline message
        binance_kline = {"e": "kline", "k": {"s": "BTCUSD"}}
        message_type = stream_service._determine_message_type("binance", binance_kline)
        assert message_type == "kline"
        
        # Binance trade message
        binance_trade = {"e": "trade", "s": "BTCUSD"}
        message_type = stream_service._determine_message_type("binance", binance_trade)
        assert message_type == "trades"

    def test_message_type_determination_okx(self, stream_service):
        """Test message type determination for OKX"""
        # OKX ticker message
        okx_data = {"arg": {"channel": "tickers", "instId": "BTC-USDT"}}
        message_type = stream_service._determine_message_type("okx", okx_data)
        assert message_type == "ticker"
        
        # OKX candle message
        okx_candle = {"arg": {"channel": "candle1m", "instId": "BTC-USDT"}}
        message_type = stream_service._determine_message_type("okx", okx_candle)
        assert message_type == "kline"

    def test_binance_ticker_parsing(self, stream_service):
        """Test Binance ticker message parsing"""
        binance_ticker = {
            "e": "24hrTicker",
            "s": "BTCUSD",
            "c": "45250.75",
            "v": "1250.5",
            "h": "45350.0",
            "l": "44950.0",
            "P": "1.5"
        }
        
        parsed = stream_service._parse_ticker("binance", binance_ticker)
        
        assert parsed["exchange"] == "binance"
        assert parsed["symbol"] == "BTCUSD"
        assert parsed["price"] == 45250.75
        assert parsed["volume"] == 1250.5
        assert parsed["high"] == 45350.0
        assert parsed["low"] == 44950.0
        assert parsed["change"] == 1.5

    def test_okx_ticker_parsing(self, stream_service):
        """Test OKX ticker message parsing"""
        okx_ticker = {
            "arg": {"channel": "tickers", "instId": "BTC-USDT"},
            "data": [{
                "instId": "BTC-USDT",
                "last": "45250.75",
                "vol24h": "1250.5",
                "high24h": "45350.0",
                "low24h": "44950.0"
            }]
        }
        
        parsed = stream_service._parse_ticker("okx", okx_ticker)
        
        assert parsed["exchange"] == "okx"
        assert parsed["symbol"] == "BTC-USDT"
        assert parsed["price"] == 45250.75
        assert parsed["volume"] == 1250.5

    def test_binance_kline_parsing(self, stream_service):
        """Test Binance kline message parsing"""
        binance_kline = {
            "e": "kline",
            "k": {
                "s": "BTCUSD",
                "t": 1704067200000,
                "o": "45000.0",
                "h": "45100.0",
                "l": "44900.0",
                "c": "45050.0",
                "v": "1250.5",
                "x": True
            }
        }
        
        parsed = stream_service._parse_kline("binance", binance_kline)
        
        assert parsed["exchange"] == "binance"
        assert parsed["symbol"] == "BTCUSD"
        assert parsed["open"] == 45000.0
        assert parsed["high"] == 45100.0
        assert parsed["low"] == 44900.0
        assert parsed["close"] == 45050.0
        assert parsed["volume"] == 1250.5
        assert parsed["is_closed"] is True

    def test_trade_data_parsing(self, stream_service):
        """Test trade message parsing"""
        binance_trade = {
            "e": "trade",
            "s": "BTCUSD",
            "t": 12345,
            "p": "45250.75",
            "q": "0.125",
            "T": 1704067200000,
            "m": False
        }
        
        parsed = stream_service._parse_trade("binance", binance_trade)
        
        assert parsed["exchange"] == "binance"
        assert parsed["symbol"] == "BTCUSD"
        assert parsed["trade_id"] == 12345
        assert parsed["price"] == 45250.75
        assert parsed["quantity"] == 0.125
        assert parsed["is_buyer_maker"] is False

    def test_depth_data_parsing(self, stream_service):
        """Test order book depth parsing"""
        binance_depth = {
            "e": "depthUpdate",
            "s": "BTCUSD",
            "b": [["45249.50", "1.25"], ["45249.00", "2.50"]],
            "a": [["45250.50", "1.10"], ["45251.00", "3.20"]]
        }
        
        parsed = stream_service._parse_depth("binance", binance_depth)
        
        assert parsed["exchange"] == "binance"
        assert parsed["symbol"] == "BTCUSD"
        assert len(parsed["bids"]) == 2
        assert len(parsed["asks"]) == 2
        assert parsed["bids"][0] == [45249.50, 1.25]
        assert parsed["asks"][0] == [45250.50, 1.10]

    def test_data_buffering(self, stream_service):
        """Test data buffering functionality"""
        test_data = {
            "exchange": "binance",
            "symbol": "BTCUSD",
            "price": 45250.75,
            "timestamp": pd.Timestamp.now()
        }
        
        # Buffer some data
        stream_service._buffer_data("ticker", test_data)
        
        # Retrieve buffered data
        buffered = stream_service.get_buffered_data("ticker")
        
        assert len(buffered) == 1
        assert buffered.iloc[0]["exchange"] == "binance"
        assert buffered.iloc[0]["symbol"] == "BTCUSD"
        assert buffered.iloc[0]["price"] == 45250.75

    def test_buffer_size_limit(self, stream_service):
        """Test buffer size limiting"""
        stream_service.buffer_size = 3  # Small buffer for testing
        
        # Add more data than buffer size
        for i in range(5):
            test_data = {
                "exchange": "binance",
                "symbol": "BTCUSD",
                "price": 45000 + i,
                "timestamp": pd.Timestamp.now()
            }
            stream_service._buffer_data("ticker", test_data)
        
        # Should only keep latest 3 records
        buffered = stream_service.get_buffered_data("ticker")
        assert len(buffered) == 3
        
        # Should have latest prices (45002, 45003, 45004)
        prices = buffered["price"].tolist()
        assert 45002.0 in prices
        assert 45003.0 in prices
        assert 45004.0 in prices

    def test_buffer_clearing(self, stream_service):
        """Test buffer clearing functionality"""
        # Add some data
        test_data = {"exchange": "binance", "symbol": "BTCUSD", "price": 45250.75}
        stream_service._buffer_data("ticker", test_data)
        stream_service._buffer_data("trades", {"price": 45250.75})
        
        # Clear specific buffer
        stream_service.clear_buffer("ticker")
        ticker_buffer = stream_service.get_buffered_data("ticker")
        trades_buffer = stream_service.get_buffered_data("trades")
        
        assert len(ticker_buffer) == 0
        assert len(trades_buffer) == 1  # Should still have trades data
        
        # Clear all buffers
        stream_service.clear_buffer()
        all_buffers_empty = all(
            len(stream_service.get_buffered_data(dt)) == 0 
            for dt in stream_service.data_buffers.keys()
        )
        assert all_buffers_empty

    def test_stream_statistics(self, stream_service):
        """Test comprehensive stream statistics"""
        # Simulate some activity
        stream_service.global_stats["total_messages"] = 1000
        stream_service.global_stats["start_time"] = datetime.now()
        
        # Add some manager stats
        for exchange, manager in stream_service.stream_managers.items():
            manager.is_connected = True
            manager.stats["messages_received"] = 100
            manager.subscriptions.add("ticker:BTC/USDT")
        
        # Add some buffer data
        stream_service._buffer_data("ticker", {"price": 45000})
        stream_service._buffer_data("trades", {"price": 45001})
        
        stats = stream_service.get_stream_stats()
        
        # Verify global stats
        assert stats["total_messages"] == 1000
        assert "start_time" in stats
        
        # Verify exchange stats
        assert "exchange_stats" in stats
        for exchange in stream_service.exchanges:
            assert exchange in stats["exchange_stats"]
            exchange_stats = stats["exchange_stats"][exchange]
            assert "connected" in exchange_stats
            assert "subscriptions" in exchange_stats
            assert "messages_received" in exchange_stats
        
        # Verify buffer stats
        assert "buffer_stats" in stats
        assert stats["buffer_stats"]["ticker"] == 1
        assert stats["buffer_stats"]["trades"] == 1

    def test_message_handler_calling(self, stream_service):
        """Test that message handlers are called correctly"""
        handler_calls = []
        
        def test_handler(data):
            handler_calls.append(data)
        
        # Register handler
        stream_service.add_data_handler("ticker", test_handler)
        
        # Simulate message processing
        test_message = {
            "e": "24hrTicker",
            "s": "BTCUSD",
            "c": "45250.75"
        }
        
        stream_service._handle_message("binance", json.dumps(test_message))
        
        # Handler should have been called
        assert len(handler_calls) == 1
        parsed_data = handler_calls[0]
        assert parsed_data["symbol"] == "BTCUSD"
        assert parsed_data["price"] == 45250.75

    def test_invalid_json_handling(self, stream_service):
        """Test handling of invalid JSON messages"""
        # This should not crash the service
        stream_service._handle_message("binance", "invalid json {")
        
        # Service should continue functioning
        assert stream_service.is_running is not None  # Service state unchanged

    def test_unknown_message_type_handling(self, stream_service):
        """Test handling of unknown message types"""
        unknown_message = {
            "unknown_field": "unknown_value"
        }
        
        # Should handle gracefully without crashing
        stream_service._handle_message("binance", json.dumps(unknown_message))
        
        # No data should be buffered for unknown types
        assert len(stream_service.data_buffers) == 0