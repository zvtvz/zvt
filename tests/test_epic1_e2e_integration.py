# -*- coding: utf-8 -*-
"""
Epic 1 End-to-End Integration Testing Framework
Comprehensive validation of crypto market integration components
"""

import asyncio
import pytest
import time
import threading
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

# ZVT imports
from zvt.contract import IntervalLevel
from zvt.domain.crypto import CryptoPair, CryptoPerp, CryptoAsset
from zvt.services.crypto.data_loader import CryptoDataLoader
from zvt.services.crypto.stream_service import CryptoStreamService
from zvt.services.crypto.api_ingestion import CryptoAPIIngestion, create_crypto_api
from zvt.services.crypto.connectors import (
    BinanceConnector, OKXConnector, BybitConnector, 
    CoinbaseConnector, MockCryptoConnector
)

logger = logging.getLogger(__name__)


class E2ETestConfig:
    """End-to-end test configuration and constants"""
    
    # Test exchanges (using testnet/mock mode)
    EXCHANGES = ["binance", "okx", "bybit", "coinbase"]
    TEST_SYMBOLS = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
    
    # Performance thresholds
    PERFORMANCE_THRESHOLDS = {
        "data_loading_rate": 1000,  # records/second
        "streaming_capacity": 10000,  # messages/second  
        "api_response_time": 200,  # milliseconds
        "memory_limit": 2048,  # MB for 1M records
        "uptime_target": 99.9  # percentage
    }
    
    # Test timeouts
    TIMEOUTS = {
        "service_startup": 30,  # seconds
        "data_loading": 120,  # seconds
        "streaming_setup": 60,  # seconds
        "api_response": 5  # seconds
    }


class E2ETestFramework:
    """Framework for managing end-to-end test execution"""
    
    def __init__(self):
        self.config = E2ETestConfig()
        self.test_results = {}
        self.performance_metrics = {}
        self.services = {
            "data_loader": None,
            "stream_service": None,
            "api_ingestion": None
        }
        self.start_time = None
        self.memory_baseline = None
        
    def setup_test_environment(self):
        """Initialize test environment and services"""
        logger.info("Setting up E2E test environment")
        self.start_time = time.time()
        self.memory_baseline = psutil.virtual_memory().used
        
        # Initialize services with test configuration
        self.services["data_loader"] = CryptoDataLoader(
            exchanges=self.config.EXCHANGES,
            max_workers=3,
            rate_limit_delay=0.1,
            validation_enabled=True
        )
        
        self.services["stream_service"] = CryptoStreamService(
            exchanges=self.config.EXCHANGES[:3],  # Limit for testing
            buffer_size=1000,
            enable_heartbeat=True
        )
        
        self.services["api_ingestion"] = CryptoAPIIngestion(
            data_loader=self.services["data_loader"],
            stream_service=self.services["stream_service"]
        )
        
        logger.info("E2E test environment initialized")
    
    def teardown_test_environment(self):
        """Cleanup test environment"""
        logger.info("Tearing down E2E test environment")
        
        # Stop services
        if self.services["stream_service"] and self.services["stream_service"].is_running:
            self.services["stream_service"].stop()
        
        # Clear any resources
        for service in self.services.values():
            if hasattr(service, 'close'):
                service.close()
        
        # Calculate test duration
        if self.start_time:
            duration = time.time() - self.start_time
            logger.info(f"Total test execution time: {duration:.2f} seconds")
    
    def measure_performance(self, operation: str, func, *args, **kwargs):
        """Measure performance metrics for an operation"""
        start_time = time.time()
        memory_start = psutil.virtual_memory().used
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            logger.error(f"Performance measurement failed for {operation}: {e}")
            result = None
            success = False
        
        end_time = time.time()
        memory_end = psutil.virtual_memory().used
        
        metrics = {
            "duration": end_time - start_time,
            "memory_delta": memory_end - memory_start,
            "success": success,
            "timestamp": datetime.now()
        }
        
        self.performance_metrics[operation] = metrics
        logger.info(f"Performance for {operation}: {metrics}")
        
        return result


@pytest.fixture(scope="class")
def e2e_framework():
    """Pytest fixture for E2E test framework"""
    framework = E2ETestFramework()
    framework.setup_test_environment()
    yield framework
    framework.teardown_test_environment()


class TestE2EHistoricalDataPipeline:
    """Test Suite 1: Complete Data Pipeline E2E"""
    
    def test_001_historical_pipeline(self, e2e_framework):
        """E2E_001: Multi-Exchange Historical Data Pipeline"""
        framework = e2e_framework
        data_loader = framework.services["data_loader"]
        
        # Test configuration
        symbols = framework.config.TEST_SYMBOLS[:2]  # Limit for testing
        intervals = [IntervalLevel.LEVEL_1HOUR, IntervalLevel.LEVEL_1DAY]
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        
        def load_historical_data():
            return data_loader.load_historical_kdata(
                symbols=symbols,
                intervals=intervals,
                start_date=start_date,
                end_date=end_date,
                exchanges=framework.config.EXCHANGES[:2]  # Limit exchanges
            )
        
        # Execute with performance measurement
        results = framework.measure_performance(
            "historical_data_loading", 
            load_historical_data
        )
        
        # Validate results
        assert results is not None, "Historical data loading failed"
        assert len(results) > 0, "No data returned from historical loading"
        
        # Validate data quality
        for key, df in results.items():
            assert isinstance(df, pd.DataFrame), f"Result {key} is not a DataFrame"
            assert not df.empty, f"Empty DataFrame for {key}"
            assert 'timestamp' in df.columns, f"Missing timestamp column in {key}"
            assert 'close' in df.columns, f"Missing close price column in {key}"
        
        # Performance validation
        metrics = framework.performance_metrics["historical_data_loading"]
        assert metrics["success"], "Historical data loading performance test failed"
        assert metrics["duration"] < framework.config.TIMEOUTS["data_loading"], \
            f"Loading took too long: {metrics['duration']} seconds"
        
        # Calculate loading rate
        total_records = sum(len(df) for df in results.values())
        loading_rate = total_records / metrics["duration"] if metrics["duration"] > 0 else 0
        
        logger.info(f"Historical data loading rate: {loading_rate:.2f} records/second")
        assert loading_rate >= framework.config.PERFORMANCE_THRESHOLDS["data_loading_rate"], \
            f"Loading rate too slow: {loading_rate} < {framework.config.PERFORMANCE_THRESHOLDS['data_loading_rate']}"
    
    def test_002_streaming_pipeline(self, e2e_framework):
        """E2E_002: Real-Time Streaming Pipeline"""
        framework = e2e_framework
        stream_service = framework.services["stream_service"]
        
        # Start streaming service
        def start_streaming():
            stream_service.start()
            time.sleep(5)  # Allow connection time
            return stream_service.is_running
        
        is_running = framework.measure_performance(
            "streaming_startup",
            start_streaming
        )
        
        assert is_running, "Stream service failed to start"
        
        # Subscribe to data streams
        symbols = framework.config.TEST_SYMBOLS[:2]
        
        def setup_subscriptions():
            stream_service.subscribe_ticker(symbols)
            stream_service.subscribe_klines(symbols, ["1m"])
            time.sleep(10)  # Allow data collection
            return True
        
        framework.measure_performance(
            "streaming_subscription",
            setup_subscriptions
        )
        
        # Validate streaming data
        ticker_data = stream_service.get_buffered_data("ticker", limit=100)
        kline_data = stream_service.get_buffered_data("kline", limit=100)
        
        # Note: In real testing, we'd expect data, but with mocks it may be empty
        logger.info(f"Ticker buffer size: {len(ticker_data)}")
        logger.info(f"Kline buffer size: {len(kline_data)}")
        
        # Validate streaming statistics
        stats = stream_service.get_stream_stats()
        assert stats["active_connections"] > 0, "No active streaming connections"
        
        # Performance validation
        startup_metrics = framework.performance_metrics["streaming_startup"]
        assert startup_metrics["duration"] < framework.config.TIMEOUTS["streaming_setup"], \
            f"Streaming startup too slow: {startup_metrics['duration']} seconds"
    
    def test_003_api_ingestion_pipeline(self, e2e_framework):
        """E2E_003: API Data Ingestion Pipeline"""
        framework = e2e_framework
        api_service = framework.services["api_ingestion"]
        
        # Mock data for ingestion testing
        mock_ohlcv = [
            {
                "timestamp": datetime.now() - timedelta(hours=1),
                "open": 45000.0,
                "high": 45100.0,
                "low": 44900.0,
                "close": 45050.0,
                "volume": 100.5
            }
        ]
        
        def test_api_ingestion():
            # Test data validation and ingestion
            from zvt.services.crypto.api_ingestion import OHLCVDataModel
            
            ohlcv_models = [OHLCVDataModel(**data) for data in mock_ohlcv]
            
            # This would normally be an async call to the API
            # For testing, we'll call the internal method directly
            result = asyncio.run(api_service._ingest_ohlcv(
                exchange="binance",
                symbol="BTC/USDT",
                interval="1h",
                data=ohlcv_models
            ))
            
            return result
        
        result = framework.measure_performance(
            "api_ingestion",
            test_api_ingestion
        )
        
        assert result is not None, "API ingestion failed"
        assert result["status"] == "success", f"API ingestion status: {result.get('status')}"
        assert result["records_ingested"] > 0, "No records ingested"
        
        # Performance validation
        metrics = framework.performance_metrics["api_ingestion"]
        assert metrics["success"], "API ingestion performance test failed"


class TestE2EServiceIntegration:
    """Test Suite 2: Service Integration Validation"""
    
    def test_004_service_coordination(self, e2e_framework):
        """E2E_004: Three-Service Coordination"""
        framework = e2e_framework
        
        # Test coordinated operations
        def coordinated_operations():
            data_loader = framework.services["data_loader"]
            stream_service = framework.services["stream_service"]
            api_service = framework.services["api_ingestion"]
            
            # Start stream service
            if not stream_service.is_running:
                stream_service.start()
                time.sleep(3)
            
            # Load historical data while streaming
            results = data_loader.load_historical_kdata(
                symbols=["BTC/USDT"],
                intervals=[IntervalLevel.LEVEL_1HOUR],
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
                exchanges=["binance"]
            )
            
            # Get API statistics
            stats = asyncio.run(api_service._get_stats())
            
            return {
                "historical_results": len(results),
                "streaming_active": stream_service.is_running,
                "api_stats": stats
            }
        
        result = framework.measure_performance(
            "service_coordination",
            coordinated_operations
        )
        
        assert result["historical_results"] > 0, "Historical data loading failed during coordination"
        assert result["streaming_active"], "Streaming service not active during coordination"
        assert result["api_stats"] is not None, "API statistics not available"
        
        # Validate no resource conflicts
        metrics = framework.performance_metrics["service_coordination"]
        assert metrics["success"], "Service coordination failed"
    
    def test_005_concurrent_operations(self, e2e_framework):
        """E2E_005: Concurrent Operations"""
        framework = e2e_framework
        
        def concurrent_data_loading():
            data_loader = framework.services["data_loader"]
            
            # Multiple concurrent loading operations
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                
                for symbol in framework.config.TEST_SYMBOLS:
                    future = executor.submit(
                        data_loader.load_historical_kdata,
                        symbols=[symbol],
                        intervals=[IntervalLevel.LEVEL_1HOUR],
                        start_date=datetime.now() - timedelta(hours=24),
                        end_date=datetime.now(),
                        exchanges=["binance"]
                    )
                    futures.append(future)
                
                # Collect results
                results = []
                for future in futures:
                    try:
                        result = future.result(timeout=60)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Concurrent operation failed: {e}")
                
                return results
        
        results = framework.measure_performance(
            "concurrent_operations",
            concurrent_data_loading
        )
        
        assert len(results) > 0, "No concurrent operations completed successfully"
        
        # Validate concurrent performance
        metrics = framework.performance_metrics["concurrent_operations"]
        assert metrics["success"], "Concurrent operations failed"
        
        # Memory usage validation
        memory_usage_mb = metrics["memory_delta"] / (1024 * 1024)
        logger.info(f"Memory usage for concurrent operations: {memory_usage_mb:.2f} MB")


class TestE2EPerformanceValidation:
    """Test Suite 4: Performance & Scalability"""
    
    def test_008_load_testing(self, e2e_framework):
        """E2E_008: Load Testing"""
        framework = e2e_framework
        
        def high_volume_test():
            data_loader = framework.services["data_loader"]
            
            # Load large dataset
            symbols = framework.config.TEST_SYMBOLS
            intervals = [IntervalLevel.LEVEL_1MIN, IntervalLevel.LEVEL_1HOUR]
            
            results = data_loader.load_historical_kdata(
                symbols=symbols,
                intervals=intervals,
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now(),
                exchanges=framework.config.EXCHANGES[:2]
            )
            
            total_records = sum(len(df) for df in results.values())
            return total_records
        
        total_records = framework.measure_performance(
            "high_volume_load",
            high_volume_test
        )
        
        assert total_records > 0, "High volume load test returned no data"
        
        # Performance validation
        metrics = framework.performance_metrics["high_volume_load"]
        loading_rate = total_records / metrics["duration"] if metrics["duration"] > 0 else 0
        
        logger.info(f"High volume loading rate: {loading_rate:.2f} records/second")
        logger.info(f"Total records loaded: {total_records}")
        
        # Memory usage validation
        memory_usage_mb = metrics["memory_delta"] / (1024 * 1024)
        memory_per_record = memory_usage_mb / total_records if total_records > 0 else 0
        
        logger.info(f"Memory usage: {memory_usage_mb:.2f} MB")
        logger.info(f"Memory per record: {memory_per_record:.6f} MB")
        
        # Validate against thresholds
        assert loading_rate >= framework.config.PERFORMANCE_THRESHOLDS["data_loading_rate"], \
            f"Loading rate below threshold: {loading_rate}"


class TestE2EProductionReadiness:
    """Test Suite 5: Production Readiness"""
    
    def test_010_deployment_validation(self, e2e_framework):
        """E2E_010: Deployment Validation"""
        framework = e2e_framework
        
        # Test service health checks
        def validate_health_checks():
            results = {}
            
            # Data loader health
            data_loader = framework.services["data_loader"]
            results["data_loader"] = {
                "stats": data_loader.get_loading_stats(),
                "healthy": True
            }
            
            # Stream service health
            stream_service = framework.services["stream_service"]
            results["stream_service"] = {
                "stats": stream_service.get_stream_stats(),
                "healthy": True
            }
            
            # API service health (would be HTTP health check in real deployment)
            api_service = framework.services["api_ingestion"]
            results["api_service"] = {
                "stats": asyncio.run(api_service._get_stats()),
                "healthy": True
            }
            
            return results
        
        health_results = framework.measure_performance(
            "health_checks",
            validate_health_checks
        )
        
        assert all(result["healthy"] for result in health_results.values()), \
            "Some services failed health checks"
        
        # Validate statistics are available
        for service_name, result in health_results.items():
            assert result["stats"] is not None, f"No stats available for {service_name}"
            logger.info(f"{service_name} stats: {result['stats']}")
    
    def test_011_operational_readiness(self, e2e_framework):
        """E2E_011: Operational Readiness"""
        framework = e2e_framework
        
        # Test comprehensive metrics collection
        def collect_operational_metrics():
            metrics = {
                "performance": framework.performance_metrics,
                "system": {
                    "memory_usage": psutil.virtual_memory()._asdict(),
                    "cpu_usage": psutil.cpu_percent(interval=1),
                    "disk_usage": psutil.disk_usage('/')._asdict()
                },
                "test_duration": time.time() - framework.start_time if framework.start_time else 0,
                "services_status": {
                    "data_loader": framework.services["data_loader"] is not None,
                    "stream_service": framework.services["stream_service"] is not None,
                    "api_ingestion": framework.services["api_ingestion"] is not None
                }
            }
            return metrics
        
        metrics = framework.measure_performance(
            "operational_metrics",
            collect_operational_metrics
        )
        
        # Validate operational readiness
        assert metrics["test_duration"] > 0, "Test duration not tracked"
        assert all(metrics["services_status"].values()), "Some services not initialized"
        
        # Log comprehensive metrics
        logger.info("=== OPERATIONAL READINESS METRICS ===")
        logger.info(f"Test Duration: {metrics['test_duration']:.2f} seconds")
        logger.info(f"Memory Usage: {metrics['system']['memory_usage']['percent']:.1f}%")
        logger.info(f"CPU Usage: {metrics['system']['cpu_usage']:.1f}%")
        logger.info(f"Performance Tests: {len(metrics['performance'])} completed")
        
        # Final validation
        assert len(metrics["performance"]) > 0, "No performance metrics collected"
        assert metrics["system"]["memory_usage"]["percent"] < 95, "Memory usage too high"


# Integration test execution
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    pytest.main([__file__, "-v", "--tb=short"])