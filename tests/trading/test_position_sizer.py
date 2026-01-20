# -*- coding: utf-8 -*-
"""
TDD Cycle 3: REFACTOR Phase 3.3.2 - Dynamic Position Sizing Tests
================================================================

Comprehensive test suite for institutional-grade position sizing algorithms.
Following specifications-driven TDD methodology with performance requirements.

RED PHASE: These tests should FAIL initially to drive implementation.

Business Requirements:
- Kelly Criterion optimal position sizing for maximum long-term growth
- Volatility-adjusted sizing for consistent risk exposure
- Risk budget allocation across multiple strategies
- Real-time position sizing with <50ms response time
- Integration with existing VaR engine and portfolio management
- Position limits and concentration risk controls
"""

import pytest
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch
from typing import Dict, List

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

# These imports will initially fail - driving the implementation
from zvt.trading.position_sizer import (
    PositionSizer,
    PositionSizingResult,
    StrategyStats,
    PositionLimits,
    RiskBudgetConfig,
    OptimizedPositionSizer,
    AdvancedPositionSizer,
    RealTimePositionSizer
)
from zvt.trading.risk_engine import VaRCalculator, Portfolio, Position
from zvt.trading.strategies import TradingSignal, StrategyManager


class TestKellyCriterionSizing:
    """Test Kelly Criterion optimal position sizing calculations"""
    
    @pytest.fixture
    def strategy_stats_profitable(self):
        """Create profitable strategy statistics for testing"""
        return StrategyStats(
            win_rate=Decimal("0.60"),  # 60% win rate
            avg_win=Decimal("0.025"),  # 2.5% average win
            avg_loss=Decimal("0.015"), # 1.5% average loss
            trade_count=100,
            sharpe_ratio=Decimal("1.8"),
            max_drawdown=Decimal("-0.12")
        )
    
    @pytest.fixture
    def strategy_stats_marginal(self):
        """Create marginally profitable strategy for edge case testing"""
        return StrategyStats(
            win_rate=Decimal("0.52"),  # 52% win rate
            avg_win=Decimal("0.018"),  # 1.8% average win
            avg_loss=Decimal("0.016"), # 1.6% average loss
            trade_count=50,
            sharpe_ratio=Decimal("0.8"),
            max_drawdown=Decimal("-0.20")
        )
    
    @pytest.fixture
    def position_sizer(self):
        """Create position sizer instance"""
        var_calculator = Mock()
        portfolio_manager = Mock()
        return PositionSizer(var_calculator, portfolio_manager)
    
    def test_kelly_fraction_calculation_accuracy(self, position_sizer, strategy_stats_profitable):
        """Test Kelly Criterion formula accuracy"""
        # Test raw Kelly calculation without safety caps
        kelly_fraction = position_sizer.calculate_raw_kelly_fraction(strategy_stats_profitable)
        
        # Manual calculation: kelly = (win_rate * avg_win - (1-win_rate) * avg_loss) / avg_win
        # kelly = (0.60 * 0.025 - 0.40 * 0.015) / 0.025 = (0.015 - 0.006) / 0.025 = 0.36
        expected_kelly = Decimal("0.36")
        
        assert abs(kelly_fraction - expected_kelly) < Decimal("0.01")
        assert kelly_fraction > 0  # Should be positive for profitable strategy
        assert kelly_fraction < Decimal("1.0")  # Should never exceed 100%
        
        # Test capped Kelly calculation separately
        capped_kelly = position_sizer.calculate_kelly_fraction(strategy_stats_profitable)
        expected_capped = Decimal("0.25")  # Should be capped at 25%
        assert capped_kelly == expected_capped
    
    def test_kelly_with_losing_strategy(self, position_sizer):
        """Test Kelly Criterion with unprofitable strategy"""
        losing_stats = StrategyStats(
            win_rate=Decimal("0.40"),  # 40% win rate
            avg_win=Decimal("0.015"),  # 1.5% average win
            avg_loss=Decimal("0.020"), # 2.0% average loss
            trade_count=50,
            sharpe_ratio=Decimal("-0.5"),
            max_drawdown=Decimal("-0.30")
        )
        
        kelly_fraction = position_sizer.calculate_kelly_fraction(losing_stats)
        
        # Should return 0 or very small fraction for losing strategy
        assert kelly_fraction <= Decimal("0.01")
    
    def test_fractional_kelly_risk_reduction(self, position_sizer, strategy_stats_profitable):
        """Test fractional Kelly implementation for risk reduction"""
        full_kelly = position_sizer.calculate_kelly_fraction(strategy_stats_profitable)
        fractional_kelly = position_sizer.calculate_fractional_kelly(
            strategy_stats_profitable, 
            fraction=Decimal("0.5")  # 50% of full Kelly
        )
        
        expected_fractional = full_kelly * Decimal("0.5")
        assert abs(fractional_kelly - expected_fractional) < Decimal("0.001")
        assert fractional_kelly < full_kelly
    
    def test_max_kelly_position_limits(self, position_sizer, strategy_stats_profitable):
        """Test maximum Kelly fraction enforcement"""
        # Test with artificially high-performing strategy
        super_strategy = StrategyStats(
            win_rate=Decimal("0.90"),  # 90% win rate
            avg_win=Decimal("0.050"),  # 5% average win
            avg_loss=Decimal("0.010"), # 1% average loss
            trade_count=200,
            sharpe_ratio=Decimal("3.5"),
            max_drawdown=Decimal("-0.05")
        )
        
        kelly_fraction = position_sizer.calculate_kelly_fraction(super_strategy)
        max_allowed = Decimal("0.25")  # 25% maximum position size
        
        # Should be capped at maximum allowed
        if kelly_fraction > max_allowed:
            capped_kelly = position_sizer.apply_kelly_limits(kelly_fraction, max_allowed)
            assert capped_kelly == max_allowed
    
    def test_kelly_with_insufficient_trade_history(self, position_sizer):
        """Test Kelly calculation with insufficient trade data"""
        insufficient_stats = StrategyStats(
            win_rate=Decimal("0.65"),
            avg_win=Decimal("0.020"),
            avg_loss=Decimal("0.012"),
            trade_count=5,  # Insufficient trades
            sharpe_ratio=Decimal("1.2"),
            max_drawdown=Decimal("-0.08")
        )
        
        kelly_fraction = position_sizer.calculate_kelly_fraction(insufficient_stats)
        
        # Should apply conservative reduction for insufficient data
        assert kelly_fraction < Decimal("0.10")  # Conservative sizing
    
    def test_kelly_position_size_calculation(self, position_sizer, strategy_stats_profitable):
        """Test conversion from Kelly fraction to actual position size"""
        available_capital = Decimal("100000")  # $100,000
        target_position_value = Decimal("15000")  # Target $15,000 position
        
        kelly_fraction = position_sizer.calculate_kelly_fraction(strategy_stats_profitable)
        position_size = position_sizer.calculate_kelly_position_size(
            kelly_fraction, 
            available_capital, 
            target_position_value
        )
        
        # Validate position size is reasonable
        assert position_size > 0
        assert position_size <= available_capital * kelly_fraction
        assert isinstance(position_size, Decimal)


class TestVolatilityAdjustedSizing:
    """Test volatility-adjusted position sizing for consistent risk exposure"""
    
    @pytest.fixture
    def position_sizer(self):
        """Create position sizer with mock dependencies"""
        var_calculator = Mock()
        portfolio_manager = Mock()
        return PositionSizer(var_calculator, portfolio_manager)
    
    @pytest.fixture
    def market_data_high_vol(self):
        """Generate high volatility market data"""
        np.random.seed(42)
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')
        
        # High volatility returns (6% daily volatility)
        returns = np.random.normal(0, 0.06, 30)
        
        return pd.DataFrame({
            'BTC/USDT': returns,
            'timestamp': dates
        })
    
    @pytest.fixture
    def market_data_low_vol(self):
        """Generate low volatility market data"""
        np.random.seed(42)
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')
        
        # Low volatility returns (1% daily volatility)
        returns = np.random.normal(0, 0.01, 30)
        
        return pd.DataFrame({
            'ETH/USDT': returns,
            'timestamp': dates
        })
    
    def test_inverse_volatility_scaling(self, position_sizer, market_data_high_vol, market_data_low_vol):
        """Test inverse volatility position scaling"""
        target_volatility = Decimal("0.03")  # 3% target daily volatility
        base_position_size = Decimal("10000")  # $10,000 base position
        
        # Calculate volatility adjustments
        high_vol_adjustment = position_sizer.calculate_volatility_adjustment(
            market_data_high_vol['BTC/USDT'], target_volatility
        )
        
        low_vol_adjustment = position_sizer.calculate_volatility_adjustment(
            market_data_low_vol['ETH/USDT'], target_volatility
        )
        
        # High volatility should get smaller position (adjustment < 1.0)
        assert high_vol_adjustment < Decimal("1.0")
        
        # Low volatility should get larger position (adjustment > 1.0)
        assert low_vol_adjustment > Decimal("1.0")
        
        # Calculate adjusted position sizes
        high_vol_size = base_position_size * high_vol_adjustment
        low_vol_size = base_position_size * low_vol_adjustment
        
        # Validate sizing relationship
        assert high_vol_size < base_position_size < low_vol_size
    
    def test_target_volatility_achievement(self, position_sizer):
        """Test that volatility adjustment achieves target volatility"""
        target_vol = Decimal("0.025")  # 2.5% target volatility
        
        # Mock returns with different volatilities
        high_vol_returns = pd.Series(np.random.normal(0, 0.08, 100))  # 8% volatility
        low_vol_returns = pd.Series(np.random.normal(0, 0.01, 100))   # 1% volatility
        
        high_vol_adj = position_sizer.calculate_volatility_adjustment(high_vol_returns, target_vol)
        low_vol_adj = position_sizer.calculate_volatility_adjustment(low_vol_returns, target_vol)
        
        # Calculate resulting volatilities
        adjusted_high_vol = float(high_vol_returns.std()) * float(high_vol_adj)
        adjusted_low_vol = float(low_vol_returns.std()) * float(low_vol_adj)
        
        # Should be close to target volatility (within 20% tolerance)
        target_float = float(target_vol)
        assert abs(adjusted_high_vol - target_float) / target_float < 0.20
        assert abs(adjusted_low_vol - target_float) / target_float < 0.20
    
    def test_volatility_estimation_accuracy(self, position_sizer):
        """Test volatility estimation methods"""
        # Generate known volatility data
        true_volatility = 0.04  # 4% daily volatility
        np.random.seed(42)
        returns = np.random.normal(0, true_volatility, 252)  # 1 year of daily returns
        returns_series = pd.Series(returns)
        
        # Test different volatility estimation methods
        simple_vol = position_sizer.calculate_simple_volatility(returns_series, window=30)
        ewma_vol = position_sizer.calculate_ewma_volatility(returns_series, lambda_decay=0.94)
        garch_vol = position_sizer.calculate_garch_volatility(returns_series)
        
        # All methods should be reasonably close to true volatility
        tolerance = 0.01  # 1% tolerance
        assert abs(float(simple_vol) - true_volatility) < tolerance
        assert abs(float(ewma_vol) - true_volatility) < tolerance
        assert abs(float(garch_vol) - true_volatility) < tolerance
    
    def test_vol_adjustment_extreme_markets(self, position_sizer):
        """Test volatility adjustment in extreme market conditions"""
        target_vol = Decimal("0.02")  # 2% target
        
        # Extreme high volatility (market crash scenario)
        crash_returns = pd.Series([-0.15, -0.12, -0.08, 0.05, -0.10, 0.08, -0.06])
        
        # Extreme low volatility (market calm)
        calm_returns = pd.Series([0.001, -0.0005, 0.0008, -0.0003, 0.0012, -0.0007])
        
        crash_adjustment = position_sizer.calculate_volatility_adjustment(crash_returns, target_vol)
        calm_adjustment = position_sizer.calculate_volatility_adjustment(calm_returns, target_vol)
        
        # Crash should have very small adjustment (massive size reduction)
        assert crash_adjustment < Decimal("0.3")  # Less than 30% of normal size
        
        # Calm should have large adjustment (significant size increase)
        assert calm_adjustment > Decimal("3.0")  # More than 3x normal size
    
    def test_vol_scaling_performance_under_50ms(self, position_sizer):
        """Test volatility scaling meets performance requirements"""
        # Large dataset for performance testing
        large_returns = pd.Series(np.random.normal(0, 0.03, 10000))
        target_vol = Decimal("0.025")
        
        # Performance test
        start_time = time.perf_counter()
        
        for _ in range(100):  # 100 volatility calculations
            adjustment = position_sizer.calculate_volatility_adjustment(large_returns, target_vol)
        
        end_time = time.perf_counter()
        avg_calculation_time = ((end_time - start_time) * 1000) / 100  # ms per calculation
        
        # Should complete within 50ms per calculation
        assert avg_calculation_time < 50.0
        
        print(f"Volatility adjustment performance: {avg_calculation_time:.2f}ms per calculation")


class TestRiskBudgetAllocation:
    """Test portfolio-level risk budget allocation across strategies"""
    
    @pytest.fixture
    def position_sizer(self):
        """Create position sizer instance"""
        var_calculator = Mock()
        portfolio_manager = Mock()
        return PositionSizer(var_calculator, portfolio_manager)
    
    @pytest.fixture
    def risk_budget_config(self):
        """Create risk budget configuration"""
        return RiskBudgetConfig(
            total_portfolio_var=Decimal("0.02"),  # 2% daily portfolio VaR
            strategy_allocations={
                "momentum_btc": Decimal("0.40"),      # 40% of risk budget
                "mean_reversion_eth": Decimal("0.30"), # 30% of risk budget
                "breakout_altcoins": Decimal("0.20"),  # 20% of risk budget
                "arbitrage_pairs": Decimal("0.10")     # 10% of risk budget
            },
            rebalance_threshold=Decimal("0.05")  # 5% drift threshold
        )
    
    @pytest.fixture
    def portfolio_with_strategies(self):
        """Create portfolio with multiple strategy positions"""
        portfolio = Mock()
        portfolio.get_total_value.return_value = Decimal("1000000")  # $1M portfolio
        
        # Mock strategy positions
        strategy_positions = {
            "momentum_btc": [
                Position("BTC/USDT", Decimal("5.0"), Decimal("50000"), Decimal("51000"), "binance")
            ],
            "mean_reversion_eth": [
                Position("ETH/USDT", Decimal("100.0"), Decimal("3000"), Decimal("3100"), "binance")
            ],
            "breakout_altcoins": [
                Position("ADA/USDT", Decimal("10000"), Decimal("1.20"), Decimal("1.25"), "okx")
            ],
            "arbitrage_pairs": [
                Position("DOT/USDT", Decimal("1000"), Decimal("25.0"), Decimal("25.5"), "kraken")
            ]
        }
        portfolio.get_strategy_positions.return_value = strategy_positions
        return portfolio
    
    def test_portfolio_risk_budget_distribution(self, position_sizer, risk_budget_config, portfolio_with_strategies):
        """Test proper distribution of risk budget across strategies"""
        risk_allocations = position_sizer.allocate_risk_budget(
            portfolio_with_strategies, risk_budget_config
        )
        
        # Validate allocations sum to 100%
        total_allocation = sum(risk_allocations.values())
        assert abs(total_allocation - Decimal("1.0")) < Decimal("0.001")
        
        # Validate individual strategy allocations
        assert risk_allocations["momentum_btc"] == Decimal("0.40")
        assert risk_allocations["mean_reversion_eth"] == Decimal("0.30")
        assert risk_allocations["breakout_altcoins"] == Decimal("0.20")
        assert risk_allocations["arbitrage_pairs"] == Decimal("0.10")
    
    def test_strategy_allocation_enforcement(self, position_sizer, risk_budget_config):
        """Test enforcement of strategy-level risk allocations"""
        portfolio_value = Decimal("1000000")
        total_var_budget = portfolio_value * risk_budget_config.total_portfolio_var  # $20,000 VaR budget
        
        strategy_risk_budgets = position_sizer.calculate_strategy_risk_budgets(
            portfolio_value, risk_budget_config
        )
        
        # Validate individual strategy risk budgets
        expected_momentum = total_var_budget * Decimal("0.40")  # $8,000
        expected_mean_rev = total_var_budget * Decimal("0.30")  # $6,000
        expected_breakout = total_var_budget * Decimal("0.20")  # $4,000
        expected_arbitrage = total_var_budget * Decimal("0.10") # $2,000
        
        assert strategy_risk_budgets["momentum_btc"] == expected_momentum
        assert strategy_risk_budgets["mean_reversion_eth"] == expected_mean_rev
        assert strategy_risk_budgets["breakout_altcoins"] == expected_breakout
        assert strategy_risk_budgets["arbitrage_pairs"] == expected_arbitrage
    
    def test_dynamic_reallocation_capability(self, position_sizer, risk_budget_config):
        """Test dynamic risk budget reallocation based on strategy performance"""
        # Mock strategy performance data
        strategy_performance = {
            "momentum_btc": {"sharpe": Decimal("2.1"), "return": Decimal("0.15")},
            "mean_reversion_eth": {"sharpe": Decimal("1.8"), "return": Decimal("0.12")},
            "breakout_altcoins": {"sharpe": Decimal("0.8"), "return": Decimal("0.05")},
            "arbitrage_pairs": {"sharpe": Decimal("1.5"), "return": Decimal("0.08")}
        }
        
        # Calculate performance-weighted allocations
        new_allocations = position_sizer.calculate_performance_weighted_allocation(
            strategy_performance, risk_budget_config
        )
        
        # High-performing strategies should get more allocation
        assert new_allocations["momentum_btc"] > risk_budget_config.strategy_allocations["momentum_btc"]
        assert new_allocations["mean_reversion_eth"] > risk_budget_config.strategy_allocations["mean_reversion_eth"]
        
        # Low-performing strategy should get less allocation
        assert new_allocations["breakout_altcoins"] < risk_budget_config.strategy_allocations["breakout_altcoins"]
        
        # Total should still sum to 1.0
        assert abs(sum(new_allocations.values()) - Decimal("1.0")) < Decimal("0.001")
    
    def test_risk_budget_correlation_adjustments(self, position_sizer, risk_budget_config):
        """Test risk budget adjustments for strategy correlations"""
        # Mock correlation matrix between strategies
        correlation_matrix = {
            ("momentum_btc", "mean_reversion_eth"): Decimal("0.3"),
            ("momentum_btc", "breakout_altcoins"): Decimal("0.7"),  # High correlation
            ("momentum_btc", "arbitrage_pairs"): Decimal("-0.1"),
            ("mean_reversion_eth", "breakout_altcoins"): Decimal("0.2"),
            ("mean_reversion_eth", "arbitrage_pairs"): Decimal("-0.2"),
            ("breakout_altcoins", "arbitrage_pairs"): Decimal("0.1")
        }
        
        adjusted_allocations = position_sizer.adjust_allocations_for_correlation(
            risk_budget_config.strategy_allocations, correlation_matrix
        )
        
        # High correlation between momentum and breakout should reduce their combined allocation
        combined_correlated = adjusted_allocations["momentum_btc"] + adjusted_allocations["breakout_altcoins"]
        original_combined = risk_budget_config.strategy_allocations["momentum_btc"] + risk_budget_config.strategy_allocations["breakout_altcoins"]
        
        assert combined_correlated < original_combined
    
    def test_concentration_limit_compliance(self, position_sizer, risk_budget_config):
        """Test enforcement of concentration limits in risk allocation"""
        # Create configuration with high concentration
        concentrated_config = RiskBudgetConfig(
            total_portfolio_var=Decimal("0.02"),
            strategy_allocations={
                "momentum_btc": Decimal("0.80"),      # 80% concentration
                "mean_reversion_eth": Decimal("0.15"),
                "arbitrage_pairs": Decimal("0.05")
            }
        )
        
        max_strategy_allocation = Decimal("0.50")  # 50% maximum per strategy
        
        limited_allocations = position_sizer.apply_concentration_limits(
            concentrated_config.strategy_allocations, max_strategy_allocation
        )
        
        # Should cap momentum strategy at 50%
        assert limited_allocations["momentum_btc"] == max_strategy_allocation
        
        # Other allocations should be scaled up proportionally
        remaining_allocation = Decimal("1.0") - max_strategy_allocation
        expected_mean_rev = (Decimal("0.15") / Decimal("0.20")) * remaining_allocation
        
        assert abs(limited_allocations["mean_reversion_eth"] - expected_mean_rev) < Decimal("0.01")


class TestPositionSizerIntegration:
    """Test integration with existing trading system components"""
    
    @pytest.fixture
    def full_trading_system(self):
        """Create mock trading system with all components"""
        var_calculator = Mock()
        portfolio_manager = Mock()
        strategy_manager = Mock()
        
        # Mock portfolio with realistic data
        portfolio = Mock()
        portfolio.get_total_value.return_value = Decimal("500000")
        
        # Mock VaR calculator results
        var_calculator.calculate_historical_var.return_value = Mock(
            portfolio_var=Decimal("10000"),  # $10,000 daily VaR
            component_var={"BTC/USDT": Decimal("6000"), "ETH/USDT": Decimal("4000")}
        )
        
        return {
            "var_calculator": var_calculator,
            "portfolio_manager": portfolio_manager,
            "strategy_manager": strategy_manager,
            "portfolio": portfolio
        }
    
    def test_var_engine_integration(self, full_trading_system):
        """Test seamless integration with VaR calculation engine"""
        position_sizer = PositionSizer(
            full_trading_system["var_calculator"],
            full_trading_system["portfolio_manager"]
        )
        
        # Mock trading signal
        signal = TradingSignal(
            symbol="BTC/USDT",
            action="BUY",
            confidence=Decimal("0.85"),
            strategy_id="momentum_btc",
            timestamp=datetime.now()
        )
        
        # Calculate position size using VaR inputs
        sizing_result = position_sizer.calculate_position_size(signal)
        
        # Validate integration
        assert isinstance(sizing_result, PositionSizingResult)
        assert sizing_result.symbol == "BTC/USDT"
        assert sizing_result.recommended_size > 0
        assert sizing_result.risk_contribution <= Decimal("10000")  # Within portfolio VaR
    
    def test_real_time_data_pipeline_integration(self, full_trading_system):
        """Test integration with real-time market data pipeline"""
        position_sizer = RealTimePositionSizer(
            full_trading_system["var_calculator"],
            full_trading_system["portfolio_manager"]
        )
        
        # Mock streaming market data
        market_data_stream = [
            {"symbol": "BTC/USDT", "price": Decimal("51000"), "volume": Decimal("100")},
            {"symbol": "ETH/USDT", "price": Decimal("3100"), "volume": Decimal("500")},
            {"symbol": "ADA/USDT", "price": Decimal("1.25"), "volume": Decimal("10000")}
        ]
        
        # Process streaming data for position sizing
        for data_point in market_data_stream:
            position_sizer.update_market_data(data_point)
        
        # Validate real-time processing
        latest_volatilities = position_sizer.get_current_volatilities()
        assert "BTC/USDT" in latest_volatilities
        assert "ETH/USDT" in latest_volatilities
        assert "ADA/USDT" in latest_volatilities
    
    def test_strategy_manager_signal_processing(self, full_trading_system):
        """Test processing of strategy manager signals"""
        position_sizer = PositionSizer(
            full_trading_system["var_calculator"],
            full_trading_system["portfolio_manager"]
        )
        
        # Mock multiple strategy signals
        strategy_signals = [
            TradingSignal("BTC/USDT", "BUY", Decimal("0.90"), "momentum_btc", datetime.now()),
            TradingSignal("ETH/USDT", "SELL", Decimal("0.75"), "mean_reversion_eth", datetime.now()),
            TradingSignal("ADA/USDT", "BUY", Decimal("0.80"), "breakout_altcoins", datetime.now())
        ]
        
        # Batch process signals
        sizing_results = position_sizer.batch_calculate_position_sizes(strategy_signals)
        
        # Validate batch processing
        assert len(sizing_results) == 3
        for result in sizing_results:
            assert isinstance(result, PositionSizingResult)
            assert result.recommended_size > 0
            assert result.sizing_method in ["kelly", "volatility_adjusted", "risk_budget"]
    
    def test_portfolio_manager_position_updates(self, full_trading_system):
        """Test position updates integration with portfolio manager"""
        position_sizer = PositionSizer(
            full_trading_system["var_calculator"],
            full_trading_system["portfolio_manager"]
        )
        
        # Mock current portfolio positions
        current_positions = {
            "BTC/USDT": Position("BTC/USDT", Decimal("2.0"), Decimal("50000"), Decimal("51000"), "binance"),
            "ETH/USDT": Position("ETH/USDT", Decimal("50.0"), Decimal("3000"), Decimal("3100"), "binance")
        }
        
        full_trading_system["portfolio_manager"].get_current_positions.return_value = current_positions
        
        # Calculate incremental position sizing
        signal = TradingSignal("BTC/USDT", "BUY", Decimal("0.85"), "momentum_btc", datetime.now())
        sizing_result = position_sizer.calculate_incremental_position_size(signal)
        
        # Should account for existing position
        assert sizing_result.symbol == "BTC/USDT"
        assert hasattr(sizing_result, 'current_position_size')
        assert hasattr(sizing_result, 'incremental_size')
    
    def test_full_sizing_pipeline_performance(self, full_trading_system):
        """Test end-to-end position sizing pipeline performance"""
        position_sizer = OptimizedPositionSizer(
            full_trading_system["var_calculator"],
            full_trading_system["portfolio_manager"]
        )
        
        # Large batch of signals for performance testing
        large_signal_batch = []
        symbols = [f"ASSET{i:03d}/USDT" for i in range(100)]
        
        for symbol in symbols:
            signal = TradingSignal(symbol, "BUY", Decimal("0.80"), "momentum", datetime.now())
            large_signal_batch.append(signal)
        
        # Performance test
        start_time = time.perf_counter()
        sizing_results = position_sizer.batch_calculate_position_sizes(large_signal_batch)
        end_time = time.perf_counter()
        
        total_time_ms = (end_time - start_time) * 1000
        avg_time_per_signal = total_time_ms / len(large_signal_batch)
        
        # Should process 100 signals within 50ms total (0.5ms per signal)
        assert total_time_ms < 50.0
        assert avg_time_per_signal < 0.5
        
        print(f"Position sizing pipeline performance: {total_time_ms:.2f}ms total, {avg_time_per_signal:.3f}ms per signal")


class TestPositionSizerPerformance:
    """Test position sizer performance requirements for real-time trading"""
    
    @pytest.fixture
    def large_portfolio_data(self):
        """Create large portfolio dataset for performance testing"""
        symbols = [f"ASSET{i:03d}/USDT" for i in range(100)]
        positions = {}
        
        for symbol in symbols:
            positions[symbol] = Position(
                symbol=symbol,
                quantity=Decimal("100.0"),
                avg_price=Decimal("1000"),
                current_price=Decimal("1100"),
                exchange="binance"
            )
        
        portfolio = Portfolio(positions=positions, cash_balance=Decimal("1000000"))
        return portfolio
    
    def test_sizing_calculation_under_50ms(self, large_portfolio_data):
        """Test position sizing meets <50ms requirement for large portfolios"""
        var_calculator = Mock()
        portfolio_manager = Mock()
        position_sizer = OptimizedPositionSizer(var_calculator, portfolio_manager)
        
        # Mock VaR calculation for performance testing
        var_calculator.calculate_historical_var.return_value = Mock(
            portfolio_var=Decimal("20000"),
            component_var={symbol: Decimal("200") for symbol in large_portfolio_data.positions.keys()}
        )
        
        # Performance test with large signal batch
        signals = []
        for symbol in large_portfolio_data.positions.keys():
            signals.append(TradingSignal(symbol, "BUY", Decimal("0.80"), "momentum", datetime.now()))
        
        start_time = time.perf_counter()
        results = position_sizer.batch_calculate_position_sizes(signals)
        calculation_time = (time.perf_counter() - start_time) * 1000
        
        # Must complete within 50ms for 100 positions
        assert calculation_time < 50.0
        assert len(results) == 100
        
        print(f"Large portfolio sizing performance: {calculation_time:.2f}ms for 100 positions")
    
    def test_concurrent_sizing_decisions(self):
        """Test concurrent position sizing for multiple strategies"""
        import threading
        import concurrent.futures
        
        var_calculator = Mock()
        portfolio_manager = Mock()
        position_sizer = OptimizedPositionSizer(var_calculator, portfolio_manager)
        
        def calculate_positions_for_strategy(strategy_id):
            signals = [
                TradingSignal(f"ASSET{i:03d}/USDT", "BUY", Decimal("0.80"), strategy_id, datetime.now())
                for i in range(20)
            ]
            return position_sizer.batch_calculate_position_sizes(signals)
        
        # Test concurrent execution with 5 strategies
        strategy_ids = ["momentum", "mean_reversion", "breakout", "arbitrage", "ensemble"]
        
        start_time = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(calculate_positions_for_strategy, strategy_id) 
                      for strategy_id in strategy_ids]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        concurrent_time = (time.perf_counter() - start_time) * 1000
        
        # Concurrent processing should be efficient
        assert concurrent_time < 100.0  # 100ms for 5 concurrent strategies
        assert len(results) == 5
        
        print(f"Concurrent sizing performance: {concurrent_time:.2f}ms for 5 strategies")
    
    def test_memory_efficiency_optimization(self):
        """Test memory efficiency for large-scale position sizing"""
        import psutil
        import gc
        
        var_calculator = Mock()
        portfolio_manager = Mock()
        position_sizer = OptimizedPositionSizer(var_calculator, portfolio_manager)
        
        # Measure initial memory
        gc.collect()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        large_signal_batch = []
        for i in range(1000):  # 1000 signals
            signal = TradingSignal(f"ASSET{i:04d}/USDT", "BUY", Decimal("0.80"), "momentum", datetime.now())
            large_signal_batch.append(signal)
        
        # Process large batch
        results = position_sizer.batch_calculate_position_sizes(large_signal_batch)
        
        # Measure memory after processing
        gc.collect()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (<100MB for 1000 signals)
        assert memory_increase < 100.0
        assert len(results) == 1000
        
        print(f"Memory efficiency: {memory_increase:.1f}MB increase for 1000 signals")


class TestPositionLimits:
    """Test position limits and risk controls"""
    
    @pytest.fixture
    def position_limits(self):
        """Create position limits configuration"""
        return PositionLimits(
            max_position_pct=Decimal("0.15"),      # 15% max position
            max_leverage=Decimal("2.0"),           # 2x max leverage
            max_correlation_exposure=Decimal("0.6"), # 60% max correlated exposure
            liquidity_buffer=Decimal("0.05")       # 5% liquidity buffer
        )
    
    def test_maximum_position_size_enforcement(self, position_limits):
        """Test enforcement of maximum position size limits"""
        var_calculator = Mock()
        portfolio_manager = Mock()
        position_sizer = PositionSizer(var_calculator, portfolio_manager)
        
        portfolio_value = Decimal("1000000")  # $1M portfolio
        max_position_value = portfolio_value * position_limits.max_position_pct  # $150,000
        
        # Test oversized position request
        large_signal = TradingSignal("BTC/USDT", "BUY", Decimal("0.95"), "momentum", datetime.now())
        
        # Mock Kelly calculation that would suggest large position
        with patch.object(position_sizer, 'calculate_kelly_fraction', return_value=Decimal("0.30")):
            sizing_result = position_sizer.calculate_position_size(large_signal, position_limits)
        
        # Should be capped at maximum allowed
        assert sizing_result.recommended_size <= max_position_value
        assert sizing_result.max_position_limit == max_position_value
    
    def test_concentration_risk_prevention(self, position_limits):
        """Test prevention of excessive concentration risk"""
        var_calculator = Mock()
        portfolio_manager = Mock()
        position_sizer = PositionSizer(var_calculator, portfolio_manager)
        
        # Mock portfolio with existing large BTC position
        existing_positions = {
            "BTC/USDT": Position("BTC/USDT", Decimal("3.0"), Decimal("50000"), Decimal("51000"), "binance")
        }
        portfolio_manager.get_current_positions.return_value = existing_positions
        portfolio_manager.get_total_value.return_value = Decimal("1000000")
        
        # Calculate existing concentration
        existing_btc_value = Decimal("3.0") * Decimal("51000")  # $153,000
        existing_concentration = existing_btc_value / Decimal("1000000")  # 15.3%
        
        # Try to add more BTC position
        additional_signal = TradingSignal("BTC/USDT", "BUY", Decimal("0.85"), "momentum", datetime.now())
        sizing_result = position_sizer.calculate_position_size(additional_signal, position_limits)
        
        # Should limit additional exposure to stay under concentration limit
        total_recommended_value = existing_btc_value + sizing_result.recommended_size
        total_concentration = total_recommended_value / Decimal("1000000")
        
        assert total_concentration <= position_limits.max_position_pct
    
    def test_leverage_limit_compliance(self, position_limits):
        """Test compliance with leverage limits"""
        var_calculator = Mock()
        portfolio_manager = Mock()
        position_sizer = PositionSizer(var_calculator, portfolio_manager)
        
        portfolio_value = Decimal("1000000")  # $1M portfolio
        max_notional = portfolio_value * position_limits.max_leverage  # $2M max notional
        
        # Mock current portfolio with high leverage
        current_notional = Decimal("1800000")  # $1.8M current notional
        portfolio_manager.get_total_notional_value.return_value = current_notional
        portfolio_manager.get_total_value.return_value = portfolio_value
        
        # Try to add large position
        large_signal = TradingSignal("ETH/USDT", "BUY", Decimal("0.90"), "momentum", datetime.now())
        sizing_result = position_sizer.calculate_position_size(large_signal, position_limits)
        
        # Should limit position to stay under leverage limit
        total_notional_after = current_notional + sizing_result.recommended_size
        leverage_after = total_notional_after / portfolio_value
        
        assert leverage_after <= position_limits.max_leverage
    
    def test_liquidity_constraint_handling(self, position_limits):
        """Test handling of liquidity constraints"""
        var_calculator = Mock()
        portfolio_manager = Mock()
        position_sizer = PositionSizer(var_calculator, portfolio_manager)
        
        # Mock market data with liquidity information
        market_liquidity = {
            "BTC/USDT": {"daily_volume": Decimal("1000000"), "bid_ask_spread": Decimal("0.001")},
            "LOWLIQ/USDT": {"daily_volume": Decimal("10000"), "bid_ask_spread": Decimal("0.05")}
        }
        
        # High liquidity asset should allow normal sizing
        btc_signal = TradingSignal("BTC/USDT", "BUY", Decimal("0.85"), "momentum", datetime.now())
        btc_result = position_sizer.calculate_position_size(btc_signal, position_limits, market_liquidity)
        
        # Low liquidity asset should have reduced sizing
        lowliq_signal = TradingSignal("LOWLIQ/USDT", "BUY", Decimal("0.85"), "momentum", datetime.now())
        lowliq_result = position_sizer.calculate_position_size(lowliq_signal, position_limits, market_liquidity)
        
        # Low liquidity position should be smaller (liquidity-adjusted)
        assert lowliq_result.recommended_size < btc_result.recommended_size
        assert lowliq_result.sizing_method == "liquidity_adjusted"


class TestDynamicAdjustments:
    """Test dynamic position size adjustments based on market conditions"""
    
    def test_drawdown_based_size_reduction(self):
        """Test position size reduction during drawdown periods"""
        var_calculator = Mock()
        portfolio_manager = Mock()
        position_sizer = PositionSizer(var_calculator, portfolio_manager)
        
        # Mock portfolio in drawdown
        portfolio_manager.get_current_drawdown.return_value = Decimal("-0.15")  # 15% drawdown
        
        base_signal = TradingSignal("BTC/USDT", "BUY", Decimal("0.80"), "momentum", datetime.now())
        
        # Calculate position size during drawdown
        drawdown_result = position_sizer.calculate_position_size_with_drawdown_adjustment(base_signal)
        
        # Position size should be reduced during drawdown
        assert drawdown_result.volatility_adjustment < Decimal("1.0")
        assert "drawdown_adjusted" in drawdown_result.sizing_method
    
    def test_volatility_regime_change_adaptation(self):
        """Test adaptation to changing volatility regimes"""
        var_calculator = Mock()
        portfolio_manager = Mock()
        position_sizer = PositionSizer(var_calculator, portfolio_manager)
        
        # Mock volatility regime detection
        low_vol_regime = {"current_vol": Decimal("0.01"), "regime": "low_volatility"}
        high_vol_regime = {"current_vol": Decimal("0.08"), "regime": "high_volatility"}
        
        signal = TradingSignal("BTC/USDT", "BUY", Decimal("0.80"), "momentum", datetime.now())
        
        # Low volatility regime should allow larger positions
        low_vol_result = position_sizer.calculate_position_size_with_regime_detection(signal, low_vol_regime)
        
        # High volatility regime should reduce positions
        high_vol_result = position_sizer.calculate_position_size_with_regime_detection(signal, high_vol_regime)
        
        assert low_vol_result.recommended_size > high_vol_result.recommended_size
        assert low_vol_result.volatility_adjustment > high_vol_result.volatility_adjustment
    
    def test_correlation_breakdown_response(self):
        """Test response to correlation breakdown events"""
        var_calculator = Mock()
        portfolio_manager = Mock()
        position_sizer = PositionSizer(var_calculator, portfolio_manager)
        
        # Mock correlation breakdown detection
        normal_correlations = {"BTC/USDT_ETH/USDT": Decimal("0.7")}
        breakdown_correlations = {"BTC/USDT_ETH/USDT": Decimal("0.95")}  # Excessive correlation
        
        signal = TradingSignal("ETH/USDT", "BUY", Decimal("0.80"), "momentum", datetime.now())
        
        # Normal correlation should allow normal position
        normal_result = position_sizer.calculate_position_size_with_correlation_monitoring(
            signal, normal_correlations
        )
        
        # Correlation breakdown should reduce position
        breakdown_result = position_sizer.calculate_position_size_with_correlation_monitoring(
            signal, breakdown_correlations
        )
        
        assert breakdown_result.recommended_size < normal_result.recommended_size
        assert "correlation_adjusted" in breakdown_result.sizing_method
    
    def test_emergency_position_reduction(self):
        """Test emergency position reduction during market stress"""
        var_calculator = Mock()
        portfolio_manager = Mock()
        position_sizer = PositionSizer(var_calculator, portfolio_manager)
        
        # Mock market stress conditions
        stress_indicators = {
            "vix_spike": True,
            "liquidity_dry_up": True,
            "correlation_breakdown": True,
            "portfolio_drawdown": Decimal("-0.20")
        }
        
        normal_signal = TradingSignal("BTC/USDT", "BUY", Decimal("0.85"), "momentum", datetime.now())
        
        # Emergency mode should drastically reduce position sizes
        emergency_result = position_sizer.calculate_emergency_position_size(normal_signal, stress_indicators)
        
        # Emergency sizing should be very conservative
        assert emergency_result.recommended_size < Decimal("10000")  # Very small position
        assert emergency_result.sizing_method == "emergency_conservative"
        assert emergency_result.risk_contribution < Decimal("1000")  # Minimal risk


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])