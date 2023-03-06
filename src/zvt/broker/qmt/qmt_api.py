# -*- coding: utf-8 -*-
import pandas as pd
from xtquant import xtdata

from zvt.contract import IntervalLevel, AdjustType
from zvt.contract.api import decode_entity_id
from zvt.utils import to_time_str


# http://docs.thinktrader.net/vip/QMT-Simple/


def _to_qmt_code(entity_id):
    _, exchange, code = decode_entity_id(entity_id=entity_id)
    return f"{code}.{exchange.upper()}"


def _to_qmt_dividend_type(adjust_type: AdjustType):
    if adjust_type == AdjustType.qfq:
        return "front"
    elif adjust_type == AdjustType.hfq:
        return "back"
    else:
        return "none"


def get_kdata(
    entity_id,
    start_timestamp,
    end_timestamp,
    level=IntervalLevel.LEVEL_1DAY,
    adjust_type=AdjustType.qfq,
):
    code = _to_qmt_code(entity_id=entity_id)
    period = level.value
    # 保证qmt先下载数据到本地
    xtdata.download_history_data(stock_code=code, period=period, start_time="", end_time="")
    records = xtdata.get_market_data(
        stock_list=[code],
        period=period,
        start_time=to_time_str(start_timestamp, fmt="YYYYMMDDHHmmss"),
        end_time=to_time_str(end_timestamp, fmt="YYYYMMDDHHmmss"),
        dividend_type=_to_qmt_dividend_type(adjust_type=adjust_type),
        fill_data=False,
    )

    dfs = []
    for col in records:
        df = records[col].T
        df.columns = [col]
        dfs.append(df)
    return pd.concat(dfs, axis=1)


if __name__ == "__main__":
    print(get_kdata(entity_id="stock_sz_000338", start_timestamp="20230101", end_timestamp="20230329"))
