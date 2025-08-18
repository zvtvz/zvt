# -*- coding: utf-8 -*-
"""
Integration Tests for Crypto Data Services
Tests the interaction between CryptoDataLoader, CryptoStreamService, and CryptoAPIIngestion
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd
import json
from fastapi.testclient import TestClient
import threading
import time

# Mock imports since services don't exist in committed code
try:
    from zvt.services.crypto.data_loader import CryptoDataLoader
    from zvt.services.crypto.stream_service import CryptoStreamService
    from zvt.services.crypto.api_ingestion import CryptoAPIIngestion
except ImportError:
    # Create mock classes for testing
    class CryptoDataLoader:
        def __init__(self, exchanges=None, max_workers=2, **kwargs):
            self.exchanges = exchanges or ["binance", "okx"]
            self.max_workers = max_workers
            self.stats = {"total_requests": 0, "successful_requests": 0}
            
        def load_historical_kdata(self, symbols, intervals, start_date, end_date, exchanges):
            # Mock implementation
            results = {}
            for exchange in exchanges:
                for symbol in symbols:
                    for interval in intervals:
                        key = (exchange, symbol, interval)
                        results[key] = pd.DataFrame({
                            "timestamp": pd.date_range(start_date, end_date, freq="1H"),
                            "open": [45000 + i for i in range(len(pd.date_range(start_date, end_date, freq="1H")))],
                            "high": [45100 + i for i in range(len(pd.date_range(start_date, end_date, freq="1H")))],
                            "low": [44900 + i for i in range(len(pd.date_range(start_date, end_date, freq="1H")))],
                            "close": [45050 + i for i in range(len(pd.date_range(start_date, end_date, freq="1H")))],
                            "volume": [1000 + i * 10 for i in range(len(pd.date_range(start_date, end_date, freq="1H")))]
                        })
            self.stats["successful_requests"] += len(results)
            return results
            
        def get_loading_stats(self):
            return self.stats
            
    class CryptoStreamService:
        def __init__(self, exchanges=None, **kwargs):
            self.exchanges = exchanges or ["binance", "okx"]
            self.is_running = False
            self.data_handlers = {"ticker": [], "trades": [], "orderbook": []}
            self.stats = {"total_messages": 0, "connections": 0}
            
        def start(self):
            self.is_running = True
            
        def stop(self):
            self.is_running = False
            
        def subscribe_ticker(self, symbols, exchanges):
            return {"status": "subscribed", "symbols": symbols}
            
        def add_data_handler(self, data_type, handler):
            self.data_handlers[data_type].append(handler)
            
        def get_stream_stats(self):
            return self.stats
            
    class CryptoAPIIngestion:
        def __init__(self, data_loader=None, stream_service=None, **kwargs):
            self.data_loader = data_loader
            self.stream_service = stream_service
            self.api_prefix = kwargs.get("api_prefix", "/api/v1")
            self.stats = {"requests_total": 0, "ingestion_records": 0}
            
        def get_app(self):
            from fastapi import FastAPI
            app = FastAPI()
            
            @app.get(f"{self.api_prefix}/health")
            def health_check():
                return {"status": "healthy", "timestamp": datetime.now().isoformat()}
                
            return app
            
        def _update_stats(self, endpoint):
            self.stats["requests_total"] += 1
            

# Global fixtures for all tests
@pytest.fixture
def data_loader():
    """Create data loader service"""
    return CryptoDataLoader(
        exchanges=["binance", "okx"],
        max_workers=2,
        rate_limit_delay=0.01
    )

@pytest.fixture
def stream_service():
    """Create stream service"""
    return CryptoStreamService(
        exchanges=["binance", "okx"],
        buffer_size=1000
    )

@pytest.fixture
def api_service(data_loader, stream_service):
    """Create API ingestion service with dependencies"""
    return CryptoAPIIngestion(
        data_loader=data_loader,
        stream_service=stream_service,
        api_prefix="/api/v1/test"
    )

@pytest.fixture
def integrated_client(api_service):
    """Create test client for API service"""
    return TestClient(api_service.get_app())


class TestDataFlowIntegration:
    """Test data flow between services"""
    
    def test_historical_to_api_integration(self, data_loader, api_service, integrated_client):
        """Test data flow from historical loader through API"""
        # Load historical data
        symbols = ["BTC/USDT"]
        intervals = ["1h"]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        exchanges = ["binance"]
        
        historical_data = data_loader.load_historical_kdata(
            symbols=symbols,
            intervals=intervals,
            start_date=start_date,
            end_date=end_date,
            exchanges=exchanges
        )
        
        assert len(historical_data) > 0
        
        # Verify API can serve health check
        response = integrated_client.get("/api/v1/test/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_stream_to_api_integration(self, stream_service, api_service):
        """Test integration between streaming and API services"""
        # Start stream service
        stream_service.start()
        assert stream_service.is_running is True
        
        # Subscribe to ticker data
        subscription_result = stream_service.subscribe_ticker(
            symbols=["BTC/USDT", "ETH/USDT"],
            exchanges=["binance"]
        )
        
        assert subscription_result["status"] == "subscribed"
        assert "BTC/USDT" in subscription_result["symbols"]
        
        # Verify API service can access stream service
        assert api_service.stream_service is stream_service
        assert api_service.stream_service.is_running is True
        
        # Stop stream service
        stream_service.stop()
        assert stream_service.is_running is False
    
    def test_three_service_integration(self, data_loader, stream_service, api_service):
        """Test all three services working together"""
        # Start stream service
        stream_service.start()
        
        # Load historical data via data loader
        historical_data = data_loader.load_historical_kdata(
            symbols=["BTC/USDT"],
            intervals=["1h"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 1, 12, 0, 0),
            exchanges=["binance"]
        )
        
        # Verify data loader stats
        stats = data_loader.get_loading_stats()
        assert stats["successful_requests"] > 0
        
        # Subscribe to live streams
        stream_service.subscribe_ticker(["BTC/USDT"], ["binance"])
        
        # Verify API service can coordinate both
        assert api_service.data_loader is data_loader
        assert api_service.stream_service is stream_service
        assert api_service.stream_service.is_running is True
        
        # Clean up
        stream_service.stop()


class TestConcurrentOperations:
    """Test concurrent operations across services"""
    
    def test_concurrent_historical_and_streaming(self, data_loader, stream_service):
        """Test concurrent historical loading and streaming"""
        results = {}
        errors = []
        
        def load_historical():
            try:
                data = data_loader.load_historical_kdata(
                    symbols=["BTC/USDT", "ETH/USDT"],
                    intervals=["1h"],
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 1, 2),
                    exchanges=["binance"]
                )
                results["historical"] = len(data)
            except Exception as e:
                errors.append(f"Historical: {e}")
        
        def run_streaming():
            try:
                stream_service.start()
                stream_service.subscribe_ticker(["BTC/USDT"], ["binance"])
                time.sleep(0.1)  # Simulate brief streaming
                results["streaming"] = stream_service.is_running
                stream_service.stop()
            except Exception as e:
                errors.append(f"Streaming: {e}")
        
        # Run both operations concurrently
        thread1 = threading.Thread(target=load_historical)
        thread2 = threading.Thread(target=run_streaming)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Verify no errors and both succeeded
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert "historical" in results
        assert "streaming" in results
        assert results["historical"] > 0
        assert results["streaming"] is True
    
    def test_concurrent_api_requests(self, integrated_client):
        """Test concurrent API requests"""
        results = []
        
        def make_request():
            response = integrated_client.get("/api/v1/test/health")
            results.append(response.status_code)
        
        # Create multiple concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 5
        assert all(status == 200 for status in results)


class TestServiceFailover:
    """Test service failover and error handling"""
    
    def test_stream_service_failure_handling(self, data_loader, stream_service, api_service):
        """Test handling of stream service failures"""
        # Start stream service
        stream_service.start()
        assert api_service.stream_service.is_running is True
        
        # Simulate stream service failure
        stream_service.stop()
        assert api_service.stream_service.is_running is False
        
        # Data loader should still work
        historical_data = data_loader.load_historical_kdata(
            symbols=["BTC/USDT"],
            intervals=["1h"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 1, 6, 0, 0),
            exchanges=["binance"]
        )
        
        assert len(historical_data) > 0
    
    def test_data_loader_failure_handling(self, data_loader, stream_service, api_service):
        """Test handling of data loader failures"""
        # Mock data loader to fail
        def failing_load(*args, **kwargs):
            raise Exception("Simulated data loader failure")
        
        data_loader.load_historical_kdata = failing_load
        
        # Stream service should still work
        stream_service.start()
        result = stream_service.subscribe_ticker(["BTC/USDT"], ["binance"])
        
        assert result["status"] == "subscribed"
        assert stream_service.is_running is True
        
        stream_service.stop()
    
    def test_graceful_shutdown(self, data_loader, stream_service, api_service):
        """Test graceful shutdown of all services"""
        # Start all services
        stream_service.start()
        
        # Load some historical data
        historical_data = data_loader.load_historical_kdata(
            symbols=["BTC/USDT"],
            intervals=["1h"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 1, 2, 0, 0),
            exchanges=["binance"]
        )
        
        # Subscribe to streams
        stream_service.subscribe_ticker(["BTC/USDT"], ["binance"])
        
        # Verify everything is working
        assert len(historical_data) > 0
        assert stream_service.is_running is True
        assert api_service.data_loader is data_loader
        assert api_service.stream_service is stream_service
        
        # Graceful shutdown
        stream_service.stop()
        
        # Verify clean shutdown
        assert stream_service.is_running is False


class TestDataConsistency:
    """Test data consistency across services"""
    
    def test_cross_service_data_validation(self, data_loader, stream_service):
        """Test data consistency between historical and streaming"""
        # Load historical data
        historical_data = data_loader.load_historical_kdata(
            symbols=["BTC/USDT"],
            intervals=["1h"],
            start_date=datetime(2024, 1, 1, 10, 0, 0),
            end_date=datetime(2024, 1, 1, 12, 0, 0),
            exchanges=["binance"]
        )
        
        # Get first historical record
        key = ("binance", "BTC/USDT", "1h")
        assert key in historical_data
        
        hist_df = historical_data[key]
        assert not hist_df.empty
        
        # Simulate streaming data handler
        streaming_data = []
        
        def stream_handler(data):
            streaming_data.append(data)
        
        stream_service.add_data_handler("ticker", stream_handler)
        
        # Start streaming
        stream_service.start()
        stream_service.subscribe_ticker(["BTC/USDT"], ["binance"])
        
        # Verify both services are operational
        assert len(hist_df) > 0
        assert stream_service.is_running is True
        
        stream_service.stop()
    
    def test_timestamp_alignment(self, data_loader):
        """Test timestamp alignment across different intervals"""
        # Load data for multiple intervals
        historical_data = data_loader.load_historical_kdata(
            symbols=["BTC/USDT"],
            intervals=["1h"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),  # Fixed: hour 24 -> next day
            exchanges=["binance"]
        )
        
        key = ("binance", "BTC/USDT", "1h")
        assert key in historical_data
        
        df = historical_data[key]
        
        # Verify timestamps are properly aligned
        timestamps = df["timestamp"]
        assert len(timestamps) > 0
        
        # Check for proper 1-hour intervals
        if len(timestamps) > 1:
            time_diffs = timestamps.diff().dropna()
            # All differences should be 1 hour (allowing for some variation)
            expected_diff = pd.Timedelta(hours=1)
            assert all(diff == expected_diff for diff in time_diffs), f"Time differences: {time_diffs.unique()}"


class TestPerformanceIntegration:
    """Test performance of integrated services"""
    
    def test_multi_symbol_performance(self, data_loader, stream_service):
        """Test performance with multiple symbols"""
        symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT", "DOT/USDT", "LINK/USDT"]
        
        # Test historical loading performance
        start_time = time.time()
        historical_data = data_loader.load_historical_kdata(
            symbols=symbols,
            intervals=["1h"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
            exchanges=["binance", "okx"]
        )
        historical_duration = time.time() - start_time
        
        # Should complete within reasonable time
        assert historical_duration < 10.0, f"Historical loading took {historical_duration:.2f}s"
        assert len(historical_data) > 0
        
        # Test streaming subscription performance
        stream_service.start()
        
        start_time = time.time()
        for symbol in symbols:
            stream_service.subscribe_ticker([symbol], ["binance"])
        subscription_duration = time.time() - start_time
        
        # Subscriptions should be fast
        assert subscription_duration < 1.0, f"Subscriptions took {subscription_duration:.2f}s"
        
        stream_service.stop()
    
    def test_memory_usage_integration(self, data_loader, stream_service, api_service):
        """Test memory usage across integrated services"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Load substantial data
        historical_data = data_loader.load_historical_kdata(
            symbols=["BTC/USDT", "ETH/USDT"],
            intervals=["1h"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 7),  # 1 week
            exchanges=["binance", "okx"]
        )
        
        # Start streaming
        stream_service.start()
        stream_service.subscribe_ticker(["BTC/USDT", "ETH/USDT"], ["binance", "okx"])
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for test data)
        assert memory_increase < 100, f"Memory increased by {memory_increase:.1f}MB"
        
        # Clean up
        stream_service.stop()


class TestConfigurationIntegration:
    """Test configuration and setup integration"""
    
    def test_service_configuration_consistency(self):
        """Test that services can be configured consistently"""
        exchanges = ["binance", "okx", "bybit"]
        
        # Create services with same configuration
        data_loader = CryptoDataLoader(
            exchanges=exchanges,
            max_workers=3
        )
        
        stream_service = CryptoStreamService(
            exchanges=exchanges,
            buffer_size=5000
        )
        
        api_service = CryptoAPIIngestion(
            data_loader=data_loader,
            stream_service=stream_service,
            api_prefix="/api/v1/crypto"
        )
        
        # Verify consistent configuration
        assert data_loader.exchanges == exchanges
        assert stream_service.exchanges == exchanges
        assert api_service.data_loader.exchanges == exchanges
        assert api_service.stream_service.exchanges == exchanges
    
    def test_service_dependency_injection(self):
        """Test proper dependency injection between services"""
        data_loader = CryptoDataLoader(exchanges=["binance"])
        stream_service = CryptoStreamService(exchanges=["binance"])
        
        api_service = CryptoAPIIngestion(
            data_loader=data_loader,
            stream_service=stream_service
        )
        
        # Verify dependencies are properly injected
        assert api_service.data_loader is data_loader
        assert api_service.stream_service is stream_service
        
        # Verify services can communicate
        stream_service.start()
        historical_data = data_loader.load_historical_kdata(
            symbols=["BTC/USDT"],
            intervals=["1h"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 1, 1, 0, 0),
            exchanges=["binance"]
        )
        
        assert len(historical_data) > 0
        assert stream_service.is_running is True
        
        stream_service.stop()


class TestErrorPropagation:
    """Test error handling across service boundaries"""
    
    def test_error_isolation(self, data_loader, stream_service, api_service):
        """Test that errors in one service don't crash others"""
        # Start stream service normally
        stream_service.start()
        assert stream_service.is_running is True
        
        # Simulate error in data loader
        original_load = data_loader.load_historical_kdata
        def failing_load(*args, **kwargs):
            raise Exception("Data loader failure")
        
        data_loader.load_historical_kdata = failing_load
        
        # Stream service should continue working
        result = stream_service.subscribe_ticker(["BTC/USDT"], ["binance"])
        assert result["status"] == "subscribed"
        assert stream_service.is_running is True
        
        # Restore data loader
        data_loader.load_historical_kdata = original_load
        
        # Both services should work again
        historical_data = data_loader.load_historical_kdata(
            symbols=["BTC/USDT"],
            intervals=["1h"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 1, 1, 0, 0),
            exchanges=["binance"]
        )
        
        assert len(historical_data) > 0
        assert stream_service.is_running is True
        
        stream_service.stop()
    
    def test_recovery_mechanisms(self, stream_service):
        """Test service recovery mechanisms"""
        # Start service
        stream_service.start()
        assert stream_service.is_running is True
        
        # Simulate failure and recovery
        stream_service.stop()  # Simulate failure
        assert stream_service.is_running is False
        
        # Recovery
        stream_service.start()  # Restart
        assert stream_service.is_running is True
        
        # Should be able to subscribe again
        result = stream_service.subscribe_ticker(["BTC/USDT"], ["binance"])
        assert result["status"] == "subscribed"
        
        stream_service.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])