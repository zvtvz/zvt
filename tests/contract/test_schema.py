# -*- coding: utf-8 -*-
from zvt.domain import Stock


def test_trading_time():
    assert Stock.in_real_trading_time(timestamp="2024-09-02 08:00") is False
    assert Stock.in_real_trading_time(timestamp="2024-09-02 09:20") is True
    assert Stock.in_real_trading_time(timestamp="2024-09-02 09:30") is True
    assert Stock.in_real_trading_time(timestamp="2024-09-02 11:00") is True
    assert Stock.in_real_trading_time(timestamp="2024-09-02 11:30") is True
    assert Stock.in_real_trading_time(timestamp="2024-09-02 11:40") is False
    assert Stock.in_real_trading_time(timestamp="2024-09-02 13:00") is True
    assert Stock.in_real_trading_time(timestamp="2024-09-02 15:00") is True
    assert Stock.in_real_trading_time(timestamp="2024-09-02 15:10") is False
    assert Stock.in_real_trading_time(timestamp="2024-09-02 16:10") is False

    assert Stock.in_trading_time(timestamp="2024-09-02 08:00") is False
    assert Stock.in_trading_time(timestamp="2024-09-02 09:20") is True
    assert Stock.in_trading_time(timestamp="2024-09-02 09:30") is True
    assert Stock.in_trading_time(timestamp="2024-09-02 11:00") is True
    assert Stock.in_trading_time(timestamp="2024-09-02 11:30") is True
    assert Stock.in_trading_time(timestamp="2024-09-02 11:40") is True
    assert Stock.in_trading_time(timestamp="2024-09-02 13:00") is True
    assert Stock.in_trading_time(timestamp="2024-09-02 15:00") is True
    assert Stock.in_trading_time(timestamp="2024-09-02 15:10") is False
    assert Stock.in_trading_time(timestamp="2024-09-02 16:10") is False
