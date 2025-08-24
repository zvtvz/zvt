# -*- coding: utf-8 -*-
"""
Trading Portfolio Models
========================

Portfolio and Position models for risk calculations and trading operations.
These are lightweight models focused on trading and risk management.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Any


@dataclass 
class Position:
    """Position model for trading and risk calculations"""
    symbol: str
    quantity: Decimal 
    avg_price: Decimal
    current_price: Decimal
    exchange: str = "binance"


@dataclass
class Portfolio:
    """Portfolio model for trading and risk calculations"""
    positions: Dict[str, Position] = field(default_factory=dict)
    cash_balance: Decimal = Decimal("0")
    base_currency: str = "USDT"
    
    def get_total_value(self) -> Decimal:
        """Calculate total portfolio value"""
        total = self.cash_balance
        for position in self.positions.values():
            total += position.quantity * position.current_price
        return total
    
    def get_positions(self) -> Dict[str, Position]:
        """Get portfolio positions"""
        return self.positions
    
    def get_strategy_positions(self) -> Dict[str, List[str]]:
        """Get positions grouped by strategy (mock implementation for testing)"""
        return {
            "momentum_btc": ["BTC/USDT"],
            "mean_reversion_eth": ["ETH/USDT"], 
            "arbitrage_multi": ["ADA/USDT", "DOT/USDT"]
        }