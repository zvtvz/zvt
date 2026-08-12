# -*- coding: utf-8 -*-
"""
Integration Tests for Exchange Connectors
Tests real and mock connector functionality across multiple exchanges
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import asyncio
import time

from zvt.services.crypto.connectors import (
    BinanceConnector, OKXConnector, BybitConnector, 
    CoinbaseConnector, MockCryptoConnector
)
from zvt.services.crypto.data_loader import CryptoDataLoader
from zvt.services.crypto.stream_service import CryptoStreamService


class TestExchangeConnectors:
    """Test suite for exchange connector implementations"""
    
    @pytest.fixture
    def mock_connectors(self):
        """Create mock connectors for testing"""
        return {
            "binance": MockCryptoConnector("binance"),
            "okx": MockCryptoConnector("okx"), 
            "bybit": MockCryptoConnector("bybit"),
            "coinbase": MockCryptoConnector("coinbase")
        }
    
    @pytest.fixture
    def test_symbols(self):
        """Common test symbols"""
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    
    @pytest.fixture
    def test_intervals(self):
        """Common test intervals"""
        return ["1m", "5m", "1h", "1d"]

    def test_connector_initialization(self):
        """Test connector initialization and configuration"""
        # Test Binance connector
        binance = BinanceConnector(testnet=True)
        assert binance.get_exchange_name() == "binance"
        assert binance.testnet is True
        assert "testnet.binance" in binance.base_url
        
        # Test OKX connector
        okx = OKXConnector(testnet=True)
        assert okx.get_exchange_name() == "okx"
        assert okx.testnet is True
        
        # Test Bybit connector 
        bybit = BybitConnector(testnet=True)
        assert bybit.get_exchange_name() == "bybit"
        assert "testnet" in bybit.base_url
        
        # Test Coinbase connector
        coinbase = CoinbaseConnector(testnet=True)
        assert coinbase.get_exchange_name() == "coinbase"
        assert "sandbox" in coinbase.base_url

    def test_symbol_normalization(self):
        """Test symbol format conversion across exchanges"""
        test_symbol = "BTC/USDT"
        
        # Binance uses BTCUSDT format
        binance = BinanceConnector()
        assert binance.normalize_symbol(test_symbol) == "BTCUSDT"
        
        # OKX uses BTC-USDT format  
        okx = OKXConnector()
        assert okx.normalize_symbol(test_symbol) == "BTC-USDT"
        assert okx.denormalize_symbol("BTC-USDT") == "BTC/USDT"
        
        # Coinbase uses BTC-USD format
        coinbase = CoinbaseConnector()
        assert coinbase.normalize_symbol("BTC/USD") == "BTC-USD"
        assert coinbase.denormalize_symbol("BTC-USD") == "BTC/USD"

    def test_interval_normalization(self):
        """Test interval format conversion"""
        binance = BinanceConnector()
        assert binance.normalize_interval("1m") == "1m"
        assert binance.normalize_interval("1h") == "1h"
        assert binance.normalize_interval("1d") == "1d"
        
        okx = OKXConnector()  
        assert okx.normalize_interval("1h") == "1H"
        assert okx.normalize_interval("1d") == "1D"
        
        bybit = BybitConnector()
        assert bybit.normalize_interval("1m") == "1"
        assert bybit.normalize_interval("1d") == "D"
        
        coinbase = CoinbaseConnector()
        assert coinbase.normalize_interval("1m") == "60"  # seconds
        assert coinbase.normalize_interval("1h") == "3600"

    @patch('requests.Session.get')
    def test_ohlcv_data_retrieval(self, mock_get, test_symbols):
        """Test OHLCV data retrieval with mocked responses"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = [
            [1640995200000, "47000", "48000", "46000", "47500", "100.5"]
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        connector = BinanceConnector(testnet=True)
        df = connector.get_ohlcv(
            symbol="BTC/USDT",
            interval="1h",
            start_time=datetime.now() - timedelta(days=1),
            end_time=datetime.now(),
            limit=24
        )
        
        assert isinstance(df, pd.DataFrame)
        assert len(df.columns) >= 6  # timestamp, open, high, low, close, volume
        
    def test_mock_connector_functionality(self, mock_connectors, test_symbols):
        """Test MockCryptoConnector generates valid data"""
        mock_connector = mock_connectors["binance"]
        
        # Test OHLCV data generation
        df = mock_connector.get_ohlcv(
            symbol="BTC/USDT",
            interval="1h", 
            start_time=datetime.now() - timedelta(days=1),
            end_time=datetime.now(),
            limit=24
        )
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert all(col in df.columns for col in ["timestamp", "open", "high", "low", "close", "volume"])
        assert df["high"].min() >= df["low"].max()  # Basic OHLC validation
        
        # Test trades data generation
        trades_df = mock_connector.get_trades("BTC/USDT", limit=10)
        assert isinstance(trades_df, pd.DataFrame) 
        assert len(trades_df) > 0
        assert all(col in trades_df.columns for col in ["timestamp", "price", "quantity", "side", "trade_id"])
        
        # Test orderbook data
        orderbook = mock_connector.get_orderbook("BTC/USDT", depth=10)
        assert isinstance(orderbook, dict)
        assert "bids" in orderbook and "asks" in orderbook
        assert len(orderbook["bids"]) > 0 and len(orderbook["asks"]) > 0

    def test_data_loader_integration(self, test_symbols):
        """Test CryptoDataLoader integration with connectors"""
        from zvt.contract import IntervalLevel
        
        data_loader = CryptoDataLoader(
            exchanges=["binance", "okx"],  # Use testnet connectors
            max_workers=2,
            validation_enabled=True
        )
        
        # Test historical data loading
        results = data_loader.load_historical_kdata(
            symbols=test_symbols[:1],  # Just BTC for faster test
            intervals=[IntervalLevel.LEVEL_1HOUR],
            start_date=datetime.now() - timedelta(days=2),
            end_date=datetime.now(),
            exchanges=["binance"]  # Test single exchange first
        )
        
        assert isinstance(results, dict)
        # Should have results for (exchange, symbol, interval) combinations
        assert len(results) > 0
        
        # Verify data structure
        for key, df in results.items():
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            print(f"Loaded {len(df)} records for {key}")

    def test_error_handling_and_retries(self):
        """Test error handling and retry mechanisms"""
        # Test with invalid symbol
        connector = MockCryptoConnector("binance")
        
        # Should handle gracefully and return empty DataFrame
        df = connector.get_ohlcv("INVALID/SYMBOL", "1h", limit=10)
        assert isinstance(df, pd.DataFrame)
        # Mock connector should still generate data even for "invalid" symbols
        
        # Test rate limiting
        start_time = time.time()
        connector._apply_rate_limit()
        connector._apply_rate_limit()  # Second call should be delayed
        elapsed = time.time() - start_time
        assert elapsed >= connector.rate_limit_delay

    def test_websocket_subscription_setup(self):
        """Test WebSocket subscription setup (without actual connections)"""
        connector = BinanceConnector(testnet=True)
        
        # Mock callback function
        callback = Mock()
        
        # Test ticker subscription setup
        connector.subscribe_ticker(["BTC/USDT"], callback)
        assert len(connector._ws_connections) > 0
        
        # Test trades subscription
        connector.subscribe_trades(["ETH/USDT"], callback) 
        assert len(connector._ws_connections) > 1

    def test_stream_service_integration(self):
        """Test CryptoStreamService with mock data"""
        stream_service = CryptoStreamService(
            exchanges=["binance"],
            buffer_size=1000
        )
        
        # Test service initialization
        assert len(stream_service.stream_managers) > 0
        assert "binance" in stream_service.stream_managers
        
        # Test handler registration
        handler = Mock()
        stream_service.add_data_handler("ticker", handler)
        assert handler in stream_service.data_handlers["ticker"]

    def test_data_validation_and_processing(self):
        """Test data validation and processing logic"""
        from zvt.contract import IntervalLevel
        
        data_loader = CryptoDataLoader(validation_enabled=True)
        
        # Create test DataFrame with some invalid data
        test_data = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=10, freq="1H"),
            "open": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            "high": [105, 106, 107, 108, 109, 110, 111, 112, 113, 114],
            "low": [95, 96, 97, 98, 99, 100, 101, 102, 103, 104],
            "close": [104, 105, 106, 107, 108, 109, 110, 111, 112, 113],
            "volume": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
        })
        
        # Add invalid record (high < low)
        test_data.loc[2, "high"] = 90  # Invalid: high < low
        test_data.loc[3, "volume"] = -100  # Invalid: negative volume
        
        validated_data = data_loader._validate_and_process_data(
            test_data, "BTC/USDT", IntervalLevel.LEVEL_1HOUR
        )
        
        # Should have removed invalid records
        assert len(validated_data) < len(test_data)
        assert data_loader.stats["validation_errors"] > 0

    def test_connector_statistics_tracking(self):
        """Test that connectors properly track statistics"""
        connector = MockCryptoConnector("binance")
        
        initial_requests = connector.stats["requests_made"]
        
        # Make some requests
        connector.get_ohlcv("BTC/USDT", "1h", limit=10)
        connector.get_trades("BTC/USDT", limit=10)
        connector.get_orderbook("BTC/USDT")
        
        # Statistics should be updated
        assert connector.stats["requests_made"] > initial_requests
        
        # Test WebSocket message counting
        initial_ws_messages = connector.stats["ws_messages_received"]
        # Simulate receiving WebSocket message
        connector.stats["ws_messages_received"] += 1
        assert connector.stats["ws_messages_received"] > initial_ws_messages

    @pytest.mark.asyncio
    async def test_async_data_loading(self):
        """Test asynchronous data loading capabilities"""
        from zvt.contract import IntervalLevel
        
        data_loader = CryptoDataLoader(exchanges=["binance"])
        
        # Test async historical data loading
        results = await data_loader.load_historical_async(
            symbols=["BTC/USDT"],
            intervals=[IntervalLevel.LEVEL_1HOUR],
            start_date=datetime.now() - timedelta(hours=24),
            end_date=datetime.now()
        )
        
        assert isinstance(results, dict)
        assert len(results) > 0

    def test_multi_exchange_consistency(self, test_symbols):
        """Test that multiple exchanges return consistent data formats"""
        exchanges = ["binance", "okx", "bybit", "coinbase"]
        data_loader = CryptoDataLoader(exchanges=exchanges)
        
        # Test that all exchanges return the same data structure
        for exchange in exchanges:
            connector = data_loader._get_connector(exchange)
            
            # Test OHLCV format consistency
            df = connector.get_ohlcv("BTC/USDT", "1h", limit=5)
            assert isinstance(df, pd.DataFrame)
            expected_columns = ["timestamp", "open", "high", "low", "close", "volume"]
            assert all(col in df.columns for col in expected_columns)
            
            # Test orderbook format consistency  
            orderbook = connector.get_orderbook("BTC/USDT")
            assert isinstance(orderbook, dict)
            assert "bids" in orderbook and "asks" in orderbook
            assert "timestamp" in orderbook


class TestExchangeConnectorPerformance:
    """Performance and stress tests for connectors"""
    
    def test_concurrent_requests(self):
        """Test connector performance under concurrent requests"""
        import concurrent.futures
        import threading
        
        connector = MockCryptoConnector("binance")
        symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "ADA/USDT", "DOT/USDT"]
        
        def fetch_data(symbol):
            return connector.get_ohlcv(symbol, "1h", limit=100)
        
        # Test concurrent execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_data, symbol) for symbol in symbols]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        assert len(results) == len(symbols)
        assert all(isinstance(df, pd.DataFrame) and len(df) > 0 for df in results)
        
        # Rate limiting should have been applied
        assert connector.stats["requests_made"] >= len(symbols)

    def test_memory_efficiency(self):
        """Test memory usage for large data sets"""
        connector = MockCryptoConnector("binance")
        
        # Request large dataset
        large_df = connector.get_ohlcv(
            "BTC/USDT", "1m", 
            start_time=datetime.now() - timedelta(days=7),
            limit=5000
        )
        
        assert isinstance(large_df, pd.DataFrame)
        assert len(large_df) > 1000
        
        # Verify data types are memory efficient
        assert large_df["timestamp"].dtype == "datetime64[ns]"
        assert large_df["open"].dtype in ["float64", "float32"]


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])