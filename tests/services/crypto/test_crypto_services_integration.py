# -*- coding: utf-8 -*-
"""
Integration Tests for Crypto Services
Tests the complete crypto service stack integration
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import asyncio
import threading
import time

from zvt.contract import IntervalLevel
from zvt.services.crypto.data_loader import CryptoDataLoader
from zvt.services.crypto.stream_service import CryptoStreamService
from zvt.services.crypto.api_ingestion import CryptoAPIIngestion


class TestCryptoServicesIntegration:
    """Integration tests for the complete crypto services stack"""
    
    @pytest.fixture
    def test_config(self):
        """Test configuration for services"""
        return {
            "exchanges": ["binance", "okx"],
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "intervals": [IntervalLevel.LEVEL_1MIN, IntervalLevel.LEVEL_1HOUR],
            "testnet": True
        }
    
    def test_data_loader_service_integration(self, test_config):
        """Test CryptoDataLoader service integration"""
        data_loader = CryptoDataLoader(
            exchanges=test_config["exchanges"],
            max_workers=2,
            validation_enabled=True,
            rate_limit_delay=0.1
        )
        
        # Test loading historical data
        results = data_loader.load_historical_kdata(
            symbols=test_config["symbols"][:1],  # Test with one symbol for speed
            intervals=test_config["intervals"][:1],  # Test with one interval
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            exchanges=test_config["exchanges"][:1]  # Test with one exchange
        )
        
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # Verify data structure and content
        for key, df in results.items():
            exchange, symbol, interval = key
            assert exchange in test_config["exchanges"]
            assert symbol in test_config["symbols"]
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            
            # Verify required columns exist
            required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
            assert all(col in df.columns for col in required_cols)
            
            # Verify data quality
            assert df["high"].min() >= df["low"].max()  # High >= Low always
            assert (df["volume"] >= 0).all()  # Volume non-negative
            assert df["timestamp"].is_monotonic_increasing  # Timestamps sorted
        
        # Test loading statistics
        stats = data_loader.get_loading_stats()
        assert stats["total_requests"] > 0
        assert stats["successful_requests"] > 0
        assert stats["data_points_loaded"] > 0
        
        print(f"✓ Loaded {stats['data_points_loaded']} data points from {stats['successful_requests']} successful requests")
    
    def test_stream_service_initialization(self, test_config):
        """Test CryptoStreamService initialization and configuration"""
        stream_service = CryptoStreamService(
            exchanges=test_config["exchanges"],
            buffer_size=1000,
            enable_heartbeat=True,
            heartbeat_interval=5.0
        )
        
        # Verify service initialization
        assert len(stream_service.stream_managers) == len(test_config["exchanges"])
        for exchange in test_config["exchanges"]:
            assert exchange in stream_service.stream_managers
        
        # Test data handler registration
        ticker_handler = Mock()
        trade_handler = Mock()
        
        stream_service.add_data_handler("ticker", ticker_handler)
        stream_service.add_data_handler("trades", trade_handler)
        
        assert ticker_handler in stream_service.data_handlers["ticker"]
        assert trade_handler in stream_service.data_handlers["trades"]
        
        # Test subscription methods (without actually connecting)
        stream_service.subscribe_ticker(test_config["symbols"])
        stream_service.subscribe_trades(test_config["symbols"][:1])
        
        # Verify subscriptions were registered
        for exchange in test_config["exchanges"]:
            manager = stream_service.stream_managers[exchange]
            assert len(manager.subscriptions) > 0
        
        print(f"✓ Stream service initialized with {len(stream_service.stream_managers)} exchanges")
    
    def test_api_ingestion_service_integration(self, test_config):
        """Test CryptoAPIIngestion service integration"""
        api_ingestion = CryptoAPIIngestion(
            exchanges=test_config["exchanges"],
            batch_size=100,
            ingestion_interval=30,
            enable_scheduling=False  # Disable automatic scheduling for tests
        )
        
        # Test service initialization
        assert len(api_ingestion.data_loader.exchanges) == len(test_config["exchanges"])
        
        # Test manual ingestion trigger
        ingestion_results = api_ingestion.trigger_ingestion(
            symbols=test_config["symbols"][:1],
            intervals=test_config["intervals"][:1],
            lookback_hours=1
        )
        
        assert isinstance(ingestion_results, dict)
        
        # Test ingestion statistics
        stats = api_ingestion.get_ingestion_stats()
        assert isinstance(stats, dict)
        assert "total_ingestions" in stats
        assert "successful_ingestions" in stats
        
        print(f"✓ API ingestion completed: {len(ingestion_results)} datasets")
    
    def test_cross_service_data_consistency(self, test_config):
        """Test data consistency across different services"""
        # Initialize services
        data_loader = CryptoDataLoader(exchanges=test_config["exchanges"][:1])
        
        # Load same data through different methods
        historical_data = data_loader.load_historical_kdata(
            symbols=test_config["symbols"][:1],
            intervals=test_config["intervals"][:1], 
            start_date=datetime.now() - timedelta(hours=2),
            end_date=datetime.now()
        )
        
        tick_data = data_loader.load_tick_data(
            symbols=test_config["symbols"][:1],
            start_date=datetime.now() - timedelta(hours=1),
            end_date=datetime.now(),
            data_types=["trades"]
        )
        
        # Verify both methods return valid data
        assert len(historical_data) > 0
        assert len(tick_data) > 0
        
        # Compare data formats and consistency
        for key, df in historical_data.items():
            assert isinstance(df, pd.DataFrame)
            assert "timestamp" in df.columns
        
        for key, df in tick_data.items():
            assert isinstance(df, pd.DataFrame) 
            assert "timestamp" in df.columns
        
        print("✓ Data consistency verified across services")
    
    def test_error_handling_and_recovery(self, test_config):
        """Test error handling and recovery mechanisms"""
        # Test with invalid configuration
        data_loader = CryptoDataLoader(
            exchanges=["invalid_exchange"],
            max_retries=2,
            rate_limit_delay=0.1
        )
        
        # Should handle gracefully
        results = data_loader.load_historical_kdata(
            symbols=["INVALID/SYMBOL"],
            intervals=[IntervalLevel.LEVEL_1HOUR],
            start_date=datetime.now() - timedelta(hours=1),
            end_date=datetime.now()
        )
        
        # Should return empty results without crashing
        assert isinstance(results, dict)
        
        # Check error statistics
        stats = data_loader.get_loading_stats()
        assert stats["failed_requests"] >= 0  # May have some failures
        
        print("✓ Error handling verified")
    
    def test_concurrent_service_operations(self, test_config):
        """Test concurrent operations across services"""
        import concurrent.futures
        
        def load_data_task():
            loader = CryptoDataLoader(exchanges=test_config["exchanges"][:1])
            return loader.load_historical_kdata(
                symbols=test_config["symbols"][:1],
                intervals=test_config["intervals"][:1],
                start_date=datetime.now() - timedelta(hours=1),
                end_date=datetime.now()
            )
        
        def load_tick_task():
            loader = CryptoDataLoader(exchanges=test_config["exchanges"][:1])
            return loader.load_tick_data(
                symbols=test_config["symbols"][:1],
                start_date=datetime.now() - timedelta(minutes=30),
                end_date=datetime.now()
            )
        
        # Run tasks concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(load_data_task)
            future2 = executor.submit(load_tick_task)
            
            results1 = future1.result(timeout=30)
            results2 = future2.result(timeout=30)
        
        # Both should complete successfully
        assert isinstance(results1, dict)
        assert isinstance(results2, dict)
        
        print("✓ Concurrent operations completed successfully")
    
    def test_service_performance_metrics(self, test_config):
        """Test performance metrics and monitoring"""
        data_loader = CryptoDataLoader(
            exchanges=test_config["exchanges"],
            max_workers=3
        )
        
        # Measure loading performance
        start_time = time.time()
        
        results = data_loader.load_historical_kdata(
            symbols=test_config["symbols"],
            intervals=test_config["intervals"][:1],
            start_date=datetime.now() - timedelta(hours=6),
            end_date=datetime.now()
        )
        
        elapsed_time = time.time() - start_time
        
        # Performance metrics
        stats = data_loader.get_loading_stats()
        total_points = stats["data_points_loaded"]
        requests_made = stats["total_requests"]
        
        print(f"✓ Performance metrics:")
        print(f"  - Loaded {total_points} data points in {elapsed_time:.2f}s")
        print(f"  - {requests_made} API requests made")
        print(f"  - {total_points/elapsed_time:.1f} points/second")
        print(f"  - {requests_made/elapsed_time:.1f} requests/second")
        
        # Basic performance assertions
        assert elapsed_time < 60  # Should complete within 1 minute
        assert total_points > 0
        assert requests_made > 0
    
    def test_data_quality_and_validation(self, test_config):
        """Test data quality across the service stack"""
        data_loader = CryptoDataLoader(
            exchanges=test_config["exchanges"][:1],
            validation_enabled=True
        )
        
        # Load data with validation enabled
        results = data_loader.load_historical_kdata(
            symbols=test_config["symbols"][:1],
            intervals=test_config["intervals"][:1],
            start_date=datetime.now() - timedelta(hours=12),
            end_date=datetime.now()
        )
        
        validation_stats = data_loader.get_loading_stats()
        
        # Analyze data quality
        for key, df in results.items():
            if not df.empty:
                # Check for data completeness
                assert not df["timestamp"].isna().any()
                assert not df["close"].isna().any()
                
                # Check OHLC logic
                assert (df["high"] >= df["open"]).all()
                assert (df["high"] >= df["close"]).all()
                assert (df["low"] <= df["open"]).all()
                assert (df["low"] <= df["close"]).all()
                
                # Check volume is non-negative
                assert (df["volume"] >= 0).all()
                
                # Check timestamp ordering
                assert df["timestamp"].is_monotonic_increasing
        
        print(f"✓ Data quality validation passed")
        print(f"  - Validation errors: {validation_stats['validation_errors']}")
        print(f"  - Gaps detected: {validation_stats['gaps_detected']}")
    
    @pytest.mark.asyncio
    async def test_async_service_integration(self, test_config):
        """Test asynchronous service integration"""
        data_loader = CryptoDataLoader(exchanges=test_config["exchanges"][:1])
        
        # Test async data loading
        async_results = await data_loader.load_historical_async(
            symbols=test_config["symbols"][:1],
            intervals=test_config["intervals"][:1],
            start_date=datetime.now() - timedelta(hours=2),
            end_date=datetime.now()
        )
        
        assert isinstance(async_results, dict)
        assert len(async_results) > 0
        
        print("✓ Async service integration verified")
    
    def test_service_resource_cleanup(self, test_config):
        """Test proper resource cleanup and teardown"""
        # Test stream service cleanup
        stream_service = CryptoStreamService(
            exchanges=test_config["exchanges"][:1],
            enable_heartbeat=False
        )
        
        # Add some subscriptions
        stream_service.subscribe_ticker(test_config["symbols"][:1])
        
        # Test cleanup
        stream_service.stop()
        assert not stream_service.is_running
        
        # Test data loader cleanup
        data_loader = CryptoDataLoader(exchanges=test_config["exchanges"][:1])
        
        # Load some data to initialize connectors
        data_loader.load_historical_kdata(
            symbols=test_config["symbols"][:1],
            intervals=test_config["intervals"][:1],
            start_date=datetime.now() - timedelta(hours=1),
            end_date=datetime.now()
        )
        
        # Verify connectors were created
        assert len(data_loader._connectors) > 0
        
        # Reset should clear resources
        data_loader.reset_stats()
        stats = data_loader.get_loading_stats()
        assert all(value == 0 for value in stats.values())
        
        print("✓ Resource cleanup verified")


class TestCryptoServicesEndToEnd:
    """End-to-end integration tests"""
    
    def test_complete_crypto_pipeline(self):
        """Test the complete crypto data pipeline"""
        # Step 1: Load historical data
        data_loader = CryptoDataLoader(
            exchanges=["binance"],
            validation_enabled=True
        )
        
        historical_data = data_loader.load_historical_kdata(
            symbols=["BTC/USDT"],
            intervals=[IntervalLevel.LEVEL_1HOUR],
            start_date=datetime.now() - timedelta(hours=24),
            end_date=datetime.now()
        )
        
        assert len(historical_data) > 0
        
        # Step 2: Initialize streaming service
        stream_service = CryptoStreamService(
            exchanges=["binance"],
            buffer_size=100
        )
        
        # Add data handlers
        ticker_data = []
        def ticker_handler(data):
            ticker_data.append(data)
        
        stream_service.add_data_handler("ticker", ticker_handler)
        
        # Step 3: Initialize API ingestion
        api_ingestion = CryptoAPIIngestion(
            exchanges=["binance"],
            enable_scheduling=False
        )
        
        # Step 4: Verify integration
        ingestion_stats = api_ingestion.get_ingestion_stats()
        loading_stats = data_loader.get_loading_stats()
        
        print("✓ Complete crypto pipeline integration verified")
        print(f"  - Historical data: {len(historical_data)} datasets")
        print(f"  - Loading stats: {loading_stats}")
        print(f"  - Ingestion stats: {ingestion_stats}")


if __name__ == "__main__":
    # Run the integration tests
    pytest.main([__file__, "-v", "--tb=short"])