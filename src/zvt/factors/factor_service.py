# -*- coding: utf-8 -*-
import pandas as pd

from zvt.contract import zvt_context
from zvt.domain import Stock
from zvt.factors.factor_models import FactorRequestModel
from zvt.factors.technical_factor import TechnicalFactor
from zvt.trader import TradingSignalType


def query_factor_result(factor_request_model: FactorRequestModel):
    factor_name = factor_request_model.factor_name
    entity_ids = factor_request_model.entity_ids
    level = factor_request_model.level

    factor: TechnicalFactor = zvt_context.factor_cls_registry[factor_name](
        provider="em",
        entity_provider="em",
        entity_schema=Stock,
        entity_ids=entity_ids,
        level=level,
        start_timestamp=factor_request_model.start_timestamp,
    )
    df = factor.get_trading_signal_df()
    df = df.reset_index(drop=False)

    def to_trading_signal(order_type):
        if order_type is None:
            return None
        if order_type:
            return TradingSignalType.open_long
        if not order_type:
            return TradingSignalType.close_long

    df = df.rename(columns={"timestamp": "happen_timestamp"})
    df["due_timestamp"] = df["happen_timestamp"] + pd.Timedelta(seconds=level.to_second())
    df["trading_signal_type"] = df["filter_result"].apply(lambda x: to_trading_signal(x))

    print(df)
    return df.to_dict(orient="records")


# the __all__ is generated
__all__ = ["query_factor_result"]
