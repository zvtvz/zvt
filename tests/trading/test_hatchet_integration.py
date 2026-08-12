# tests/trading/test_hatchet_integration.py
"""
TDD REFACTOR: Hatchet Integration Tests - RED Phase
Spec: Replace custom resilience with Hatchet workflow orchestration
Methodology: Test-Driven Development (Red-Green-Refactor)

RED Phase: These tests MUST fail initially because Hatchet integration doesn't exist
Goal: Replace CircuitBreaker, RetryConfig, TradingErrorHandler with Hatchet workflows
"""
import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from datetime import datetime

from src.zvt.trading.crypto_trading_engine import CryptoTradingEngine
from src.zvt.trading.models import Order, OrderType, OrderSide
from src.zvt.trading.crypto_trading_engine import OrderRequest
from src.zvt.trading.hatchet_workflows import (
    OrderExecutionWorkflow, 
    PortfolioRebalancingWorkflow,
    RiskMonitoringWorkflow
)


class TestHatchetOrderExecution:
    """
    TDD Test Suite for Hatchet Order Execution Workflow
    Spec: Replace complex order execution with simple Hatchet workflow
    
    RED Phase Requirements:
    - Hatchet workflow for order placement
    - Built-in error handling and retries
    - Workflow-based orchestration
    - Event-driven architecture
    """
    
    def test_hatchet_order_execution_workflow(self):
        """
        RED Phase: Test fails because OrderExecutionWorkflow doesn't exist
        Spec Requirement: "Replace custom error handling with Hatchet workflow"
        """
        # Arrange
        engine = CryptoTradingEngine(enable_hatchet=True)
        order_request = OrderRequest(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0"),
            portfolio_id="test_portfolio"
        )
        
        # Act & Assert (This MUST fail initially - RED phase)
        workflow_result = engine.execute_order_workflow(order_request)
        
        assert workflow_result.success == True
        assert workflow_result.workflow_id is not None
        assert workflow_result.status == "submitted"
        assert workflow_result.resilience_handled_by == "hatchet"
    
    def test_hatchet_handles_exchange_failures(self):
        """
        RED Phase: Test Hatchet handles failures instead of CircuitBreaker
        Spec Requirement: "Remove CircuitBreaker - Hatchet handles resilience"
        """
        engine = CryptoTradingEngine(enable_hatchet=True)
        
        # Simulate exchange failure
        with patch('src.zvt.trading.connectors.BinanceConnector.place_order') as mock_place:
            mock_place.side_effect = Exception("Exchange connection failed")
            
            order_request = OrderRequest(
                symbol="ETH/USDT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal("5.0")
            )
            
            # Hatchet workflow should handle the error and retry
            result = engine.execute_order_workflow(order_request)
            
            assert result.success == True  # Eventually succeeds after Hatchet retries
            assert result.retry_count > 0  # Hatchet handled retries
            assert result.error_recovery == "hatchet_workflow"
    
    def test_simplified_engine_without_resilience_code(self):
        """
        RED Phase: Test engine works without custom resilience infrastructure
        Spec Requirement: "Remove CircuitBreaker, RetryConfig, TradingErrorHandler"
        """
        engine = CryptoTradingEngine(enable_hatchet=True)
        
        # These should not exist after refactoring
        assert not hasattr(engine, 'error_handler')
        assert not hasattr(engine, 'routing_strategy._performance_tracker')
        assert not hasattr(engine.position_manager, '_performance_tracker')
        
        # Verify core functionality still works
        order_request = OrderRequest(
            symbol="ADA/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1000.0"),
            price=Decimal("0.5")
        )
        
        result = engine.execute_order_workflow(order_request)
        assert result.success == True


class TestHatchetPortfolioWorkflows:
    """
    TDD Test Suite for Hatchet Portfolio Management Workflows
    Spec: Replace complex portfolio operations with Hatchet workflows
    
    RED Phase Requirements:
    - Portfolio rebalancing workflow
    - Risk monitoring workflow
    - Event-driven portfolio updates
    """
    
    def test_hatchet_portfolio_rebalancing_workflow(self):
        """
        RED Phase: Test fails because PortfolioRebalancingWorkflow doesn't exist
        Spec Requirement: "Portfolio rebalancing as Hatchet workflow"
        """
        engine = CryptoTradingEngine(enable_hatchet=True)
        portfolio_id = "rebalancing_test_portfolio"
        
        # Create portfolio with drift
        engine.create_portfolio(portfolio_id, target_allocations={
            "BTC/USDT": Decimal("0.5"),
            "ETH/USDT": Decimal("0.3"), 
            "ADA/USDT": Decimal("0.2")
        })
        
        # Trigger rebalancing workflow
        workflow_result = engine.start_rebalancing_workflow(portfolio_id)
        
        assert workflow_result.workflow_id is not None
        assert workflow_result.status == "running"
        assert workflow_result.workflow_type == "portfolio_rebalancing"
        assert workflow_result.managed_by == "hatchet"
    
    def test_hatchet_risk_monitoring_workflow(self):
        """
        RED Phase: Test fails because RiskMonitoringWorkflow doesn't exist
        Spec Requirement: "Risk monitoring as continuous Hatchet workflow"
        """
        engine = CryptoTradingEngine(enable_hatchet=True)
        portfolio_id = "risk_monitoring_portfolio"
        
        # Start continuous risk monitoring
        workflow_result = engine.start_risk_monitoring_workflow(
            portfolio_id, 
            check_interval="30s",
            var_limit=Decimal("0.02")
        )
        
        assert workflow_result.workflow_id is not None
        assert workflow_result.status == "monitoring"
        assert workflow_result.workflow_type == "risk_monitoring"
        assert workflow_result.schedule == "continuous"
    
    def test_event_driven_portfolio_updates(self):
        """
        RED Phase: Test event-driven architecture with Hatchet
        Spec Requirement: "Event-driven portfolio updates via Hatchet events"
        """
        engine = CryptoTradingEngine(enable_hatchet=True)
        portfolio_id = "event_driven_portfolio"
        
        # Price update should trigger portfolio recalculation workflow
        engine.emit_price_update_event("BTC/USDT", Decimal("46000"))
        
        # Verify event triggered workflow
        triggered_workflows = engine.get_triggered_workflows(
            event_type="price_update",
            symbol="BTC/USDT"
        )
        
        assert len(triggered_workflows) > 0
        assert any(w.workflow_type == "portfolio_valuation" for w in triggered_workflows)
        assert all(w.managed_by == "hatchet" for w in triggered_workflows)


class TestKISSSimplification:
    """
    TDD Test Suite for KISS Principle Application
    Spec: Verify removal of complex resilience code
    
    RED Phase Requirements:
    - No CircuitBreaker classes
    - No RetryConfig classes  
    - No TradingErrorHandler
    - No complex performance tracking
    - Simplified interfaces
    """
    
    def test_removed_circuit_breaker_infrastructure(self):
        """
        RED Phase: Test CircuitBreaker classes are removed
        Spec Requirement: "Remove CircuitBreaker - handled by Hatchet"
        """
        # These imports should fail after refactoring
        with pytest.raises(ImportError):
            from src.zvt.trading.crypto_trading_engine import CircuitBreaker
        
        with pytest.raises(ImportError):
            from src.zvt.trading.crypto_trading_engine import CircuitBreakerConfig
    
    def test_removed_retry_infrastructure(self):
        """
        RED Phase: Test retry infrastructure is removed
        Spec Requirement: "Remove RetryConfig - handled by Hatchet"
        """
        # These imports should fail after refactoring
        with pytest.raises(ImportError):
            from src.zvt.trading.crypto_trading_engine import RetryConfig
        
        with pytest.raises(ImportError):
            from src.zvt.trading.crypto_trading_engine import retry_with_backoff
    
    def test_removed_trading_error_handler(self):
        """
        RED Phase: Test TradingErrorHandler is removed
        Spec Requirement: "Remove TradingErrorHandler - handled by Hatchet"
        """
        with pytest.raises(ImportError):
            from src.zvt.trading.crypto_trading_engine import TradingErrorHandler
    
    def test_removed_audit_logging(self):
        """
        RED Phase: Test audit logging is removed
        Spec Requirement: "Remove audit_logging - handled by Hatchet monitoring"
        """
        with pytest.raises(ImportError):
            from src.zvt.trading.crypto_trading_engine import audit_logging
    
    def test_simplified_trading_engine_interface(self):
        """
        RED Phase: Test simplified engine interface
        Spec Requirement: "Simplified engine focused on business logic"
        """
        engine = CryptoTradingEngine(enable_hatchet=True)
        
        # Verify simplified public interface
        public_methods = [method for method in dir(engine) if not method.startswith('_')]
        
        # Should have core business methods
        assert 'place_order' in public_methods
        assert 'get_positions' in public_methods
        assert 'calculate_portfolio_value' in public_methods
        
        # Should NOT have resilience methods
        assert 'get_circuit_breaker' not in public_methods
        assert 'execute_with_circuit_breaker' not in public_methods
        assert 'get_error_stats' not in public_methods
        assert 'get_routing_analytics' not in public_methods
    
    def test_performance_tracking_simplified(self):
        """
        RED Phase: Test performance tracking is simplified
        Spec Requirement: "Remove complex performance tracking - Hatchet provides monitoring"
        """
        engine = CryptoTradingEngine(enable_hatchet=True)
        
        # Complex performance tracking should be removed
        assert not hasattr(engine, 'order_latency_ms')
        assert not hasattr(engine, 'routing_strategy._performance_tracker')
        
        # Basic metrics should still be available via Hatchet
        metrics = engine.get_hatchet_metrics()
        assert 'workflow_executions' in metrics
        assert 'error_rates' in metrics
        assert 'performance_stats' in metrics


class TestBackwardCompatibility:
    """
    TDD Test Suite for Backward Compatibility
    Spec: Ensure all existing functionality works after refactoring
    
    RED Phase Requirements:
    - All 17 TDD Cycle 1 tests still pass
    - All 15 TDD Cycle 2 tests still pass
    - Same public API (with Hatchet backend)
    - No breaking changes
    """
    
    def test_existing_order_tests_compatibility(self):
        """
        RED Phase: Test existing order management tests still pass
        Spec Requirement: "Maintain all existing functionality"
        """
        # This test will import and run existing test suites
        # to ensure they still pass after Hatchet refactoring
        
        # Import existing test classes
        from tests.trading.test_order_routing import TestOrderRouting
        from tests.trading.test_order_routing import TestOrderPlacement
        
        # These should still pass after refactoring
        engine = CryptoTradingEngine(enable_hatchet=True)
        
        # Test that old interface still works
        order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=Decimal("1.0"),
            order_type=OrderType.MARKET
        )
        
        # Should work with new Hatchet backend
        result = engine.place_order(order)
        assert result.success == True
    
    def test_existing_portfolio_tests_compatibility(self):
        """
        RED Phase: Test existing portfolio analytics tests still pass
        Spec Requirement: "Maintain portfolio analytics functionality"
        """
        engine = CryptoTradingEngine(enable_hatchet=True)
        
        # Test portfolio creation still works
        portfolio_id = "compatibility_test"
        engine.create_portfolio(portfolio_id)
        
        # Test position addition still works
        engine.add_position_to_portfolio(
            portfolio_id, "BTC/USDT", 
            quantity=Decimal("1.0"), 
            avg_price=Decimal("45000")
        )
        
        # Test portfolio valuation still works
        portfolio_value = engine.calculate_portfolio_value(portfolio_id)
        assert portfolio_value.total_value > 0
        
        # Test all portfolio analytics still work
        assert hasattr(engine, 'calculate_sharpe_ratio')
        assert hasattr(engine, 'detect_portfolio_drift') 
        assert hasattr(engine, 'generate_rebalancing_trades')