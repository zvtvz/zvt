# -*- coding: utf-8 -*-
"""
TDD Cycle 3: Strategy Framework Test Suite - RED Phase
=====================================================

Comprehensive test suite for crypto trading strategy framework that will drive
the implementation of intelligent, automated trading strategies.

RED Phase Objective: Create failing tests that define the complete strategy architecture
Expected: 15+ failing tests that will guide perfect implementation

Epic 2 Phase 3 Requirements:
- Intelligent strategy framework with 5+ strategy types
- Real-time signal generation with <100ms latency
- Risk-based position sizing and portfolio management
- Strategy performance tracking and optimization
- Multi-strategy portfolio allocation and coordination
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from src.zvt.trading.crypto_trading_engine import CryptoTradingEngine, OrderRequest
from src.zvt.trading.strategies import SignalType


class TestStrategyFrameworkCore:
    """
    TDD Test Suite for Core Strategy Framework Architecture
    Spec: Epic 2 Phase 3.1 - Strategy interface design and lifecycle management
    
    RED Phase Requirements:
    - IStrategy protocol interface definition
    - StrategyBase abstract class with lifecycle management
    - Signal generation interfaces and enums
    - Strategy configuration and parameter management
    """
    
    def test_strategy_protocol_interface_definition(self):
        """
        RED Phase: Test fails because IStrategy protocol doesn't exist
        Spec Requirement: "Core strategy interface with lifecycle methods"
        """
        # MUST fail initially - IStrategy protocol doesn't exist
        try:
            from src.zvt.trading.strategies import IStrategy
            
            # Strategy protocol should define core interface
            assert hasattr(IStrategy, 'generate_signal')
            assert hasattr(IStrategy, 'update_position_size')
            assert hasattr(IStrategy, 'get_performance_metrics')
            assert hasattr(IStrategy, 'start')
            assert hasattr(IStrategy, 'stop')
            assert hasattr(IStrategy, 'configure')
            
        except ImportError:
            pytest.fail("IStrategy protocol interface not implemented")
    
    def test_strategy_base_class_lifecycle(self):
        """
        RED Phase: Test fails because StrategyBase class doesn't exist
        Spec Requirement: "Abstract base class with strategy lifecycle management"
        """
        try:
            from src.zvt.trading.strategies import StrategyBase
            
            # Create instance (should work as abstract base)
            strategy = StrategyBase(
                strategy_id="test_strategy_001",
                name="Test Strategy",
                description="Test strategy for TDD validation"
            )
            
            # Lifecycle management
            assert not strategy.is_running
            strategy.start()
            assert strategy.is_running
            strategy.stop()
            assert not strategy.is_running
            
            # Configuration management
            config = {"param1": 0.5, "param2": 100}
            strategy.configure(config)
            assert strategy.get_configuration() == config
            
            # Performance tracking
            metrics = strategy.get_performance_metrics()
            assert isinstance(metrics, dict)
            assert "total_signals" in metrics
            assert "win_rate" in metrics
            assert "sharpe_ratio" in metrics
            
        except ImportError:
            pytest.fail("StrategyBase class not implemented")
    
    def test_signal_generation_interface(self):
        """
        RED Phase: Test fails because signal generation interface doesn't exist
        Spec Requirement: "Real-time signal generation with standardized output"
        """
        try:
            from src.zvt.trading.strategies import ISignalGenerator, Signal, SignalType
            
            # Signal types enumeration
            assert SignalType.BUY in SignalType
            assert SignalType.SELL in SignalType
            assert SignalType.HOLD in SignalType
            
            # Signal data structure
            signal = Signal(
                symbol="BTC/USDT",
                signal_type=SignalType.BUY,
                strength=0.75,  # Signal confidence 0-1
                timestamp=datetime.now(),
                metadata={"indicator": "RSI", "value": 30.5}
            )
            
            assert signal.symbol == "BTC/USDT"
            assert signal.signal_type == SignalType.BUY
            assert signal.strength == 0.75
            assert isinstance(signal.timestamp, datetime)
            
        except ImportError:
            pytest.fail("Signal generation interface not implemented")
    
    def test_position_sizing_interface(self):
        """
        RED Phase: Test fails because position sizing interface doesn't exist
        Spec Requirement: "Risk-based position sizing with configurable parameters"
        """
        try:
            from src.zvt.trading.strategies import IPositionSizer, PositionSize
            
            # Position sizing calculation
            position_size = PositionSize(
                symbol="ETH/USDT",
                suggested_quantity=Decimal("5.0"),
                max_risk_amount=Decimal("1000.0"),
                confidence_level=0.8,
                risk_percentage=0.02,  # 2% portfolio risk
                metadata={"volatility": 0.25, "correlation": 0.6}
            )
            
            assert position_size.symbol == "ETH/USDT"
            assert position_size.suggested_quantity == Decimal("5.0")
            assert position_size.max_risk_amount == Decimal("1000.0")
            assert position_size.confidence_level == 0.8
            
        except ImportError:
            pytest.fail("Position sizing interface not implemented")
    
    def test_strategy_configuration_system(self):
        """
        RED Phase: Test fails because strategy configuration system doesn't exist
        Spec Requirement: "Dynamic strategy parameter configuration and validation"
        """
        try:
            from src.zvt.trading.strategies import StrategyConfig, ParameterType
            
            # Strategy configuration with typed parameters
            config = StrategyConfig(
                strategy_type="momentum",
                parameters={
                    "lookback_period": {"value": 14, "type": ParameterType.INTEGER, "min": 5, "max": 50},
                    "rsi_threshold": {"value": 30.0, "type": ParameterType.FLOAT, "min": 10.0, "max": 90.0},
                    "risk_limit": {"value": 0.02, "type": ParameterType.PERCENTAGE, "min": 0.01, "max": 0.05},
                    "enabled": {"value": True, "type": ParameterType.BOOLEAN}
                }
            )
            
            # Parameter validation
            assert config.validate_parameters()
            assert config.get_parameter("lookback_period") == 14
            assert config.get_parameter("rsi_threshold") == 30.0
            
            # Invalid parameter should fail validation
            config.set_parameter("rsi_threshold", 150.0)  # Outside valid range
            assert not config.validate_parameters()
            
        except ImportError:
            pytest.fail("Strategy configuration system not implemented")
    
    def test_strategy_performance_metrics(self):
        """
        RED Phase: Test fails because strategy performance tracking doesn't exist
        Spec Requirement: "Comprehensive strategy performance metrics and analytics"
        """
        try:
            from src.zvt.trading.strategies import StrategyMetrics
            
            # Performance metrics calculation
            metrics = StrategyMetrics(
                strategy_id="momentum_001",
                total_signals=150,
                profitable_signals=98,
                total_return=Decimal("0.15"),  # 15% return
                sharpe_ratio=Decimal("1.8"),
                max_drawdown=Decimal("0.08"),  # 8% max drawdown
                win_rate=Decimal("0.653"),  # 65.3% win rate
                avg_holding_period=timedelta(hours=4, minutes=30),
                last_updated=datetime.now()
            )
            
            assert metrics.strategy_id == "momentum_001"
            assert metrics.total_signals == 150
            assert metrics.win_rate == Decimal("0.653")
            assert metrics.sharpe_ratio == Decimal("1.8")
            
            # Performance analysis methods
            assert metrics.is_performing_well()  # Based on win rate and Sharpe ratio
            assert metrics.get_risk_adjusted_return() > 0
            
        except ImportError:
            pytest.fail("Strategy performance metrics not implemented")


class TestStrategyTypes:
    """
    TDD Test Suite for Specific Trading Strategy Types
    Spec: Epic 2 Phase 3.2 - Five core trading strategy implementations
    
    RED Phase Requirements:
    - MomentumStrategy with RSI and MACD indicators
    - MeanReversionStrategy with Bollinger Bands
    - ArbitrageStrategy with cross-exchange monitoring
    - TrendFollowingStrategy with moving averages
    - PairTradingStrategy with correlation analysis
    """
    
    def test_momentum_strategy_interface(self):
        """
        RED Phase: Test fails because MomentumStrategy doesn't exist
        Spec Requirement: "Momentum-based trading with RSI/MACD indicators"
        """
        try:
            from src.zvt.trading.strategies import MomentumStrategy
            
            # Create momentum strategy
            strategy = MomentumStrategy(
                strategy_id="momentum_btc_001",
                symbol="BTC/USDT",
                rsi_period=14,
                rsi_oversold=30,
                rsi_overbought=70,
                macd_fast=12,
                macd_slow=26,
                macd_signal=9
            )
            
            # Strategy should generate signals based on momentum indicators
            mock_price_data = [
                {"timestamp": datetime.now() - timedelta(minutes=i), "close": 45000 + i * 100}
                for i in range(30)
            ]
            
            signal = strategy.generate_signal(mock_price_data)
            assert signal.symbol == "BTC/USDT"
            assert signal.signal_type in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
            assert 0 <= signal.strength <= 1
            
            # Momentum-specific indicators
            rsi_value = strategy.calculate_rsi(mock_price_data)
            assert 0 <= rsi_value <= 100
            
            macd_line, signal_line, histogram = strategy.calculate_macd(mock_price_data)
            assert isinstance(macd_line, float)
            assert isinstance(signal_line, float)
            
        except ImportError:
            pytest.fail("MomentumStrategy not implemented")
    
    def test_mean_reversion_strategy_interface(self):
        """
        RED Phase: Test fails because MeanReversionStrategy doesn't exist
        Spec Requirement: "Statistical mean reversion with Bollinger Bands"
        """
        try:
            from src.zvt.trading.strategies import MeanReversionStrategy
            
            # Create mean reversion strategy
            strategy = MeanReversionStrategy(
                strategy_id="mean_reversion_eth_001",
                symbol="ETH/USDT",
                bollinger_period=20,
                bollinger_std_dev=2.0,
                mean_reversion_threshold=0.8,
                exit_threshold=0.2
            )
            
            # Mock price data with volatility
            mock_price_data = [
                {"timestamp": datetime.now() - timedelta(minutes=i), "close": 3000 + (i % 10 - 5) * 50}
                for i in range(25)
            ]
            
            signal = strategy.generate_signal(mock_price_data)
            assert signal.symbol == "ETH/USDT"
            
            # Mean reversion specific calculations
            upper_band, middle_band, lower_band = strategy.calculate_bollinger_bands(mock_price_data)
            assert upper_band > middle_band > lower_band
            
            z_score = strategy.calculate_z_score(mock_price_data)
            assert isinstance(z_score, float)
            
        except ImportError:
            pytest.fail("MeanReversionStrategy not implemented")
    
    def test_arbitrage_strategy_interface(self):
        """
        RED Phase: Test fails because ArbitrageStrategy doesn't exist
        Spec Requirement: "Cross-exchange arbitrage opportunity detection"
        """
        try:
            from src.zvt.trading.strategies import ArbitrageStrategy
            
            # Create arbitrage strategy
            strategy = ArbitrageStrategy(
                strategy_id="arbitrage_btc_001",
                symbol="BTC/USDT",
                exchanges=["binance", "okx", "bybit"],
                min_profit_threshold=0.005,  # 0.5% minimum profit
                max_execution_time=30,  # 30 seconds
                transaction_cost_rate=0.001  # 0.1% total fees
            )
            
            # Mock exchange price data
            exchange_prices = {
                "binance": {"bid": 44950, "ask": 45000, "timestamp": datetime.now()},
                "okx": {"bid": 45100, "ask": 45150, "timestamp": datetime.now()},
                "bybit": {"bid": 45080, "ask": 45120, "timestamp": datetime.now()}
            }
            
            arbitrage_opportunity = strategy.detect_arbitrage_opportunity(exchange_prices)
            assert arbitrage_opportunity is not None
            assert "buy_exchange" in arbitrage_opportunity
            assert "sell_exchange" in arbitrage_opportunity
            assert "profit_percentage" in arbitrage_opportunity
            
            # Execution plan generation
            execution_plan = strategy.generate_execution_plan(arbitrage_opportunity)
            assert "buy_order" in execution_plan
            assert "sell_order" in execution_plan
            assert "estimated_profit" in execution_plan
            
        except ImportError:
            pytest.fail("ArbitrageStrategy not implemented")
    
    def test_trend_following_strategy_interface(self):
        """
        RED Phase: Test fails because TrendFollowingStrategy doesn't exist
        Spec Requirement: "Trend following with moving average crossovers"
        """
        try:
            from src.zvt.trading.strategies import TrendFollowingStrategy
            
            # Create trend following strategy
            strategy = TrendFollowingStrategy(
                strategy_id="trend_following_ada_001",
                symbol="ADA/USDT",
                short_ma_period=10,
                long_ma_period=30,
                breakout_threshold=0.02,  # 2% breakout
                trend_strength_threshold=0.6
            )
            
            # Mock trending price data
            mock_price_data = [
                {"timestamp": datetime.now() - timedelta(minutes=i), "close": 0.5 + i * 0.01}
                for i in range(35)
            ]
            
            signal = strategy.generate_signal(mock_price_data)
            assert signal.symbol == "ADA/USDT"
            
            # Trend analysis methods
            trend_direction = strategy.determine_trend_direction(mock_price_data)
            assert trend_direction in ["uptrend", "downtrend", "sideways"]
            
            trend_strength = strategy.calculate_trend_strength(mock_price_data)
            assert 0 <= trend_strength <= 1
            
            short_ma = strategy.calculate_moving_average(mock_price_data, 10)
            long_ma = strategy.calculate_moving_average(mock_price_data, 30)
            assert isinstance(short_ma, float)
            assert isinstance(long_ma, float)
            
        except ImportError:
            pytest.fail("TrendFollowingStrategy not implemented")
    
    def test_pair_trading_strategy_interface(self):
        """
        RED Phase: Test fails because PairTradingStrategy doesn't exist
        Spec Requirement: "Statistical arbitrage with correlation analysis"
        """
        try:
            from src.zvt.trading.strategies import PairTradingStrategy
            
            # Create pair trading strategy
            strategy = PairTradingStrategy(
                strategy_id="pair_trading_btc_eth_001",
                primary_symbol="BTC/USDT",
                secondary_symbol="ETH/USDT",
                lookback_period=30,
                correlation_threshold=0.7,
                z_score_entry=2.0,
                z_score_exit=0.5
            )
            
            # Mock correlated price data
            btc_prices = [{"timestamp": datetime.now() - timedelta(minutes=i), "close": 45000 + i * 100} for i in range(35)]
            eth_prices = [{"timestamp": datetime.now() - timedelta(minutes=i), "close": 3000 + i * 6} for i in range(35)]
            
            pair_data = {"BTC/USDT": btc_prices, "ETH/USDT": eth_prices}
            
            signal = strategy.generate_signal(pair_data)
            assert signal.symbol in ["BTC/USDT", "ETH/USDT"]
            
            # Pair trading specific analysis
            correlation = strategy.calculate_correlation(btc_prices, eth_prices)
            assert -1 <= correlation <= 1
            
            spread = strategy.calculate_spread(btc_prices, eth_prices)
            z_score = strategy.calculate_spread_z_score(spread)
            assert isinstance(z_score, float)
            
            # Position sizing for pairs
            pair_positions = strategy.calculate_pair_positions(z_score, portfolio_value=100000)
            assert "primary_position" in pair_positions
            assert "secondary_position" in pair_positions
            
        except ImportError:
            pytest.fail("PairTradingStrategy not implemented")


class TestStrategyManager:
    """
    TDD Test Suite for Strategy Management and Orchestration
    Spec: Epic 2 Phase 3.3 - Multi-strategy coordination and portfolio integration
    
    RED Phase Requirements:
    - StrategyManager for multi-strategy orchestration
    - Strategy portfolio allocation and risk management
    - Real-time strategy monitoring and performance tracking
    - Integration with existing CryptoTradingEngine architecture
    """
    
    def test_strategy_manager_initialization(self):
        """
        RED Phase: Test fails because StrategyManager doesn't exist
        Spec Requirement: "Central strategy orchestration and management system"
        """
        try:
            from src.zvt.trading.strategies import StrategyManager
            
            # Initialize strategy manager with trading engine
            engine = CryptoTradingEngine()
            strategy_manager = StrategyManager(trading_engine=engine)
            
            assert strategy_manager.trading_engine is engine
            assert len(strategy_manager.active_strategies) == 0
            assert not strategy_manager.is_running
            
            # Strategy registration
            strategy_config = {
                "strategy_type": "momentum",
                "symbol": "BTC/USDT",
                "allocation": 0.2,  # 20% of portfolio
                "parameters": {"rsi_period": 14, "rsi_oversold": 30}
            }
            
            strategy_id = strategy_manager.register_strategy(strategy_config)
            assert strategy_id is not None
            assert len(strategy_manager.active_strategies) == 1
            
        except ImportError:
            pytest.fail("StrategyManager not implemented")
    
    def test_multi_strategy_portfolio_allocation(self):
        """
        RED Phase: Test fails because multi-strategy allocation doesn't exist
        Spec Requirement: "Dynamic portfolio allocation across multiple strategies"
        """
        try:
            from src.zvt.trading.strategies import StrategyManager, PortfolioAllocation
            
            engine = CryptoTradingEngine()
            strategy_manager = StrategyManager(trading_engine=engine)
            
            # Register multiple strategies with different allocations
            strategies = [
                {"type": "momentum", "symbol": "BTC/USDT", "allocation": 0.4},
                {"type": "mean_reversion", "symbol": "ETH/USDT", "allocation": 0.3},
                {"type": "arbitrage", "symbol": "ADA/USDT", "allocation": 0.2},
                {"type": "trend_following", "symbol": "DOT/USDT", "allocation": 0.1}
            ]
            
            for strategy_config in strategies:
                strategy_manager.register_strategy(strategy_config)
            
            # Portfolio allocation management
            total_allocation = strategy_manager.get_total_allocation()
            assert total_allocation == 1.0  # 100% allocated
            
            allocation_breakdown = strategy_manager.get_allocation_breakdown()
            assert len(allocation_breakdown) == 4
            assert allocation_breakdown["momentum"]["allocation"] == 0.4
            
            # Rebalance allocations
            new_allocations = {"momentum": 0.5, "mean_reversion": 0.3, "arbitrage": 0.2}
            strategy_manager.update_allocations(new_allocations)
            
            updated_breakdown = strategy_manager.get_allocation_breakdown()
            assert updated_breakdown["momentum"]["allocation"] == 0.5
            
        except ImportError:
            pytest.fail("Multi-strategy portfolio allocation not implemented")
    
    def test_strategy_performance_monitoring(self):
        """
        RED Phase: Test fails because strategy performance monitoring doesn't exist
        Spec Requirement: "Real-time strategy performance tracking and analysis"
        """
        try:
            from src.zvt.trading.strategies import StrategyManager, PerformanceMonitor
            
            engine = CryptoTradingEngine()
            strategy_manager = StrategyManager(trading_engine=engine)
            
            # Register strategy and start monitoring
            strategy_config = {"type": "momentum", "symbol": "BTC/USDT", "allocation": 0.5}
            strategy_id = strategy_manager.register_strategy(strategy_config)
            
            strategy_manager.start_monitoring()
            assert strategy_manager.is_monitoring
            
            # Performance metrics collection
            performance_summary = strategy_manager.get_performance_summary()
            assert "total_strategies" in performance_summary
            assert "active_strategies" in performance_summary
            assert "total_signals_generated" in performance_summary
            assert "portfolio_return" in performance_summary
            
            # Individual strategy performance
            strategy_performance = strategy_manager.get_strategy_performance(strategy_id)
            assert "strategy_id" in strategy_performance
            assert "total_signals" in strategy_performance
            assert "win_rate" in strategy_performance
            assert "sharpe_ratio" in strategy_performance
            
            # Performance comparison
            ranking = strategy_manager.rank_strategies_by_performance()
            assert isinstance(ranking, list)
            
        except ImportError:
            pytest.fail("Strategy performance monitoring not implemented")
    
    def test_strategy_integration_with_trading_engine(self):
        """
        RED Phase: Test fails because strategy integration doesn't exist
        Spec Requirement: "Seamless integration with existing SOLID architecture"
        """
        try:
            from src.zvt.trading.strategies import StrategyManager
            
            engine = CryptoTradingEngine()
            strategy_manager = StrategyManager(trading_engine=engine)
            
            # Verify integration with existing services
            assert hasattr(strategy_manager, 'trading_service')
            assert hasattr(strategy_manager, 'portfolio_service') 
            assert hasattr(strategy_manager, 'analytics_service')
            assert hasattr(strategy_manager, 'risk_manager')
            
            # Strategy execution through existing infrastructure
            strategy_config = {"type": "momentum", "symbol": "BTC/USDT", "allocation": 0.3}
            strategy_id = strategy_manager.register_strategy(strategy_config)
            
            # Mock signal generation and order execution
            with patch.object(strategy_manager, '_generate_strategy_signal') as mock_signal:
                from src.zvt.trading.strategies import Signal, SignalType
                mock_signal.return_value = Signal(
                    symbol="BTC/USDT",
                    signal_type=SignalType.BUY,
                    strength=0.8,
                    timestamp=datetime.now()
                )
                
                # Execute strategy through trading engine
                execution_result = strategy_manager.execute_strategy_signal(strategy_id)
                assert execution_result is not None
                assert "order_result" in execution_result
                
        except ImportError:
            pytest.fail("Strategy integration with trading engine not implemented")


class TestStrategyOptimization:
    """
    TDD Test Suite for Strategy Optimization and Parameter Tuning
    Spec: Epic 2 Phase 3.4 - Strategy optimization and automated parameter tuning
    
    RED Phase Requirements:
    - Parameter optimization algorithms
    - Backtesting integration for strategy validation
    - Performance-based parameter adjustment
    - Strategy ensemble methods
    """
    
    def test_strategy_parameter_optimization(self):
        """
        RED Phase: Test fails because strategy optimization doesn't exist
        Spec Requirement: "Automated parameter optimization using historical performance"
        """
        try:
            from src.zvt.trading.strategies import StrategyOptimizer, OptimizationResult
            
            # Parameter space definition for optimization
            parameter_space = {
                "rsi_period": {"min": 10, "max": 20, "step": 2},
                "rsi_oversold": {"min": 20, "max": 40, "step": 5},
                "rsi_overbought": {"min": 60, "max": 80, "step": 5}
            }
            
            optimizer = StrategyOptimizer(
                strategy_type="momentum",
                symbol="BTC/USDT",
                parameter_space=parameter_space,
                optimization_metric="sharpe_ratio"
            )
            
            # Mock historical data for optimization
            historical_data = [
                {"timestamp": datetime.now() - timedelta(days=i), "close": 45000 + i * 100}
                for i in range(100)
            ]
            
            optimization_result = optimizer.optimize(
                historical_data=historical_data,
                optimization_period=timedelta(days=30),
                validation_period=timedelta(days=10)
            )
            
            assert isinstance(optimization_result, OptimizationResult)
            assert "best_parameters" in optimization_result
            assert "best_performance" in optimization_result
            assert "optimization_history" in optimization_result
            
        except ImportError:
            pytest.fail("Strategy parameter optimization not implemented")
    
    def test_strategy_ensemble_methods(self):
        """
        RED Phase: Test fails because strategy ensemble doesn't exist
        Spec Requirement: "Strategy ensemble combining multiple approaches"
        """
        try:
            from src.zvt.trading.strategies import StrategyEnsemble, EnsembleMethod
            
            # Create ensemble combining multiple strategies
            ensemble = StrategyEnsemble(
                ensemble_id="btc_ensemble_001",
                symbol="BTC/USDT",
                member_strategies=[
                    {"type": "momentum", "weight": 0.4},
                    {"type": "mean_reversion", "weight": 0.3},
                    {"type": "trend_following", "weight": 0.3}
                ],
                ensemble_method=EnsembleMethod.WEIGHTED_AVERAGE,
                confidence_threshold=0.6
            )
            
            # Ensemble signal generation
            member_signals = [
                {"strategy": "momentum", "signal": SignalType.BUY, "strength": 0.8},
                {"strategy": "mean_reversion", "signal": SignalType.HOLD, "strength": 0.4},
                {"strategy": "trend_following", "signal": SignalType.BUY, "strength": 0.7}
            ]
            
            ensemble_signal = ensemble.generate_ensemble_signal(member_signals)
            assert ensemble_signal.signal_type in [SignalType.BUY, SignalType.SELL, SignalType.HOLD]
            assert 0 <= ensemble_signal.strength <= 1
            
            # Ensemble performance tracking
            ensemble_metrics = ensemble.get_ensemble_performance()
            assert "member_contributions" in ensemble_metrics
            assert "ensemble_sharpe_ratio" in ensemble_metrics
            
        except ImportError:
            pytest.fail("Strategy ensemble methods not implemented")


# RED Phase: These tests will fail until strategy framework is implemented
# Target: 15+ failing tests to guide implementation