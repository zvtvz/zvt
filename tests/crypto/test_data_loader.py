# -*- coding: utf-8 -*-
"""
Tests for Crypto Data Loader Service
Comprehensive testing of historical data loading functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import time

from zvt.contract import IntervalLevel
from zvt.services.crypto.data_loader import CryptoDataLoader


class TestCryptoDataLoader:
    """Test suite for CryptoDataLoader service"""

    @pytest.fixture
    def data_loader(self):
        """Create CryptoDataLoader instance for testing"""
        return CryptoDataLoader(
            exchanges=["binance", "okx", "bybit"],
            max_workers=2,
            rate_limit_delay=0.01,  # Fast for testing
            max_retries=2,
            chunk_size=100,
            validation_enabled=True
        )

    def test_initialization(self, data_loader):
        """Test CryptoDataLoader initialization"""
        assert data_loader.exchanges == ["binance", "okx", "bybit"]
        assert data_loader.max_workers == 2
        assert data_loader.rate_limit_delay == 0.01
        assert data_loader.max_retries == 2
        assert data_loader.validation_enabled is True
        assert data_loader.stats["total_requests"] == 0

    def test_load_historical_kdata_single_symbol(self, data_loader):
        """Test loading historical data for single symbol"""
        symbols = ["BTC/USDT"]
        intervals = [IntervalLevel.LEVEL_1HOUR]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        exchanges = ["binance"]

        results = data_loader.load_historical_kdata(
            symbols=symbols,
            intervals=intervals,
            start_date=start_date,
            end_date=end_date,
            exchanges=exchanges
        )

        # Should return data for each exchange-symbol-interval combination
        assert len(results) == 1
        key = ("binance", "BTC/USDT", "1h")
        assert key in results
        
        df = results[key]
        assert not df.empty
        assert "timestamp" in df.columns
        assert "open" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns

    def test_load_historical_kdata_multiple_symbols(self, data_loader):
        """Test loading data for multiple symbols and intervals"""
        symbols = ["BTC/USDT", "ETH/USDT"]
        intervals = [IntervalLevel.LEVEL_1HOUR, IntervalLevel.LEVEL_1DAY]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        exchanges = ["binance", "okx"]

        results = data_loader.load_historical_kdata(
            symbols=symbols,
            intervals=intervals,
            start_date=start_date,
            end_date=end_date,
            exchanges=exchanges
        )

        # Should have 2 exchanges × 2 symbols × 2 intervals = 8 results
        expected_combinations = 2 * 2 * 2
        assert len(results) <= expected_combinations  # Some might be empty

        # Check that keys follow expected format
        for key in results.keys():
            exchange, symbol, interval = key
            assert exchange in exchanges
            assert symbol in symbols
            assert interval in ["1h", "1d"]

    def test_mock_ohlcv_generation(self, data_loader):
        """Test mock OHLCV data generation"""
        connector = Mock()
        symbol = "BTC/USDT"
        interval = IntervalLevel.LEVEL_1HOUR
        start_date = pd.Timestamp("2024-01-01")
        end_date = pd.Timestamp("2024-01-01 12:00:00")

        df = data_loader._mock_load_ohlcv(
            connector, symbol, interval, start_date, end_date
        )

        assert not df.empty
        assert len(df) == 12  # 12 hours of data
        
        # Validate OHLCV columns
        required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
        for col in required_columns:
            assert col in df.columns

        # Validate OHLCV relationships
        assert all(df["high"] >= df["open"])
        assert all(df["high"] >= df["close"])
        assert all(df["low"] <= df["open"])
        assert all(df["low"] <= df["close"])
        assert all(df["volume"] > 0)

    def test_data_validation_and_processing(self, data_loader):
        """Test data validation and gap detection"""
        # Create test data with some invalid records
        data = {
            "timestamp": pd.date_range("2024-01-01", periods=5, freq="1H"),
            "open": [100, 101, 0, 103, 104],  # One invalid (zero)
            "high": [102, 103, 102, 105, 106],
            "low": [99, 100, 98, 102, 103],
            "close": [101, 102, 101, 104, 105],
            "volume": [1000, 1100, 1200, 1300, -100]  # One invalid (negative)
        }
        df = pd.DataFrame(data)

        # Test validation
        validated_df = data_loader._validate_and_process_data(
            df, "BTC/USDT", IntervalLevel.LEVEL_1HOUR
        )

        # Should remove invalid records
        assert len(validated_df) == 3  # 2 invalid records removed
        assert all(validated_df["open"] > 0)
        assert all(validated_df["volume"] >= 0)
        assert data_loader.stats["validation_errors"] == 2

    def test_data_gap_detection(self, data_loader):
        """Test gap detection in time series data"""
        # Create data with a gap
        timestamps = [
            datetime(2024, 1, 1, 10, 0),
            datetime(2024, 1, 1, 11, 0),
            datetime(2024, 1, 1, 12, 0),
            # Gap: 13:00 missing
            datetime(2024, 1, 1, 14, 0),  # 2-hour gap
            datetime(2024, 1, 1, 15, 0),
        ]
        
        data = {
            "timestamp": timestamps,
            "open": [100, 101, 102, 104, 105],
            "high": [102, 103, 104, 106, 107],
            "low": [99, 100, 101, 103, 104],
            "close": [101, 102, 103, 105, 106],
            "volume": [1000, 1100, 1200, 1300, 1400]
        }
        df = pd.DataFrame(data)

        validated_df = data_loader._validate_and_process_data(
            df, "BTC/USDT", IntervalLevel.LEVEL_1HOUR
        )

        # Should detect gap
        assert data_loader.stats["gaps_detected"] > 0

    def test_rate_limiting(self, data_loader):
        """Test rate limiting functionality"""
        exchange = "binance"
        
        # First call should not delay
        start_time = time.time()
        data_loader._apply_rate_limit(exchange)
        first_duration = time.time() - start_time
        
        # Second call immediately after should delay
        start_time = time.time()
        data_loader._apply_rate_limit(exchange)
        second_duration = time.time() - start_time
        
        # Second call should take at least the rate limit delay
        assert second_duration >= data_loader.rate_limit_delay

    def test_connector_caching(self, data_loader):
        """Test exchange connector caching"""
        exchange = "binance"
        
        # Get connector twice
        connector1 = data_loader._get_connector(exchange)
        connector2 = data_loader._get_connector(exchange)
        
        # Should be the same object (cached)
        assert connector1 is connector2
        assert exchange in data_loader._connectors

    def test_load_tick_data(self, data_loader):
        """Test tick data loading functionality"""
        symbols = ["BTC/USDT"]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 1, 1, 0, 0)  # 1 hour
        exchanges = ["binance"]
        data_types = ["trades", "orderbook"]

        results = data_loader.load_tick_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            exchanges=exchanges,
            data_types=data_types
        )

        # Should have results for each exchange-symbol-data_type combination
        expected_keys = [
            ("binance", "BTC/USDT", "trades"),
            ("binance", "BTC/USDT", "orderbook")
        ]
        
        for key in expected_keys:
            if key in results:
                df = results[key]
                assert not df.empty

    def test_mock_trade_data_generation(self, data_loader):
        """Test mock trade data generation"""
        symbol = "BTC/USDT"
        start = pd.Timestamp("2024-01-01 12:00:00")
        end = pd.Timestamp("2024-01-01 12:05:00")  # 5 minutes

        trade_df = data_loader._mock_trade_data(symbol, start, end)

        assert not trade_df.empty
        assert "timestamp" in trade_df.columns
        assert "price" in trade_df.columns
        assert "size" in trade_df.columns
        assert "side" in trade_df.columns
        assert "trade_id" in trade_df.columns
        
        # Validate trade data
        assert all(trade_df["price"] > 0)
        assert all(trade_df["size"] > 0)
        assert all(trade_df["side"].isin(["buy", "sell"]))

    def test_mock_orderbook_data_generation(self, data_loader):
        """Test mock order book data generation"""
        symbol = "BTC/USDT"
        start = pd.Timestamp("2024-01-01 12:00:00")
        end = pd.Timestamp("2024-01-01 12:05:00")

        ob_df = data_loader._mock_orderbook_data(symbol, start, end)

        assert not ob_df.empty
        assert "timestamp" in ob_df.columns
        assert "bids" in ob_df.columns
        assert "asks" in ob_df.columns
        assert "mid_price" in ob_df.columns

        # Validate order book structure
        for _, row in ob_df.iterrows():
            bids = row["bids"]
            asks = row["asks"]
            
            assert len(bids) == 5  # 5 levels
            assert len(asks) == 5  # 5 levels
            
            # Check bid/ask structure
            for bid in bids:
                assert bid["price"] > 0
                assert bid["size"] > 0
            
            for ask in asks:
                assert ask["price"] > 0
                assert ask["size"] > 0

    def test_mock_funding_data_generation(self, data_loader):
        """Test mock funding rate data generation"""
        symbol = "BTC-PERP"
        start = pd.Timestamp("2024-01-01")
        end = pd.Timestamp("2024-01-02")

        funding_df = data_loader._mock_funding_data(symbol, start, end)

        assert not fund_df.empty
        assert "timestamp" in funding_df.columns
        assert "funding_rate" in funding_df.columns
        assert "next_funding_time" in funding_df.columns

        # Validate funding data
        assert all(abs(funding_df["funding_rate"]) < 0.01)  # Reasonable funding rates

    def test_progress_callback(self, data_loader):
        """Test progress callback functionality"""
        progress_updates = []
        
        def progress_callback(completed, total):
            progress_updates.append((completed, total))
        
        data_loader.set_progress_callback(progress_callback)
        
        # Load small dataset to trigger progress updates
        symbols = ["BTC/USDT"]
        intervals = [IntervalLevel.LEVEL_1HOUR]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 1, 1, 0, 0)
        exchanges = ["binance"]

        data_loader.load_historical_kdata(
            symbols=symbols,
            intervals=intervals,
            start_date=start_date,
            end_date=end_date,
            exchanges=exchanges
        )

        # Should have received progress updates
        assert len(progress_updates) > 0
        
        # Final update should show completion
        final_completed, final_total = progress_updates[-1]
        assert final_completed == final_total

    def test_statistics_tracking(self, data_loader):
        """Test statistics tracking"""
        initial_stats = data_loader.get_loading_stats()
        assert initial_stats["total_requests"] == 0
        assert initial_stats["successful_requests"] == 0

        # Load some data
        symbols = ["BTC/USDT"]
        intervals = [IntervalLevel.LEVEL_1HOUR]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 1, 1, 0, 0)
        exchanges = ["binance"]

        data_loader.load_historical_kdata(
            symbols=symbols,
            intervals=intervals,
            start_date=start_date,
            end_date=end_date,
            exchanges=exchanges
        )

        # Check updated statistics
        final_stats = data_loader.get_loading_stats()
        assert final_stats["total_requests"] > 0
        assert final_stats["successful_requests"] > 0
        assert final_stats["data_points_loaded"] > 0

    def test_reset_statistics(self, data_loader):
        """Test statistics reset functionality"""
        # Generate some statistics
        data_loader.stats["total_requests"] = 100
        data_loader.stats["successful_requests"] = 95
        
        # Reset statistics
        data_loader.reset_stats()
        
        # Should be back to zero
        stats = data_loader.get_loading_stats()
        assert stats["total_requests"] == 0
        assert stats["successful_requests"] == 0

    def test_parallel_loading_performance(self, data_loader):
        """Test parallel loading performance"""
        symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
        intervals = [IntervalLevel.LEVEL_1HOUR, IntervalLevel.LEVEL_1DAY]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        exchanges = ["binance", "okx"]

        start_time = time.time()
        
        results = data_loader.load_historical_kdata(
            symbols=symbols,
            intervals=intervals,
            start_date=start_date,
            end_date=end_date,
            exchanges=exchanges
        )
        
        duration = time.time() - start_time
        
        # With parallel loading, should complete reasonably quickly
        # 3 symbols × 2 intervals × 2 exchanges = 12 tasks
        assert duration < 10.0  # Should complete within 10 seconds
        
        # Should have multiple results
        assert len(results) > 0

    @patch('zvt.services.crypto.data_loader.pd.np.random.random')
    def test_deterministic_mock_data(self, mock_random, data_loader):
        """Test that mock data generation is consistent"""
        # Make random predictable
        mock_random.return_value = 0.5
        
        connector = Mock()
        symbol = "BTC/USDT"
        interval = IntervalLevel.LEVEL_1HOUR
        start_date = pd.Timestamp("2024-01-01")
        end_date = pd.Timestamp("2024-01-01 02:00:00")

        df1 = data_loader._mock_load_ohlcv(
            connector, symbol, interval, start_date, end_date
        )
        
        df2 = data_loader._mock_load_ohlcv(
            connector, symbol, interval, start_date, end_date
        )

        # With deterministic random, should get identical results
        pd.testing.assert_frame_equal(df1, df2)

    def test_error_handling_during_loading(self, data_loader):
        """Test error handling during data loading"""
        # Override _load_symbol_interval to simulate error
        def mock_load_with_error(*args, **kwargs):
            raise Exception("Simulated network error")
        
        data_loader._load_symbol_interval = mock_load_with_error
        
        symbols = ["BTC/USDT"]
        intervals = [IntervalLevel.LEVEL_1HOUR]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 1, 1, 0, 0)
        exchanges = ["binance"]

        # Should handle errors gracefully
        results = data_loader.load_historical_kdata(
            symbols=symbols,
            intervals=intervals,
            start_date=start_date,
            end_date=end_date,
            exchanges=exchanges
        )

        # Should return empty results rather than crashing
        assert len(results) == 0
        assert data_loader.stats["failed_requests"] > 0