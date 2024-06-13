# -*- coding: utf-8 -*-
from zvt.contract import IntervalLevel
from zvt.factors.ma.ma_factor import CrossMaFactor

from zvt.contract.factor import TargetType
from zvt.factors.macd.macd_factor import BullFactor
from ..context import init_test_context

init_test_context()


def test_cross_ma_select_targets():
    entity_ids = ["stock_sz_000338"]
    start_timestamp = "2018-01-01"
    end_timestamp = "2019-06-30"
    factor = CrossMaFactor(
        provider="joinquant",
        entity_ids=entity_ids,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        keep_window=10,
        windows=[5, 10],
        need_persist=False,
        level=IntervalLevel.LEVEL_1DAY,
        adjust_type="hfq",
    )
    assert "stock_sz_000338" in factor.get_targets(timestamp="2018-01-19")


def test_bull_select_targets():
    factor = BullFactor(
        start_timestamp="2019-01-01", end_timestamp="2019-06-10", level=IntervalLevel.LEVEL_1DAY, provider="joinquant"
    )

    targets = factor.get_targets(timestamp="2019-05-08", target_type=TargetType.positive)

    assert "stock_sz_000338" not in targets
    assert "stock_sz_002572" not in targets

    targets = factor.get_targets("2019-05-08", target_type=TargetType.negative)
    assert "stock_sz_000338" in targets
    assert "stock_sz_002572" not in targets

    factor.move_on(timeout=0)

    targets = factor.get_targets(timestamp="2019-06-19", target_type=TargetType.positive)

    assert "stock_sz_000338" in targets

    assert "stock_sz_002572" not in targets
