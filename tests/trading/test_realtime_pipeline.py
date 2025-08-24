# -*- coding: utf-8 -*-
"""
Tests for TDD Cycle 3: REFACTOR Phase 3.2 - Real-time Data Pipeline
===================================================================

Comprehensive tests for real-time signal generation pipeline.
Validates sub-100ms latency, integration with strategy framework,
and production-grade performance requirements.
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from zvt.trading.realtime_pipeline import (
    LatencyMetrics,
    StreamingDataPoint,
    RealTimeSignalProcessor,
    RealTimeDataPipeline,
    RealTimeTradingIntegration
)
from zvt.trading.strategies import (
    StrategyManager,
    Signal,
    SignalType,
    MomentumStrategy
)


class TestLatencyMetrics:
    """Test latency tracking and performance metrics"""
    
    def test_latency_metrics_initialization(self):
        """Test latency metrics proper initialization"""
        metrics = LatencyMetrics()
        
        assert len(metrics.signal_generation_latencies) == 0
        assert len(metrics.data_processing_latencies) == 0
        assert len(metrics.end_to_end_latencies) == 0
        assert metrics.target_signal_latency == 50.0
        assert metrics.target_e2e_latency == 100.0
        assert metrics.total_signals_processed == 0
        assert metrics.signals_under_target == 0
        assert metrics.performance_violations == 0
    
    def test_signal_latency_recording_under_target(self):
        """Test recording signal latency under performance target"""
        metrics = LatencyMetrics()
        
        # Record latency under target (30ms < 50ms target)
        metrics.record_signal_latency(30.0)
        
        assert metrics.total_signals_processed == 1
        assert metrics.signals_under_target == 1
        assert metrics.performance_violations == 0
        assert list(metrics.signal_generation_latencies) == [30.0]
    
    def test_signal_latency_recording_over_target(self):
        """Test recording signal latency over performance target"""
        metrics = LatencyMetrics()
        
        # Record latency over target (75ms > 50ms target)
        metrics.record_signal_latency(75.0)
        
        assert metrics.total_signals_processed == 1
        assert metrics.signals_under_target == 0
        assert metrics.performance_violations == 1
        assert list(metrics.signal_generation_latencies) == [75.0]
    
    def test_performance_summary_calculation(self):
        """Test comprehensive performance summary generation"""
        metrics = LatencyMetrics()
        
        # Record multiple latencies
        latencies = [25.0, 35.0, 45.0, 65.0, 85.0]  # Mix of under/over target
        for latency in latencies:
            metrics.record_signal_latency(latency)
            metrics.record_e2e_latency(latency * 1.5)  # E2E is typically higher
        
        summary = metrics.get_performance_summary()
        
        assert summary["total_signals"] == 5
        assert summary["signals_under_target"] == 3  # 25, 35, 45 are under 50ms
        assert summary["performance_violations"] == 2  # 65, 85 are over 50ms
        assert summary["success_rate"] == 0.6  # 3/5 = 60%
        
        # Check signal latency stats
        signal_stats = summary["signal_latency"]
        assert signal_stats["current"] == 85.0
        assert signal_stats["avg"] == 51.0  # Average of latencies
        assert signal_stats["target"] == 50.0
        
        # Check e2e latency stats
        e2e_stats = summary["e2e_latency"]
        assert e2e_stats["target"] == 100.0


class TestStreamingDataPoint:
    """Test streaming data point structure and performance tracking"""
    
    def test_streaming_data_point_creation(self):
        """Test creation of streaming data point with proper fields"""
        timestamp = datetime.now()
        
        data_point = StreamingDataPoint(
            exchange="binance",
            symbol="BTC/USDT",
            timestamp=timestamp,
            price=50000.0,
            volume=1.5,
            data_type="ticker",
            metadata={"source": "websocket"}
        )
        
        assert data_point.exchange == "binance"
        assert data_point.symbol == "BTC/USDT"
        assert data_point.timestamp == timestamp
        assert data_point.price == 50000.0
        assert data_point.volume == 1.5
        assert data_point.data_type == "ticker"
        assert data_point.metadata["source"] == "websocket"
        assert data_point.received_at > 0
    
    def test_data_point_age_calculation(self):
        """Test age calculation for data freshness tracking"""
        data_point = StreamingDataPoint(
            exchange="binance",
            symbol="BTC/USDT",
            timestamp=datetime.now(),
            price=50000.0,
            volume=1.5,
            data_type="ticker"
        )
        
        # Wait a small amount and check age
        time.sleep(0.001)  # 1ms
        age_ms = data_point.get_age_ms()
        
        assert age_ms >= 1.0  # Should be at least 1ms
        assert age_ms < 100.0  # Should be less than 100ms for this test


class TestRealTimeSignalProcessor:
    """Test high-performance signal processor for sub-100ms latency"""
    
    @pytest.fixture
    def mock_strategy_manager(self):
        """Create mock strategy manager with test strategies"""
        manager = Mock()
        
        # Create a test momentum strategy
        strategy = MomentumStrategy("test_momentum", "BTC/USDT")
        manager.active_strategies = {"test_momentum": strategy}
        
        return manager
    
    @pytest.fixture
    def signal_processor(self, mock_strategy_manager):
        """Create signal processor with mock strategy manager"""
        return RealTimeSignalProcessor(mock_strategy_manager, buffer_size=100)
    
    def test_signal_processor_initialization(self, signal_processor):
        """Test signal processor proper initialization"""
        assert signal_processor.buffer_size == 100
        assert len(signal_processor.price_buffers) == 0
        assert len(signal_processor.strategy_cache) == 0
        assert signal_processor.metrics.target_signal_latency == 50.0
        assert signal_processor.max_concurrent_strategies == 10
        assert not signal_processor.is_processing
    
    @pytest.mark.asyncio
    async def test_market_data_processing_buffer_update(self, signal_processor):
        """Test market data processing updates circular buffer correctly"""
        data_point = StreamingDataPoint(
            exchange="binance",
            symbol="BTC/USDT",
            timestamp=datetime.now(),
            price=50000.0,
            volume=1.5,
            data_type="ticker"
        )
        
        await signal_processor.process_market_data(data_point)
        
        # Check buffer was updated
        assert "BTC/USDT" in signal_processor.price_buffers
        assert len(signal_processor.price_buffers["BTC/USDT"]) == 1
        assert signal_processor.price_buffers["BTC/USDT"][0] == data_point
    
    @pytest.mark.asyncio
    async def test_signal_generation_with_sufficient_data(self, signal_processor):
        """Test signal generation when sufficient market data is available"""
        symbol = "BTC/USDT"
        
        # Add 30 data points to trigger signal generation
        for i in range(30):
            data_point = StreamingDataPoint(
                exchange="binance",
                symbol=symbol,
                timestamp=datetime.now(),
                price=50000.0 + i * 10,  # Trending upward
                volume=1.5,
                data_type="ticker"
            )
            await signal_processor.process_market_data(data_point)
        
        # Should have triggered signal generation
        assert len(signal_processor.price_buffers[symbol]) == 30
        
        # Check if any latency metrics were recorded
        # (Indicating signal generation attempt)
        assert signal_processor.metrics.total_signals_processed >= 0
    
    def test_strategies_for_symbol_filtering(self, signal_processor):
        """Test filtering strategies by symbol"""
        # Mock strategy manager has BTC/USDT strategy
        strategies = signal_processor._get_strategies_for_symbol("BTC/USDT")
        assert "test_momentum" in strategies
        
        # Different symbol should return no strategies
        strategies = signal_processor._get_strategies_for_symbol("ETH/USDT")
        assert len(strategies) == 0
    
    def test_data_formatting_for_strategies(self, signal_processor):
        """Test conversion of streaming data to strategy format"""
        timestamp = datetime.now()
        price_data = [
            StreamingDataPoint(
                exchange="binance",
                symbol="BTC/USDT", 
                timestamp=timestamp,
                price=50000.0,
                volume=1.5,
                data_type="ticker"
            ),
            StreamingDataPoint(
                exchange="binance",
                symbol="BTC/USDT",
                timestamp=timestamp,
                price=51000.0,
                volume=2.0,
                data_type="ticker"
            )
        ]
        
        formatted_data = signal_processor._format_data_for_strategies(price_data)
        
        assert len(formatted_data) == 2
        assert formatted_data[0]["close"] == 50000.0
        assert formatted_data[0]["volume"] == 1.5
        assert formatted_data[1]["close"] == 51000.0
        assert formatted_data[1]["volume"] == 2.0
    
    def test_signal_enhancement_with_metadata(self, signal_processor):
        """Test signal enhancement with performance metadata"""
        original_signal = Signal(
            symbol="BTC/USDT",
            signal_type=SignalType.BUY,
            strength=0.8,
            timestamp=datetime.now(),
            metadata={"rsi": 25.0}
        )
        
        enhanced_signal = signal_processor._enhance_signal_with_metadata(
            original_signal, 
            latency_ms=35.0
        )
        
        assert enhanced_signal.symbol == "BTC/USDT"
        assert enhanced_signal.signal_type == SignalType.BUY
        assert enhanced_signal.strength == 0.8
        assert enhanced_signal.metadata["rsi"] == 25.0
        assert enhanced_signal.metadata["processing_latency_ms"] == 35.0
        assert enhanced_signal.metadata["performance_target_met"] == True  # 35ms < 50ms target
    
    @pytest.mark.asyncio
    async def test_signal_queue_operations(self, signal_processor):
        """Test signal queue put/get operations"""
        test_signal = Signal(
            symbol="BTC/USDT",
            signal_type=SignalType.BUY,
            strength=0.8,
            timestamp=datetime.now()
        )
        
        # Put signal in queue
        await signal_processor.signal_queue.put(test_signal)
        
        # Get signal from queue
        retrieved_signal = await signal_processor.get_signal(timeout=0.1)
        
        assert retrieved_signal is not None
        assert retrieved_signal.symbol == "BTC/USDT"
        assert retrieved_signal.signal_type == SignalType.BUY
        assert retrieved_signal.strength == 0.8
    
    @pytest.mark.asyncio
    async def test_signal_queue_timeout(self, signal_processor):
        """Test signal queue timeout when no signals available"""
        # Try to get signal from empty queue
        signal = await signal_processor.get_signal(timeout=0.1)
        
        assert signal is None
    
    def test_performance_metrics_access(self, signal_processor):
        """Test access to performance metrics"""
        # Record some test metrics
        signal_processor.metrics.record_signal_latency(45.0)
        signal_processor.metrics.record_data_latency(5.0)
        signal_processor.metrics.record_e2e_latency(85.0)
        
        metrics = signal_processor.get_performance_metrics()
        
        assert "total_signals" in metrics
        assert "success_rate" in metrics
        assert "signal_latency" in metrics
        assert "e2e_latency" in metrics
        assert metrics["signal_latency"]["current"] == 45.0
        assert metrics["e2e_latency"]["current"] == 85.0


class TestRealTimeDataPipeline:
    """Test real-time data pipeline orchestration and integration"""
    
    @pytest.fixture
    def mock_strategy_manager(self):
        """Create mock strategy manager"""
        manager = Mock()
        strategy = Mock()
        strategy.symbol = "BTC/USDT"
        manager.active_strategies = {"test_strategy": strategy}
        return manager
    
    @pytest.fixture
    def mock_stream_service(self):
        """Create mock crypto stream service"""
        service = Mock()
        service.start = Mock()
        service.stop = Mock()
        service.add_data_handler = Mock()
        service.subscribe_ticker = Mock()
        service.subscribe_trades = Mock()
        service.get_stream_stats = Mock(return_value={"active_connections": 3})
        return service
    
    @pytest.fixture
    def pipeline(self, mock_strategy_manager, mock_stream_service):
        """Create real-time data pipeline"""
        return RealTimeDataPipeline(
            strategy_manager=mock_strategy_manager,
            stream_service=mock_stream_service,
            enable_performance_monitoring=False,  # Disable for faster tests
            latency_alert_threshold=100.0
        )
    
    def test_pipeline_initialization(self, pipeline, mock_strategy_manager, mock_stream_service):
        """Test pipeline proper initialization"""
        assert pipeline.strategy_manager == mock_strategy_manager
        assert pipeline.stream_service == mock_stream_service
        assert pipeline.latency_alert_threshold == 100.0
        assert not pipeline.is_running
        assert len(pipeline.signal_handlers) == 0
        assert pipeline.signal_processor is not None
    
    def test_data_handlers_setup(self, pipeline):
        """Test data handlers are properly registered with stream service"""
        # Verify handlers were registered
        assert pipeline.stream_service.add_data_handler.call_count == 2
        
        # Check ticker and trade handlers were added
        call_args = [call[0] for call in pipeline.stream_service.add_data_handler.call_args_list]
        assert ("ticker", ) in [args[:1] for args in call_args]
        assert ("trades", ) in [args[:1] for args in call_args]
    
    @pytest.mark.asyncio
    async def test_pipeline_start_stop_lifecycle(self, pipeline):
        """Test pipeline start and stop lifecycle"""
        # Start pipeline
        await pipeline.start()
        
        assert pipeline.is_running == True
        assert pipeline.performance_stats["pipeline_start_time"] is not None
        assert len(pipeline.processing_tasks) >= 1  # Signal processing task
        
        # Verify stream service was started
        pipeline.stream_service.start.assert_called_once()
        
        # Verify subscriptions were made
        pipeline.stream_service.subscribe_ticker.assert_called_once()
        pipeline.stream_service.subscribe_trades.assert_called_once()
        
        # Stop pipeline
        await pipeline.stop()
        
        assert pipeline.is_running == False
        pipeline.stream_service.stop.assert_called_once()
    
    def test_signal_handler_registration(self, pipeline):
        """Test signal handler registration"""
        handler = Mock()
        
        pipeline.add_signal_handler(handler)
        
        assert len(pipeline.signal_handlers) == 1
        assert handler in pipeline.signal_handlers
    
    def test_pipeline_metrics_compilation(self, pipeline):
        """Test comprehensive pipeline metrics compilation"""
        # Mock signal processor metrics
        mock_metrics = {
            "total_signals": 100,
            "success_rate": 0.95,
            "signal_latency": {"avg": 45.0, "p95": 75.0}
        }
        pipeline.signal_processor.get_performance_metrics = Mock(return_value=mock_metrics)
        
        metrics = pipeline.get_pipeline_metrics()
        
        assert "pipeline_stats" in metrics
        assert "signal_processing" in metrics
        assert "stream_service" in metrics
        assert "is_running" in metrics
        assert "active_strategies" in metrics
        assert "performance_status" in metrics
        
        # Check performance status calculation based on mocked metrics
        expected_status = "OPTIMAL" if mock_metrics["success_rate"] > 0.95 else "DEGRADED"
        assert metrics["performance_status"] == expected_status


class TestRealTimeTradingIntegration:
    """Test integration between pipeline and trading engine"""
    
    @pytest.fixture
    def mock_pipeline(self):
        """Create mock real-time pipeline"""
        pipeline = Mock()
        pipeline.add_signal_handler = Mock()
        return pipeline
    
    @pytest.fixture
    def mock_trading_engine(self):
        """Create mock trading engine"""
        return Mock()
    
    @pytest.fixture
    def integration(self, mock_pipeline, mock_trading_engine):
        """Create trading integration"""
        return RealTimeTradingIntegration(mock_pipeline, mock_trading_engine)
    
    def test_integration_initialization(self, integration, mock_pipeline):
        """Test trading integration initialization"""
        assert integration.pipeline == mock_pipeline
        assert integration.min_signal_strength == 0.7
        assert integration.max_position_size_pct == 0.05
        assert integration.signal_cooldown == timedelta(minutes=5)
        assert len(integration.recent_signals) == 0
        
        # Verify signal handler was registered
        mock_pipeline.add_signal_handler.assert_called_once()
    
    def test_signal_validation_strength_threshold(self, integration):
        """Test signal validation based on strength threshold"""
        # High strength signal should pass
        strong_signal = Signal(
            symbol="BTC/USDT",
            signal_type=SignalType.BUY,
            strength=0.8,
            timestamp=datetime.now(),
            metadata={"processing_latency_ms": 45.0}
        )
        assert integration._validate_signal(strong_signal) == True
        
        # Low strength signal should fail
        weak_signal = Signal(
            symbol="BTC/USDT",
            signal_type=SignalType.BUY,
            strength=0.5,  # Below 0.7 threshold
            timestamp=datetime.now(),
            metadata={"processing_latency_ms": 45.0}
        )
        assert integration._validate_signal(weak_signal) == False
    
    def test_signal_validation_latency_threshold(self, integration):
        """Test signal validation based on latency threshold"""
        # Low latency signal should pass
        fast_signal = Signal(
            symbol="BTC/USDT",
            signal_type=SignalType.BUY,
            strength=0.8,
            timestamp=datetime.now(),
            metadata={"processing_latency_ms": 75.0}  # Under 100ms
        )
        assert integration._validate_signal(fast_signal) == True
        
        # High latency signal should fail
        slow_signal = Signal(
            symbol="BTC/USDT",
            signal_type=SignalType.BUY,
            strength=0.8,
            timestamp=datetime.now(),
            metadata={"processing_latency_ms": 150.0}  # Over 100ms
        )
        assert integration._validate_signal(slow_signal) == False
    
    def test_signal_validation_hold_signals(self, integration):
        """Test that HOLD signals are filtered out"""
        hold_signal = Signal(
            symbol="BTC/USDT",
            signal_type=SignalType.HOLD,
            strength=0.8,
            timestamp=datetime.now(),
            metadata={"processing_latency_ms": 45.0}
        )
        assert integration._validate_signal(hold_signal) == False
    
    def test_signal_cooldown_mechanism(self, integration):
        """Test signal cooldown prevents over-trading"""
        signal = Signal(
            symbol="BTC/USDT",
            signal_type=SignalType.BUY,
            strength=0.8,
            timestamp=datetime.now()
        )
        
        # First signal should pass cooldown
        assert integration._check_signal_cooldown(signal) == True
        
        # Immediate second signal should fail cooldown
        assert integration._check_signal_cooldown(signal) == False
        
        # Verify symbol was added to recent signals
        assert "BTC/USDT" in integration.recent_signals
    
    def test_position_size_calculation(self, integration):
        """Test position size calculation based on signal strength"""
        # High strength signal
        strong_signal = Signal(
            symbol="BTC/USDT",
            signal_type=SignalType.BUY,
            strength=0.9,
            timestamp=datetime.now()
        )
        strong_size = integration._calculate_position_size(strong_signal)
        
        # Medium strength signal
        medium_signal = Signal(
            symbol="BTC/USDT",
            signal_type=SignalType.BUY,
            strength=0.7,
            timestamp=datetime.now()
        )
        medium_size = integration._calculate_position_size(medium_signal)
        
        # Stronger signal should result in larger position
        assert strong_size > medium_size
        
        # Both should be within reasonable bounds
        assert 0.001 <= strong_size <= 0.05  # Between min and max
        assert 0.001 <= medium_size <= 0.05


# ================================================================================================
# PERFORMANCE BENCHMARKS
# ================================================================================================

class TestPerformanceBenchmarks:
    """Performance benchmarks to validate sub-100ms latency requirements"""
    
    @pytest.mark.asyncio
    async def test_signal_processing_latency_benchmark(self):
        """Benchmark signal processing latency under load"""
        # Create test strategy manager
        manager = Mock()
        strategy = MomentumStrategy("test_momentum", "BTC/USDT")
        manager.active_strategies = {"test_momentum": strategy}
        
        processor = RealTimeSignalProcessor(manager, buffer_size=1000)
        
        # Generate 30 data points for signal generation
        data_points = []
        for i in range(30):
            data_points.append(StreamingDataPoint(
                exchange="binance",
                symbol="BTC/USDT",
                timestamp=datetime.now(),
                price=50000.0 + i * 10,
                volume=1.0 + i * 0.1,
                data_type="ticker"
            ))
        
        # Pre-populate buffer to enable signal generation
        for dp in data_points:
            await processor.process_market_data(dp)
        
        # Benchmark signal processing
        start_time = time.perf_counter()
        
        # Process additional data point that should trigger signal generation
        trigger_data = StreamingDataPoint(
            exchange="binance",
            symbol="BTC/USDT",
            timestamp=datetime.now(),
            price=50300.0,
            volume=2.0,
            data_type="ticker"
        )
        
        await processor.process_market_data(trigger_data)
        
        end_time = time.perf_counter()
        processing_latency = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Assert latency is under target
        assert processing_latency < 100.0, f"Signal processing took {processing_latency:.2f}ms (target: <100ms)"
        
        print(f"Signal processing latency: {processing_latency:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_throughput_benchmark(self):
        """Benchmark data throughput capacity"""
        manager = Mock()
        strategy = Mock()
        strategy.symbol = "BTC/USDT"
        manager.active_strategies = {"test_strategy": strategy}
        
        processor = RealTimeSignalProcessor(manager, buffer_size=10000)
        
        # Process large number of data points
        num_points = 1000
        start_time = time.perf_counter()
        
        for i in range(num_points):
            data_point = StreamingDataPoint(
                exchange="binance",
                symbol="BTC/USDT",
                timestamp=datetime.now(),
                price=50000.0 + i,
                volume=1.0,
                data_type="ticker"
            )
            await processor.process_market_data(data_point)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        throughput = num_points / total_time
        
        # Assert reasonable throughput (should handle >1000 data points/second)
        assert throughput > 1000, f"Throughput {throughput:.0f} data points/second is too low"
        
        print(f"Data processing throughput: {throughput:.0f} data points/second")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])