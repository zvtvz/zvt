# -*- coding: utf-8 -*-
import logging
import time

import numpy as np
import pandas as pd
from xtquant import xtdata

from zvt.contract import IntervalLevel, AdjustType
from zvt.contract.api import decode_entity_id, df_to_db, get_db_session
from zvt.domain import StockQuote, Stock
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_time_str, current_date, to_pd_timestamp, now_pd_timestamp

# https://dict.thinktrader.net/nativeApi/start_now.html?id=e2M5nZ

logger = logging.getLogger(__name__)


def _to_qmt_code(entity_id):
    _, exchange, code = decode_entity_id(entity_id=entity_id)
    return f"{code}.{exchange.upper()}"


def _to_zvt_entity_id(qmt_code):
    code, exchange = qmt_code.split(".")
    exchange = exchange.lower()
    return f"stock_{exchange}_{code}"


def _to_qmt_dividend_type(adjust_type: AdjustType):
    if adjust_type == AdjustType.qfq:
        return "front"
    elif adjust_type == AdjustType.hfq:
        return "back"
    else:
        return "none"


def _qmt_instrument_detail_to_stock(stock_detail):
    exchange = stock_detail["ExchangeID"].lower()
    code = stock_detail["InstrumentID"]
    name = stock_detail["InstrumentName"]
    list_date = to_pd_timestamp(stock_detail["OpenDate"])
    end_date = to_pd_timestamp(stock_detail["ExpireDate"])
    pre_close = stock_detail["PreClose"]
    limit_up_price = stock_detail["UpStopPrice"]
    limit_down_price = stock_detail["DownStopPrice"]
    float_volume = stock_detail["FloatVolume"]
    total_volume = stock_detail["TotalVolume"]

    entity_id = f"stock_{exchange}_{code}"

    return {
        "id": entity_id,
        "entity_id": entity_id,
        "timestamp": list_date,
        "entity_type": "stock",
        "exchange": exchange,
        "code": code,
        "name": name,
        "list_date": list_date,
        "end_date": end_date,
        "pre_close": pre_close,
        "limit_up_price": limit_up_price,
        "limit_down_price": limit_down_price,
        "float_volume": float_volume,
        "total_volume": total_volume,
    }


def get_qmt_stocks():
    return xtdata.get_stock_list_in_sector("沪深A股")


def get_entity_list():
    stocks = get_qmt_stocks()
    entity_list = []

    for stock in stocks:
        stock_detail = xtdata.get_instrument_detail(stock, False)
        if stock_detail:
            entity_list.append(_qmt_instrument_detail_to_stock(stock_detail))
        else:
            code, exchange = stock.split(".")
            exchange = exchange.lower()
            entity_id = f"stock_{exchange}_{code}"
            # get from provider exchange
            datas = Stock.query_data(provider="em", entity_id=entity_id, return_type="dict")
            if datas:
                entity = datas[0]
            else:
                entity = {
                    "id": _to_zvt_entity_id(stock),
                    "entity_id": entity_id,
                    "entity_type": "stock",
                    "exchange": exchange,
                    "code": code,
                    "name": "未获取",
                }

            # xtdata.download_financial_data(stock_list=[stock], table_list=["Capital"])
            capital_datas = xtdata.get_financial_data(
                [stock],
                table_list=["Capital"],
                report_type="report_time",
            )
            df = capital_datas[stock]["Capital"]
            if pd_is_not_null(df):
                latest_data = df.iloc[-1]
                entity["float_volume"] = latest_data["circulating_capital"]
                entity["total_volume"] = latest_data["total_capital"]

            tick = xtdata.get_full_tick(code_list=[stock])
            if tick and tick[stock]:
                if code.startswith("300") or code.startswith("688"):
                    limit_up_price = tick[stock]["lastClose"] * 1.2
                    limit_down_price = tick[stock]["lastClose"] * 0.8
                else:
                    limit_up_price = tick[stock]["lastClose"] * 1.1
                    limit_down_price = tick[stock]["lastClose"] * 0.9
                entity["limit_up_price"] = round(limit_up_price, 2)
                entity["limit_down_price"] = round(limit_down_price, 2)
            entity_list.append(entity)

    return pd.DataFrame.from_records(data=entity_list)


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


def tick_to_quote():
    entity_list = get_entity_list()
    entity_df = entity_list[
        ["entity_id", "code", "name", "limit_up_price", "limit_down_price", "float_volume", "total_volume"]
    ]
    entity_df = entity_df.set_index("entity_id", drop=False)

    def calculate_limit_up_amount(row):
        if row["is_limit_up"]:
            return row["price"] * row["bidVol"][0] * 100
        else:
            return None

    def calculate_limit_down_amount(row):
        if row["is_limit_down"]:
            return row["price"] * row["askVol"][0] * 100
        else:
            return None

    def on_data(datas, stock_df=entity_df):
        start_time = time.time()

        tick_df = pd.DataFrame.from_records(data=[datas[code] for code in datas], index=list(datas.keys()))
        tick_df.index = tick_df.index.map(_to_zvt_entity_id)

        df = pd.concat(
            [
                stock_df.loc[
                    tick_df.index,
                ],
                tick_df,
            ],
            axis=1,
        )

        df = df.rename(columns={"lastPrice": "price", "amount": "turnover"})

        df["timestamp"] = df["time"].apply(to_pd_timestamp)

        df["id"] = df[["entity_id", "timestamp"]].apply(
            lambda se: "{}_{}".format(se["entity_id"], to_time_str(se["timestamp"])), axis=1
        )

        # 换手率
        df["turnover_rate"] = df["pvolume"] / df["float_volume"]
        # 涨跌幅
        df["change_pct"] = (df["price"] - df["lastClose"]) / df["lastClose"]
        # 盘口卖单金额
        df["ask_amount"] = df.apply(
            lambda row: np.sum(np.array(row["askPrice"]) * (np.array(row["askVol"]) * 100)), axis=1
        )
        # 盘口买单金额
        df["bid_amount"] = df.apply(
            lambda row: np.sum(np.array(row["bidPrice"]) * (np.array(row["bidVol"]) * 100)), axis=1
        )
        # 涨停
        df["is_limit_up"] = (df["price"] != 0) & (df["price"] >= df["limit_up_price"])
        df["limit_up_amount"] = df.apply(lambda row: calculate_limit_up_amount(row), axis=1)

        # 跌停
        df["is_limit_down"] = (df["price"] != 0) & (df["price"] <= df["limit_down_price"])
        df["limit_down_amount"] = df.apply(lambda row: calculate_limit_down_amount(row), axis=1)

        df["float_cap"] = df["float_volume"] * df["price"]
        df["total_cap"] = df["total_volume"] * df["price"]

        df_to_db(df, data_schema=StockQuote, provider="qmt", force_update=True, drop_duplicates=False)
        cost_time = time.time() - start_time
        logger.info(f"Quotes cost_time:{cost_time} for {len(datas.keys())} stocks")

    return on_data


def download_capital_data():
    stocks = get_qmt_stocks()
    xtdata.download_financial_data2(
        stock_list=stocks, table_list=["Capital"], start_time="", end_time="", callback=lambda x: print(x)
    )


def clear_history_quote():
    session = get_db_session("qmt", data_schema=StockQuote)
    session.query(StockQuote).filter(StockQuote.timestamp < current_date()).delete()
    session.commit()


def record_tick():
    clear_history_quote()
    Stock.record_data(provider="em")
    stocks = get_qmt_stocks()
    print(stocks)
    xtdata.subscribe_whole_quote(stocks, callback=tick_to_quote())

    """阻塞线程接收行情回调"""
    import time

    client = xtdata.get_client()
    while True:
        time.sleep(3)
        if not client.is_connected():
            raise Exception("行情服务连接断开")
        current_timestamp = now_pd_timestamp()
        if current_timestamp.hour == 15 and current_timestamp.minute == 10:
            logger.info(f"record tick finished at: {current_timestamp}")
            break


if __name__ == "__main__":
    record_tick()


# the __all__ is generated
__all__ = [
    "get_qmt_stocks",
    "get_entity_list",
    "get_kdata",
    "tick_to_quote",
    "download_capital_data",
    "clear_history_quote",
]
