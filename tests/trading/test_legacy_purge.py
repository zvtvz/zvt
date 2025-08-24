# -*- coding: utf-8 -*-
"""
TDD LEGACY PURGE: RED Phase Tests
Tests expecting clean Hatchet-only architecture with no legacy components

Following TDD methodology: RED-GREEN-REFACTOR
This test suite validates the target architecture after legacy removal.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, Mock

from src.zvt.trading.crypto_trading_engine import CryptoTradingEngine, OrderRequest
from src.zvt.trading.models import Order, OrderSide, OrderType
from src.zvt.domain.crypto.crypto_trading import PositionSide


class TestCleanArchitecture:
    """
    TDD Legacy Purge: Tests for clean Hatchet-only architecture
    These tests MUST fail initially (RED phase) until legacy code is removed
    """

    def test_no_enable_hatchet_parameter_in_constructor(self):
        """
        RED Phase: Constructor should not have enable_hatchet parameter
        Target: Hatchet is always enabled, no conditional logic needed
        """
        # MUST fail initially - constructor still has enable_hatchet parameter
        try:
            # This should work without enable_hatchet parameter
            engine = CryptoTradingEngine(exchanges=["binance", "okx"])
            # Hatchet should always be enabled by default
            assert hasattr(engine, 'hatchet_integration')
            assert engine.hatchet_integration is not None
        except TypeError as e:
            # Expected failure in RED phase - constructor still requires enable_hatchet
            pytest.fail(f"Constructor still has enable_hatchet parameter: {e}")

    def test_no_legacy_error_handler_component(self):
        """
        RED Phase: TradingErrorHandler should not exist
        Target: All error handling via Hatchet workflows
        """
        engine = CryptoTradingEngine()
        
        # These legacy components should NOT exist
        assert not hasattr(engine, 'error_handler')
        assert 'TradingErrorHandler' not in str(type(engine).__dict__)
        
        # Error handling should be via Hatchet
        with patch.object(engine.hatchet_integration, 'handle_error') as mock_handle:
            mock_handle.return_value = {"status": "handled", "retry_count": 1}
            result = engine.handle_trading_error("CONNECTION_ERROR", {"exchange": "binance"})
            assert result["status"] == "handled"
            mock_handle.assert_called_once()

    def test_no_legacy_routing_strategy_component(self):
        """
        RED Phase: ExchangeRoutingStrategy should not exist
        Target: All routing via Hatchet workflows
        """
        engine = CryptoTradingEngine()
        
        # Legacy routing should NOT exist
        assert not hasattr(engine, 'routing_strategy')
        assert 'ExchangeRoutingStrategy' not in str(type(engine).__dict__)
        
        # Routing should be via Hatchet workflows
        order = Order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=Decimal("1.0"),
            order_type=OrderType.MARKET
        )
        
        with patch.object(engine.hatchet_integration, 'route_order') as mock_route:
            mock_route.return_value = {"exchange": "binance", "routing_reason": "workflow_optimized"}
            result = engine.route_order(order)
            assert result["exchange"] == "binance"
            mock_route.assert_called_once()

    def test_no_legacy_performance_tracking_components(self):
        """
        RED Phase: PerformanceTracker, PositionCache, PnLCalculator should not exist
        Target: All tracking via Hatchet metrics
        """
        engine = CryptoTradingEngine()
        
        # Legacy performance components should NOT exist
        assert not hasattr(engine, '_performance_tracker')
        assert not hasattr(engine.position_manager, '_position_cache')
        assert not hasattr(engine.position_manager, '_pnl_calculator')
        assert not hasattr(engine.position_manager, '_performance_tracker')
        
        # Performance tracking should be via Hatchet
        with patch.object(engine.hatchet_integration, 'get_performance_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "order_latency_p99": 45.2,
                "routing_efficiency": 0.94,
                "hatchet_managed": True
            }
            metrics = engine.get_performance_metrics()
            assert metrics["hatchet_managed"] == True
            assert "order_latency_p99" in metrics

    def test_no_conditional_hasattr_checks(self):
        """
        RED Phase: No hasattr() checks for legacy components
        Target: Clean code without conditional legacy support
        """
        engine = CryptoTradingEngine()
        
        # Get all methods that might have hasattr checks
        import inspect
        engine_source = inspect.getsource(type(engine))
        position_manager_source = inspect.getsource(type(engine.position_manager))
        
        # Should not contain legacy hasattr checks
        legacy_checks = [
            "hasattr(self, 'routing_strategy')",
            "hasattr(self, 'error_handler')", 
            "hasattr(self, '_performance_tracker')",
            "hasattr(self, '_position_cache')",
            "hasattr(self, '_pnl_calculator')"
        ]
        
        for check in legacy_checks:
            assert check not in engine_source, f"Found legacy hasattr check: {check}"
            assert check not in position_manager_source, f"Found legacy hasattr check: {check}"

    def test_simplified_constructor_signature(self):
        """
        RED Phase: Constructor should have simplified signature
        Target: Remove all legacy configuration parameters
        """
        import inspect
        
        # Get constructor signature
        sig = inspect.signature(CryptoTradingEngine.__init__)
        params = list(sig.parameters.keys())
        
        # Should only have essential parameters
        expected_params = ['self', 'exchanges']
        legacy_params = ['routing_config', 'cache_config', 'enable_hatchet']
        
        for legacy_param in legacy_params:
            assert legacy_param not in params, f"Legacy parameter still exists: {legacy_param}"
        
        # Should be able to create with minimal parameters
        engine = CryptoTradingEngine(exchanges=["binance"])
        assert engine is not None

    def test_workflow_methods_without_hatchet_validation(self):
        """
        RED Phase: Workflow methods should not validate Hatchet enablement
        Target: Hatchet is always enabled, no validation needed
        """
        engine = CryptoTradingEngine()
        
        # These methods should work without "Hatchet integration not enabled" errors
        order_request = OrderRequest(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0"),
            portfolio_id="test_portfolio"
        )
        
        with patch.object(engine.hatchet_integration, 'execute_order_workflow') as mock_exec:
            mock_exec.return_value = {"success": True, "workflow_id": "test_123"}
            
            # Should work without validation checks
            result = engine.execute_order_workflow(order_request)
            assert result["success"] == True

    def test_clean_import_structure(self):
        """
        RED Phase: Legacy classes should not be importable
        Target: Clean module structure without legacy components
        """
        # These legacy classes should not exist for import
        legacy_classes = [
            'TradingErrorHandler',
            'ExchangeRoutingStrategy', 
            'PerformanceTracker',
            'PositionCache',
            'PnLCalculator'
        ]
        
        from src.zvt.trading import crypto_trading_engine
        module_attrs = dir(crypto_trading_engine)
        
        for legacy_class in legacy_classes:
            assert legacy_class not in module_attrs, f"Legacy class still exists: {legacy_class}"

    def test_position_manager_simplified_initialization(self):
        """
        RED Phase: PositionManager should have simplified initialization
        Target: No conditional logic based on enable_hatchet
        """
        engine = CryptoTradingEngine()
        
        # PositionManager should be initialized without legacy components
        pm = engine.position_manager
        
        # Should not have legacy attributes
        legacy_attributes = ['_position_cache', '_pnl_calculator', '_performance_tracker']
        for attr in legacy_attributes:
            assert not hasattr(pm, attr), f"PositionManager still has legacy attribute: {attr}"
        
        # Should have Hatchet integration
        assert hasattr(pm, 'trading_engine')
        assert pm.trading_engine.hatchet_integration is not None


class TestHatchetOnlyFunctionality:
    """
    TDD Legacy Purge: Tests for Hatchet-only functionality
    Validates that all features work through Hatchet workflows
    """

    def test_order_execution_via_hatchet_only(self):
        """
        RED Phase: Order execution should only use Hatchet workflows
        Target: No legacy routing or error handling paths
        """
        engine = CryptoTradingEngine()
        
        order_request = OrderRequest(
            symbol="ETH/USDT",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=Decimal("2.5"),
            price=Decimal("3000.0"),
            portfolio_id="test_portfolio"
        )
        
        with patch.object(engine.hatchet_integration, 'execute_order_workflow') as mock_workflow:
            mock_workflow.return_value = {
                "success": True,
                "workflow_id": "order_wf_12345",
                "status": "submitted",
                "resilience_handled_by": "hatchet"
            }
            
            result = engine.execute_order_workflow(order_request)
            
            assert result["success"] == True
            assert result["resilience_handled_by"] == "hatchet"
            mock_workflow.assert_called_once_with(order_request)

    def test_risk_management_via_hatchet_only(self):
        """
        RED Phase: Risk management should only use Hatchet workflows
        Target: No legacy risk calculation or circuit breaker logic
        """
        engine = CryptoTradingEngine()
        
        with patch.object(engine.hatchet_integration, 'start_risk_monitoring_workflow') as mock_risk:
            mock_risk.return_value = {
                "workflow_id": "risk_monitor_67890",
                "status": "active",
                "risk_checks_enabled": ["position_limits", "var_monitoring", "correlation_checks"]
            }
            
            result = engine.start_risk_monitoring_workflow(
                portfolio_id="risk_test_portfolio",
                check_interval=30,
                var_threshold=0.05
            )
            
            assert result["status"] == "active"
            assert len(result["risk_checks_enabled"]) == 3
            mock_risk.assert_called_once()

    def test_portfolio_analytics_via_hatchet_only(self):
        """
        RED Phase: Portfolio analytics should only use Hatchet workflows
        Target: No legacy PnL calculation or performance tracking
        """
        engine = CryptoTradingEngine()
        
        with patch.object(engine.hatchet_integration, 'start_rebalancing_workflow') as mock_rebal:
            mock_rebal.return_value = {
                "workflow_id": "rebalancing_98765",
                "status": "analyzing",
                "target_allocations": {"BTC": 0.6, "ETH": 0.3, "USDT": 0.1}
            }
            
            result = engine.start_rebalancing_workflow(
                portfolio_id="analytics_test_portfolio",
                target_allocations={"BTC": 0.6, "ETH": 0.3, "USDT": 0.1}
            )
            
            assert result["status"] == "analyzing"
            assert result["target_allocations"]["BTC"] == 0.6
            mock_rebal.assert_called_once()


# RED Phase: These tests will fail until legacy code is removed
# Remove this comment when moving to GREEN phase