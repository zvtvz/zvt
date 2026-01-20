# -*- coding: utf-8 -*-
"""
TDD Cycle 3: REFACTOR Phase 3.3.1 - Portfolio Risk Engine Tests
==============================================================

Comprehensive test suite for institutional-grade Portfolio Value-at-Risk (VaR) calculation.
Following specifications-driven TDD methodology with performance requirements.

RED PHASE: These tests should FAIL initially to drive implementation.

Business Requirements:
- Portfolio VaR calculation using multiple methodologies (Historical, Parametric, Monte Carlo)
- <10ms calculation time for real-time trading
- Multiple confidence levels (95%, 99%) and time horizons (1-day, 5-day, 10-day)
- Expected Shortfall (CVaR) for tail risk assessment
- VaR attribution by asset and strategy
- Integration with real-time portfolio updates
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
from zvt.trading.risk_engine import (
    VaRCalculator,
    VaRResult,
    VaRMethod,
    RiskAttribution,
    PortfolioRiskEngine,
    RiskMetrics
)
from zvt.trading.portfolio import Portfolio, Position


class TestVaRCalculatorCore:
    """Test core VaR calculation functionality and accuracy"""
    
    @pytest.fixture
    def sample_portfolio(self):
        """Create sample portfolio for testing"""
        positions = {
            "BTC/USDT": Position(
                symbol="BTC/USDT",
                quantity=Decimal("1.5"),
                avg_price=Decimal("50000"),
                current_price=Decimal("51000"),
                exchange="binance"
            ),
            "ETH/USDT": Position(
                symbol="ETH/USDT", 
                quantity=Decimal("10.0"),
                avg_price=Decimal("3000"),
                current_price=Decimal("3100"),
                exchange="binance"
            ),
            "ADA/USDT": Position(
                symbol="ADA/USDT",
                quantity=Decimal("1000.0"),
                avg_price=Decimal("1.20"),
                current_price=Decimal("1.25"),
                exchange="okx"
            )
        }
        
        return Portfolio(
            positions=positions,
            cash_balance=Decimal("10000"),
            base_currency="USDT"
        )
    
    @pytest.fixture
    def historical_returns_data(self):
        """Generate historical returns data for VaR calculation"""
        np.random.seed(42)  # Reproducible results
        
        # 250 days of historical returns
        n_days = 250
        n_assets = 3
        
        # Realistic correlation structure
        correlation_matrix = np.array([
            [1.00, 0.65, 0.45],  # BTC correlations
            [0.65, 1.00, 0.55],  # ETH correlations  
            [0.45, 0.55, 1.00]   # ADA correlations
        ])
        
        # Generate correlated returns
        returns = np.random.multivariate_normal(
            mean=[0.001, 0.0008, 0.0005],  # Different expected returns
            cov=correlation_matrix * 0.04,  # 4% daily volatility scaled
            size=n_days
        )
        
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=n_days),
            periods=n_days,
            freq='D'
        )
        
        return pd.DataFrame(
            returns,
            index=dates,
            columns=["BTC/USDT", "ETH/USDT", "ADA/USDT"]
        )
    
    @pytest.fixture
    def var_calculator(self):
        """Create VaR calculator instance"""
        return VaRCalculator()
    
    def test_var_calculator_initialization(self, var_calculator):
        """Test VaR calculator proper initialization"""
        assert var_calculator is not None
        assert hasattr(var_calculator, 'calculate_historical_var')
        assert hasattr(var_calculator, 'calculate_parametric_var')
        assert hasattr(var_calculator, 'calculate_monte_carlo_var')
    
    def test_historical_var_calculation_accuracy(self, var_calculator, sample_portfolio, historical_returns_data):
        """Test historical VaR calculation accuracy and expected properties"""
        confidence_level = 0.95
        time_horizon = 1  # 1-day VaR
        
        result = var_calculator.calculate_historical_var(
            portfolio=sample_portfolio,
            historical_returns=historical_returns_data,
            confidence=confidence_level,
            time_horizon_days=time_horizon,
            lookback_days=250
        )
        
        # Validate result structure
        assert isinstance(result, VaRResult)
        assert result.portfolio_var > 0  # VaR should be positive (loss amount)
        assert result.confidence_level == confidence_level
        assert result.time_horizon_days == time_horizon
        assert result.calculation_method == VaRMethod.HISTORICAL_SIMULATION
        assert len(result.component_var) == 3  # Three assets
        assert result.expected_shortfall > result.portfolio_var  # CVaR > VaR
        
        # Validate statistical properties
        # VaR should be reasonable for crypto portfolio (typically 2-10% daily)
        portfolio_value = sample_portfolio.get_total_value()
        var_percentage = float(result.portfolio_var / portfolio_value)
        assert 0.01 <= var_percentage <= 0.20  # 1% to 20% seems reasonable for crypto
        
        # Component VaR should sum approximately to portfolio VaR (with diversification)
        total_component_var = sum(result.component_var.values())
        diversification_benefit = total_component_var - result.portfolio_var
        assert diversification_benefit >= 0  # Diversification should reduce risk
    
    def test_parametric_var_with_correlation_matrix(self, var_calculator, sample_portfolio, historical_returns_data):
        """Test parametric VaR calculation using correlation matrix approach"""
        result = var_calculator.calculate_parametric_var(
            portfolio=sample_portfolio,
            historical_returns=historical_returns_data,
            confidence=0.99,  # 99% confidence level
            covariance_method="ewma",  # Exponentially weighted moving average
            lambda_decay=0.94  # Standard EWMA decay factor
        )
        
        # Validate result properties
        assert isinstance(result, VaRResult)
        assert result.calculation_method == VaRMethod.PARAMETRIC
        assert result.confidence_level == 0.99
        assert result.portfolio_var > 0
        
        # 99% VaR should be higher than 95% VaR (more extreme scenario)
        var_95_result = var_calculator.calculate_parametric_var(
            portfolio=sample_portfolio,
            historical_returns=historical_returns_data,
            confidence=0.95
        )
        assert result.portfolio_var > var_95_result.portfolio_var
        
        # Parametric method should have covariance matrix in metadata
        assert "covariance_matrix" in result.calculation_metadata
        assert "volatilities" in result.calculation_metadata
    
    def test_monte_carlo_var_simulation_convergence(self, var_calculator, sample_portfolio, historical_returns_data):
        """Test Monte Carlo VaR simulation accuracy and convergence"""
        # Test convergence with different simulation counts
        simulations_counts = [1000, 5000, 10000]
        var_results = []
        
        for sim_count in simulations_counts:
            result = var_calculator.calculate_monte_carlo_var(
                portfolio=sample_portfolio,
                historical_returns=historical_returns_data,
                confidence=0.95,
                simulations=sim_count,
                random_seed=42  # For reproducible results
            )
            var_results.append(result.portfolio_var)
        
        # VaR estimates should converge (difference should decrease)
        diff_1000_5000 = abs(var_results[1] - var_results[0])
        diff_5000_10000 = abs(var_results[2] - var_results[1])
        
        # Higher simulation count should provide more stable estimates
        assert diff_5000_10000 <= diff_1000_5000
        
        # Validate Monte Carlo specific properties
        final_result = var_calculator.calculate_monte_carlo_var(
            portfolio=sample_portfolio,
            historical_returns=historical_returns_data,
            confidence=0.95,
            simulations=10000
        )
        
        assert final_result.calculation_method == VaRMethod.MONTE_CARLO
        assert "simulations_run" in final_result.calculation_metadata
        assert final_result.calculation_metadata["simulations_run"] == 10000


class TestVaRCalculatorPerformance:
    """Test VaR calculation performance requirements (<10ms target)"""
    
    @pytest.fixture
    def large_portfolio(self):
        """Create large portfolio for performance testing"""
        positions = {}
        
        # Create 100 positions to simulate institutional portfolio
        symbols = [f"ASSET{i:03d}/USDT" for i in range(100)]
        
        for symbol in symbols:
            positions[symbol] = Position(
                symbol=symbol,
                quantity=Decimal("100.0"),
                avg_price=Decimal("1000"),
                current_price=Decimal("1100"),
                exchange="binance"
            )
        
        return Portfolio(
            positions=positions,
            cash_balance=Decimal("100000"),
            base_currency="USDT"
        )
    
    @pytest.fixture
    def large_returns_data(self):
        """Generate large historical returns dataset for performance testing"""
        np.random.seed(42)
        
        # 500 days, 100 assets
        n_days = 500
        n_assets = 100
        
        # Generate realistic correlation structure
        correlation_matrix = np.eye(n_assets)
        for i in range(n_assets):
            for j in range(n_assets):
                if i != j:
                    correlation_matrix[i, j] = 0.3 * np.exp(-abs(i - j) / 10)
        
        returns = np.random.multivariate_normal(
            mean=np.zeros(n_assets),
            cov=correlation_matrix * 0.02,  # 2% volatility
            size=n_days
        )
        
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=n_days),
            periods=n_days,
            freq='D'
        )
        
        columns = [f"ASSET{i:03d}/USDT" for i in range(n_assets)]
        
        return pd.DataFrame(returns, index=dates, columns=columns)
    
    def test_var_calculation_performance_under_10ms(self, large_portfolio, large_returns_data):
        """Test VaR calculation meets <10ms performance target"""
        var_calculator = VaRCalculator()
        
        # Warm up (JIT compilation, cache loading)
        var_calculator.calculate_historical_var(
            portfolio=large_portfolio,
            historical_returns=large_returns_data,
            confidence=0.95,
            lookback_days=250
        )
        
        # Performance test with multiple runs
        calculation_times = []
        for _ in range(5):
            start_time = time.perf_counter()
            
            result = var_calculator.calculate_historical_var(
                portfolio=large_portfolio,
                historical_returns=large_returns_data,
                confidence=0.95,
                lookback_days=250
            )
            
            end_time = time.perf_counter()
            calculation_time = (end_time - start_time) * 1000  # Convert to ms
            calculation_times.append(calculation_time)
        
        # Validate performance requirements
        avg_calculation_time = sum(calculation_times) / len(calculation_times)
        max_calculation_time = max(calculation_times)
        
        # Target: <10ms average, <15ms maximum
        assert avg_calculation_time < 10.0, f"Average calculation time {avg_calculation_time:.2f}ms exceeds 10ms target"
        assert max_calculation_time < 15.0, f"Maximum calculation time {max_calculation_time:.2f}ms exceeds 15ms limit"
        
        # Validate calculation time is recorded in result
        assert result.calculation_time_ms < 15.0
        
        print(f"VaR Calculation Performance: {avg_calculation_time:.2f}ms average ({max_calculation_time:.2f}ms max)")
    
    def test_parametric_var_performance_optimization(self, large_portfolio, large_returns_data):
        """Test parametric VaR calculation performance with caching"""
        var_calculator = VaRCalculator()
        
        # First calculation (cold cache)
        start_time = time.perf_counter()
        result1 = var_calculator.calculate_parametric_var(
            portfolio=large_portfolio,
            historical_returns=large_returns_data,
            confidence=0.95
        )
        first_calc_time = (time.perf_counter() - start_time) * 1000
        
        # Second calculation (warm cache - covariance matrix cached)
        start_time = time.perf_counter()
        result2 = var_calculator.calculate_parametric_var(
            portfolio=large_portfolio,
            historical_returns=large_returns_data,
            confidence=0.99  # Different confidence, same covariance
        )
        second_calc_time = (time.perf_counter() - start_time) * 1000
        
        # Cached calculation should be faster
        assert second_calc_time < first_calc_time
        assert second_calc_time < 5.0  # Should be very fast with cache
        
        print(f"Parametric VaR: {first_calc_time:.2f}ms (cold) → {second_calc_time:.2f}ms (cached)")


class TestVaRAttributionAndMetrics:
    """Test VaR attribution, component analysis, and advanced metrics"""
    
    def test_var_attribution_by_strategy(self):
        """Test VaR attribution breakdown by trading strategy"""
        var_calculator = VaRCalculator()
        
        # Create portfolio with strategy attribution
        portfolio_with_strategies = Mock()
        portfolio_with_strategies.get_strategy_positions.return_value = {
            "momentum_btc": ["BTC/USDT"],
            "mean_reversion_eth": ["ETH/USDT"],
            "arbitrage_multi": ["ADA/USDT", "DOT/USDT"]
        }
        
        # Mock historical returns
        returns_data = pd.DataFrame({
            "BTC/USDT": np.random.normal(0, 0.03, 100),
            "ETH/USDT": np.random.normal(0, 0.04, 100),  
            "ADA/USDT": np.random.normal(0, 0.05, 100),
            "DOT/USDT": np.random.normal(0, 0.045, 100)
        })
        
        result = var_calculator.calculate_var_with_attribution(
            portfolio=portfolio_with_strategies,
            historical_returns=returns_data,
            attribution_type="strategy"
        )
        
        # Validate strategy attribution
        assert "strategy_attribution" in result.calculation_metadata
        strategy_vars = result.calculation_metadata["strategy_attribution"]
        
        assert "momentum_btc" in strategy_vars
        assert "mean_reversion_eth" in strategy_vars
        assert "arbitrage_multi" in strategy_vars
        
        # Strategy VaRs should be positive
        for strategy_var in strategy_vars.values():
            assert strategy_var > 0
    
    def test_expected_shortfall_calculation(self):
        """Test Expected Shortfall (Conditional VaR) calculation"""
        var_calculator = VaRCalculator()
        
        # Create simple portfolio
        portfolio = Mock()
        portfolio.get_positions.return_value = {
            "BTC/USDT": Mock(quantity=Decimal("1.0"), current_price=Decimal("50000"))
        }
        portfolio.get_total_value.return_value = Decimal("50000")
        
        # Historical returns with known distribution
        np.random.seed(42)
        returns = np.random.normal(-0.001, 0.03, 1000)  # Slight negative bias
        returns_data = pd.DataFrame({"BTC/USDT": returns})
        
        result = var_calculator.calculate_historical_var(
            portfolio=portfolio,
            historical_returns=returns_data,
            confidence=0.95
        )
        
        # Expected Shortfall should be greater than VaR
        assert result.expected_shortfall > result.portfolio_var
        
        # ES should represent average loss beyond VaR threshold
        var_threshold = np.percentile(returns, 5)  # 5th percentile for 95% confidence
        expected_es = -np.mean(returns[returns <= var_threshold]) * Decimal("50000")
        
        # Allow for reasonable tolerance in calculation
        assert abs(result.expected_shortfall - expected_es) / expected_es < 0.1
    
    def test_var_confidence_intervals(self):
        """Test VaR calculation with confidence intervals and uncertainty estimation"""
        var_calculator = VaRCalculator()
        
        portfolio = Mock()
        portfolio.get_total_value.return_value = Decimal("100000")
        
        # Bootstrap sample for confidence intervals
        np.random.seed(42)
        returns_data = pd.DataFrame({
            "BTC/USDT": np.random.normal(0, 0.03, 500)
        })
        
        result = var_calculator.calculate_var_with_confidence_intervals(
            portfolio=portfolio,
            historical_returns=returns_data,
            confidence=0.95,
            bootstrap_samples=1000
        )
        
        # Validate confidence interval structure
        assert "confidence_interval" in result.calculation_metadata
        ci = result.calculation_metadata["confidence_interval"]
        
        assert "lower_bound" in ci
        assert "upper_bound" in ci
        assert ci["lower_bound"] < result.portfolio_var < ci["upper_bound"]


class TestRealTimeVaRUpdates:
    """Test real-time VaR updates with streaming market data"""
    
    def test_var_updates_with_real_time_data(self):
        """Test VaR recalculation with real-time portfolio updates"""
        var_calculator = VaRCalculator()
        
        # Initial portfolio and VaR calculation
        initial_portfolio = Mock()
        initial_portfolio.get_total_value.return_value = Decimal("100000")
        
        returns_data = pd.DataFrame({
            "BTC/USDT": np.random.normal(0, 0.03, 200),
            "ETH/USDT": np.random.normal(0, 0.04, 200)
        })
        
        initial_var = var_calculator.calculate_historical_var(
            portfolio=initial_portfolio,
            historical_returns=returns_data,
            confidence=0.95
        )
        
        # Simulate real-time portfolio update (price change)
        updated_portfolio = Mock()
        updated_portfolio.get_total_value.return_value = Decimal("105000")  # 5% increase
        
        updated_var = var_calculator.calculate_historical_var(
            portfolio=updated_portfolio,
            historical_returns=returns_data,
            confidence=0.95
        )
        
        # VaR should scale approximately with portfolio value
        var_ratio = updated_var.portfolio_var / initial_var.portfolio_var
        portfolio_ratio = Decimal("105000") / Decimal("100000")
        
        # Allow for calculation differences, but should be close
        assert abs(float(var_ratio - portfolio_ratio)) < 0.1
    
    def test_var_calculation_with_streaming_returns(self):
        """Test VaR updates with streaming historical returns data"""
        var_calculator = VaRCalculator()
        
        portfolio = Mock()
        portfolio.get_total_value.return_value = Decimal("100000")
        
        # Initial returns dataset
        initial_returns = pd.DataFrame({
            "BTC/USDT": np.random.normal(0, 0.03, 200)
        })
        
        initial_var = var_calculator.calculate_historical_var(
            portfolio=portfolio,
            historical_returns=initial_returns,
            confidence=0.95
        )
        
        # Add new return data (simulating daily update)
        new_return = np.array([0.05])  # 5% positive return
        updated_returns = pd.concat([
            initial_returns,
            pd.DataFrame({"BTC/USDT": new_return}, 
                        index=[datetime.now()])
        ])
        
        updated_var = var_calculator.calculate_historical_var(
            portfolio=portfolio,
            historical_returns=updated_returns,
            confidence=0.95
        )
        
        # VaR should update with new data
        assert updated_var.portfolio_var != initial_var.portfolio_var
        assert updated_var.calculation_timestamp > initial_var.calculation_timestamp


class TestVaRMethodComparison:
    """Test comparison and validation across different VaR calculation methods"""
    
    def test_var_method_consistency(self):
        """Test that different VaR methods produce consistent relative results"""
        var_calculator = VaRCalculator()
        
        portfolio = Mock()
        portfolio.get_total_value.return_value = Decimal("100000")
        
        # Use same return data for all methods
        np.random.seed(42)
        returns_data = pd.DataFrame({
            "BTC/USDT": np.random.normal(0, 0.03, 500)
        })
        
        # Calculate VaR using all three methods
        historical_var = var_calculator.calculate_historical_var(
            portfolio=portfolio,
            historical_returns=returns_data,
            confidence=0.95
        )
        
        parametric_var = var_calculator.calculate_parametric_var(
            portfolio=portfolio,
            historical_returns=returns_data,
            confidence=0.95
        )
        
        monte_carlo_var = var_calculator.calculate_monte_carlo_var(
            portfolio=portfolio,
            historical_returns=returns_data,
            confidence=0.95,
            simulations=10000
        )
        
        # Methods should produce results in reasonable range of each other
        vars = [historical_var.portfolio_var, parametric_var.portfolio_var, monte_carlo_var.portfolio_var]
        
        min_var = min(vars)
        max_var = max(vars)
        
        # Maximum difference should be less than 50% (methods can vary but shouldn't be wildly different)
        relative_difference = (max_var - min_var) / min_var
        assert relative_difference < 0.5
        
        # All should be positive and reasonable
        for var_result in [historical_var, parametric_var, monte_carlo_var]:
            portfolio_value = Decimal("100000")
            var_percentage = var_result.portfolio_var / portfolio_value
            assert 0.005 <= var_percentage <= 0.30  # 0.5% to 30% seems reasonable range


class TestPortfolioRiskEngineIntegration:
    """Test integration of VaR calculator with portfolio risk engine"""
    
    def test_portfolio_risk_engine_initialization(self):
        """Test portfolio risk engine proper initialization"""
        risk_engine = PortfolioRiskEngine()
        
        assert hasattr(risk_engine, 'var_calculator')
        assert hasattr(risk_engine, 'calculate_portfolio_risk')
        assert hasattr(risk_engine, 'get_risk_summary')
    
    def test_comprehensive_risk_metrics_calculation(self):
        """Test calculation of comprehensive risk metrics beyond VaR"""
        risk_engine = PortfolioRiskEngine()
        
        # Mock portfolio
        portfolio = Mock()
        portfolio.get_total_value.return_value = Decimal("100000")
        
        # Mock returns data
        returns_data = pd.DataFrame({
            "BTC/USDT": np.random.normal(0, 0.03, 252),  # 1 year daily returns
            "ETH/USDT": np.random.normal(0, 0.04, 252)
        })
        
        risk_metrics = risk_engine.calculate_portfolio_risk(
            portfolio=portfolio,
            historical_returns=returns_data,
            calculate_all_metrics=True
        )
        
        # Validate comprehensive risk metrics
        assert isinstance(risk_metrics, RiskMetrics)
        assert hasattr(risk_metrics, 'var_95')
        assert hasattr(risk_metrics, 'var_99')
        assert hasattr(risk_metrics, 'expected_shortfall')
        assert hasattr(risk_metrics, 'volatility_annualized')
        assert hasattr(risk_metrics, 'maximum_drawdown')
        assert hasattr(risk_metrics, 'beta_to_market')
        assert hasattr(risk_metrics, 'correlation_breakdown_risk')
        
        # All metrics should be populated
        assert risk_metrics.var_95 > 0
        assert risk_metrics.var_99 > risk_metrics.var_95  # 99% VaR > 95% VaR
        assert risk_metrics.expected_shortfall > risk_metrics.var_95
        assert 0 < risk_metrics.volatility_annualized < 1  # Reasonable volatility range
    
    def test_risk_engine_performance_requirements(self):
        """Test risk engine meets performance requirements for real-time usage"""
        risk_engine = PortfolioRiskEngine()
        
        # Large portfolio for performance testing
        portfolio = Mock()
        portfolio.get_total_value.return_value = Decimal("1000000")
        
        # Large returns dataset
        np.random.seed(42)
        returns_data = pd.DataFrame({
            f"ASSET{i:02d}/USDT": np.random.normal(0, 0.02, 252)
            for i in range(50)  # 50 assets
        })
        
        # Performance test
        start_time = time.perf_counter()
        
        risk_metrics = risk_engine.calculate_portfolio_risk(
            portfolio=portfolio,
            historical_returns=returns_data
        )
        
        calculation_time = (time.perf_counter() - start_time) * 1000  # ms
        
        # Should complete within 20ms for real-time usage
        assert calculation_time < 20.0
        assert risk_metrics.calculation_time_ms < 20.0
        
        print(f"Risk Engine Performance: {calculation_time:.2f}ms for 50-asset portfolio")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])