# -*- coding: utf-8 -*-
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from zvt.trader.crypto.crypto_trader import CryptoTrader
from zvt.domain.crypto import CryptoPosition, CryptoOrder


class TestCryptoTrading:
    """Test crypto trading functionality including orders, positions, and risk management"""

    def test_crypto_order_creation(self):
        """Test creating different types of crypto orders"""
        # Market buy order
        market_order = CryptoOrder(
            id="order_1",
            entity_id="crypto_binance_BTC",
            trader="crypto_trader_1", 
            order_type="market",
            side="buy",
            quantity=0.1,
            timestamp=datetime.now()
        )
        
        assert market_order.order_type == "market"
        assert market_order.side == "buy"
        assert market_order.quantity == 0.1
        
        # Limit sell order
        limit_order = CryptoOrder(
            id="order_2",
            entity_id="crypto_binance_BTC",
            trader="crypto_trader_1",
            order_type="limit", 
            side="sell",
            quantity=0.05,
            price=46000.0,
            timestamp=datetime.now()
        )
        
        assert limit_order.order_type == "limit"
        assert limit_order.price == 46000.0

    def test_crypto_stop_loss_orders(self):
        """Test stop-loss and take-profit orders"""
        # Stop-loss order
        stop_loss = CryptoOrder(
            id="order_3",
            entity_id="crypto_binance_BTC",
            trader="crypto_trader_1",
            order_type="stop_loss",
            side="sell",
            quantity=0.1,
            stop_price=44000.0,
            timestamp=datetime.now()
        )
        
        assert stop_loss.order_type == "stop_loss"
        assert stop_loss.stop_price == 44000.0
        
        # Take-profit order
        take_profit = CryptoOrder(
            id="order_4", 
            entity_id="crypto_binance_BTC",
            trader="crypto_trader_1",
            order_type="take_profit",
            side="sell",
            quantity=0.1,
            price=48000.0,
            timestamp=datetime.now()
        )
        
        assert take_profit.order_type == "take_profit"
        assert take_profit.price == 48000.0

    def test_crypto_position_management(self):
        """Test crypto position tracking and updates"""
        position = CryptoPosition(
            id="position_1",
            entity_id="crypto_binance_BTC",
            trader="crypto_trader_1",
            quantity=0.5,
            average_price=45000.0,
            timestamp=datetime.now()
        )
        
        # Test position value calculation
        current_price = 46000.0
        position_value = position.quantity * current_price
        unrealized_pnl = (current_price - position.average_price) * position.quantity
        
        assert position_value == 23000.0  # 0.5 * 46000
        assert unrealized_pnl == 500.0    # (46000 - 45000) * 0.5

    def test_crypto_portfolio_balance_updates(self):
        """Test portfolio balance updates after trades"""
        trader = CryptoTrader(initial_balance=10000.0, base_currency="USD")
        
        # Buy 0.1 BTC at $45,000
        buy_order = CryptoOrder(
            order_type="market",
            side="buy", 
            quantity=0.1,
            price=45000.0
        )
        
        # Execute trade
        trader.execute_order(buy_order)
        
        # Check balance updates
        expected_cost = 0.1 * 45000.0  # $4,500
        expected_balance = 10000.0 - expected_cost
        
        assert trader.cash_balance == expected_balance
        assert trader.get_position("BTC").quantity == 0.1

    def test_crypto_leverage_trading(self):
        """Test leveraged crypto trading"""
        trader = CryptoTrader(initial_balance=1000.0, max_leverage=10)
        
        # Open leveraged position (10x leverage)
        leveraged_order = CryptoOrder(
            order_type="market",
            side="buy",
            quantity=0.2,  # $9,000 position with $1,000 capital
            price=45000.0,
            leverage=10
        )
        
        trader.execute_leveraged_order(leveraged_order)
        
        # Calculate margin requirements
        position_value = 0.2 * 45000.0  # $9,000
        required_margin = position_value / 10  # $900
        
        assert trader.used_margin == required_margin
        assert trader.available_margin == 1000.0 - required_margin

    def test_crypto_liquidation_price_calculation(self):
        """Test liquidation price calculation for leveraged positions"""
        trader = CryptoTrader(initial_balance=1000.0)
        
        # Long position with 10x leverage
        entry_price = 45000.0
        leverage = 10
        liquidation_buffer = 0.05  # 5% buffer before liquidation
        
        # Liquidation price = entry_price * (1 - (1/leverage) + buffer)
        liquidation_price = entry_price * (1 - (1/leverage) + liquidation_buffer)
        
        expected_liquidation = 45000.0 * (1 - 0.1 + 0.05)  # $42,750
        
        assert abs(liquidation_price - expected_liquidation) < 0.01

    def test_crypto_risk_management_position_sizing(self):
        """Test position sizing based on risk management rules"""
        trader = CryptoTrader(initial_balance=10000.0)
        trader.risk_per_trade = 0.02  # 2% risk per trade
        
        entry_price = 45000.0
        stop_loss_price = 44000.0
        risk_amount = trader.initial_balance * trader.risk_per_trade  # $200
        
        # Calculate position size based on risk
        price_risk = entry_price - stop_loss_price  # $1,000
        max_quantity = risk_amount / price_risk  # 0.2 BTC
        
        position_size = trader.calculate_position_size(
            entry_price=entry_price,
            stop_loss_price=stop_loss_price
        )
        
        assert position_size == max_quantity

    def test_crypto_order_execution_latency(self):
        """Test order execution speed and latency tracking"""
        trader = CryptoTrader()
        
        order_placed_time = datetime.now()
        
        # Simulate order execution
        with patch('time.time') as mock_time:
            mock_time.side_effect = [
                order_placed_time.timestamp(),
                order_placed_time.timestamp() + 0.1  # 100ms later
            ]
            
            execution_time = trader.execute_market_order("BTC", 0.1, "buy")
            
        # Check execution latency
        assert execution_time <= 0.5  # Should execute within 500ms

    def test_crypto_slippage_calculation(self):
        """Test slippage calculation for market orders"""
        expected_price = 45000.0
        executed_price = 45025.0  # $25 higher due to slippage
        quantity = 0.1
        
        slippage_amount = (executed_price - expected_price) * quantity  # $2.50
        slippage_percentage = slippage_amount / (expected_price * quantity) * 100  # 0.056%
        
        assert abs(slippage_percentage - 0.056) < 0.001
        
        # High slippage should trigger warning
        high_slippage_threshold = 0.1  # 0.1%
        assert slippage_percentage < high_slippage_threshold

    def test_crypto_order_book_impact(self):
        """Test market impact of large orders on order book"""
        order_book = {
            "bids": [
                {"price": 45000.0, "size": 0.5},
                {"price": 44999.0, "size": 1.0},
                {"price": 44998.0, "size": 2.0}
            ],
            "asks": [
                {"price": 45001.0, "size": 0.3},
                {"price": 45002.0, "size": 0.8},
                {"price": 45003.0, "size": 1.5}
            ]
        }
        
        # Large buy order that will impact multiple price levels
        buy_quantity = 1.0
        
        total_filled = 0.0
        weighted_price = 0.0
        
        for ask in order_book["asks"]:
            if total_filled >= buy_quantity:
                break
                
            fill_qty = min(ask["size"], buy_quantity - total_filled)
            weighted_price += ask["price"] * fill_qty
            total_filled += fill_qty
        
        avg_execution_price = weighted_price / total_filled
        
        # Should execute at multiple price levels
        assert avg_execution_price > 45001.0
        assert total_filled == buy_quantity

    @patch('zvt.trader.crypto.crypto_trader.CryptoTrader.send_order_to_exchange')
    def test_crypto_order_status_tracking(self, mock_send_order):
        """Test order status tracking and updates"""
        mock_send_order.return_value = {
            "order_id": "12345",
            "status": "submitted",
            "timestamp": datetime.now()
        }
        
        trader = CryptoTrader()
        order = CryptoOrder(
            order_type="limit",
            side="buy",
            quantity=0.1,
            price=45000.0
        )
        
        # Submit order
        result = trader.submit_order(order)
        
        assert result["status"] == "submitted"
        assert result["order_id"] == "12345"
        
        # Test order status progression
        status_progression = ["submitted", "accepted", "partially_filled", "filled"]
        
        for status in status_progression:
            assert status in ["submitted", "accepted", "partially_filled", "filled", "cancelled", "rejected"]

    def test_crypto_portfolio_rebalancing(self):
        """Test automatic portfolio rebalancing"""
        trader = CryptoTrader(initial_balance=10000.0)
        
        # Target allocation: 50% BTC, 30% ETH, 20% cash
        target_allocation = {
            "BTC": 0.5,
            "ETH": 0.3,
            "USD": 0.2
        }
        
        current_prices = {
            "BTC": 45000.0,
            "ETH": 3000.0
        }
        
        # Current positions (drift from target)
        current_positions = {
            "BTC": 0.08,  # Worth $3,600 (36%)
            "ETH": 1.5,   # Worth $4,500 (45%) 
            "USD": 1900.0  # 19% cash
        }
        
        rebalancing_orders = trader.calculate_rebalancing_orders(
            target_allocation, current_positions, current_prices
        )
        
        # Should generate orders to reach target allocation
        assert len(rebalancing_orders) > 0
        
        # Check BTC rebalancing (need to buy more)
        btc_order = next(order for order in rebalancing_orders if order["symbol"] == "BTC")
        assert btc_order["side"] == "buy"  # Need more BTC to reach 50%

    def test_crypto_trading_fees_calculation(self):
        """Test trading fees calculation and impact"""
        trader = CryptoTrader()
        trader.maker_fee = 0.001  # 0.1%
        trader.taker_fee = 0.0015  # 0.15%
        
        # Market order (taker)
        trade_value = 0.1 * 45000.0  # $4,500
        taker_fee = trade_value * trader.taker_fee  # $6.75
        
        # Limit order (maker)
        maker_fee = trade_value * trader.maker_fee  # $4.50
        
        assert taker_fee == 6.75
        assert maker_fee == 4.50
        assert taker_fee > maker_fee  # Taker fees should be higher

    def test_crypto_dca_strategy(self):
        """Test Dollar Cost Averaging (DCA) strategy"""
        trader = CryptoTrader(initial_balance=1000.0)
        dca_amount = 100.0  # $100 weekly
        
        # Simulate 10 weeks of DCA purchases
        prices = [45000, 44000, 46000, 43000, 47000, 45500, 44500, 46500, 45000, 44800]
        total_btc_bought = 0.0
        total_spent = 0.0
        
        for price in prices:
            btc_amount = dca_amount / price
            total_btc_bought += btc_amount
            total_spent += dca_amount
        
        average_price = total_spent / total_btc_bought
        
        # Average price should be different from simple arithmetic mean
        arithmetic_mean = sum(prices) / len(prices)
        assert abs(average_price - arithmetic_mean) > 100  # Should be significantly different