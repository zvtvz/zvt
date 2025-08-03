# -*- coding: utf-8 -*-
import logging
import time

import numpy as np
import pandas as pd
from xtquant import xtdata

from zvt.api.kdata import get_recent_trade_dates
from zvt.api.selector import get_entity_ids_by_filter
from zvt.contract import IntervalLevel, AdjustType
from zvt.contract.api import decode_entity_id, df_to_db, get_db_session
from zvt.domain import StockQuote, Stock, Stock1dKdata
from zvt.domain.quotes.stock.stock_quote import Stock1mQuote, StockQuoteLog
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import (
    to_date_time_str,
    current_date,
    to_pd_timestamp,
    now_pd_timestamp,
    TIME_FORMAT_MINUTE,
    date_time_by_interval,
    now_timestamp_ms,
    to_timestamp_ms,
    date_and_time,
)

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
    try:
        end_date = to_pd_timestamp(stock_detail["ExpireDate"])
    except:
        end_date = None

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


def get_qmt_stocks(include_bj=True):
    stock_list = xtdata.get_stock_list_in_sector("沪深A股")

    if include_bj:
        bj_entity_ids = get_entity_ids_by_filter(
            provider="em", ignore_delist=True, ignore_st=False, entity_type="stock", exchange="bj"
        )
        bj_stock_list = map(lambda x: _to_qmt_code(x), bj_entity_ids)

        stock_list += bj_stock_list
    return stock_list


def _build_entity_list(qmt_stocks):
    entity_list = []
    for stock in qmt_stocks:
        stock_detail = xtdata.get_instrument_detail(stock, False)
        if stock_detail:
            entity_list.append(_qmt_instrument_detail_to_stock(stock_detail))
        else:
            code, exchange = stock.split(".")
            exchange = exchange.lower()
            entity_id = f"stock_{exchange}_{code}"
            # get from provider em
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

            # Do this in other task in days timely
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
                if exchange == "bj":  # 北交所
                    limit_up_price = tick[stock]["lastClose"] * 1.29
                    limit_down_price = tick[stock]["lastClose"] * 0.71
                elif code.startswith(("30", "68")):  # 创业板和科创板
                    limit_up_price = tick[stock]["lastClose"] * 1.19
                    limit_down_price = tick[stock]["lastClose"] * 0.81
                else:
                    limit_up_price = tick[stock]["lastClose"] * 1.1
                    limit_down_price = tick[stock]["lastClose"] * 0.9
                entity["limit_up_price"] = round(limit_up_price, 2)
                entity["limit_down_price"] = round(limit_down_price, 2)
            entity_list.append(entity)

    return pd.DataFrame.from_records(data=entity_list)


def get_entity_list(include_bj=True):
    stocks = get_qmt_stocks(include_bj=include_bj)
    return _build_entity_list(qmt_stocks=stocks)


def get_kdata(
    entity_id,
    start_timestamp,
    end_timestamp,
    level=IntervalLevel.LEVEL_1DAY,
    adjust_type=AdjustType.qfq,
    download_history=True,
):
    code = _to_qmt_code(entity_id=entity_id)
    period = level.value
    start_time = to_date_time_str(start_timestamp, fmt="YYYYMMDDHHmmss")
    end_time = to_date_time_str(end_timestamp, fmt="YYYYMMDDHHmmss")
    # download比较耗时，建议单独定时任务来做
    if download_history:
        print(f"download from {start_time} to {end_time}")
        xtdata.download_history_data(stock_code=code, period=period, start_time=start_time, end_time=end_time)
    records = xtdata.get_market_data(
        stock_list=[code],
        period=period,
        start_time=to_date_time_str(start_timestamp, fmt="YYYYMMDDHHmmss"),
        end_time=to_date_time_str(end_timestamp, fmt="YYYYMMDDHHmmss"),
        dividend_type=_to_qmt_dividend_type(adjust_type=adjust_type),
        fill_data=False,
    )

    dfs = []
    for col in records:
        df = records[col].T
        df.columns = [col]
        dfs.append(df)
    df = pd.concat(dfs, axis=1)
    df["volume"] = df["volume"] * 100
    return df


def tick_to_quote(entity_df):
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
        stock_finished = False
        if not Stock.in_trading_time():
            stock_finished = True
        start_time = time.time()

        time_tag = False
        track_time = None
        for code in datas:
            tick_data = datas[code]
            if "timetag" in tick_data:
                time_tag = True
                track_time = to_timestamp_ms(tick_data["timetag"])
                delay = (now_timestamp_ms() - track_time) / (60 * 1000)
            else:
                track_time = datas[code]["time"]
                delay = (now_timestamp_ms() - track_time) / (60 * 1000)
            logger.info(f"check delay for {code}")
            if delay < 1:
                break
            else:
                logger.warning(f"delay {delay} minutes, may need to restart this script or qmt client")
                break

        tick_df = pd.DataFrame.from_records(data=[datas[code] for code in datas], index=list(datas.keys()))
        if time_tag:
            tick_df["time"] = tick_df["timetag"].apply(to_timestamp_ms)
        # 过滤无效tick,一般是退市的
        tick_df = tick_df[tick_df["lastPrice"] != 0]
        tick_df.index = tick_df.index.map(_to_zvt_entity_id)

        # tick_df = tick_df[tick_df.index.isin(stock_df.index)]

        stock_df = stock_df[~stock_df.index.duplicated(keep="first")]  # 保留首次出现的行
        tick_df = tick_df[~tick_df.index.duplicated(keep="first")]
        df = pd.concat(
            [
                stock_df,
                tick_df,
            ],
            axis=1,
            join="inner",
        )

        df = df.rename(columns={"lastPrice": "price", "amount": "turnover"})
        df["close"] = df["price"]

        if stock_finished:
            the_time = date_and_time(track_time, "15:00")
            df["time"] = to_timestamp_ms(the_time)

        df["timestamp"] = df["time"].apply(to_pd_timestamp)

        df["id"] = df[["entity_id", "timestamp"]].apply(
            lambda se: "{}_{}".format(se["entity_id"], to_date_time_str(se["timestamp"])), axis=1
        )

        df["volume"] = df["pvolume"]
        df["avg_price"] = df["turnover"] / df["volume"]
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

        df["provider"] = "qmt"
        # 实时行情统计，只保留最新
        df_to_db(df, data_schema=StockQuote, provider="qmt", force_update=True, drop_duplicates=False)

        # 1分钟分时
        df["id"] = df[["entity_id", "timestamp"]].apply(
            lambda se: "{}_{}".format(se["entity_id"], to_date_time_str(se["timestamp"], TIME_FORMAT_MINUTE)), axis=1
        )
        df_to_db(df, data_schema=Stock1mQuote, provider="qmt", force_update=True, drop_duplicates=False)

        # 日线行情
        df["timestamp"] = date_and_time(track_time, "00:00")
        df["id"] = df[["entity_id", "timestamp"]].apply(
            lambda se: "{}_{}".format(se["entity_id"], to_date_time_str(se["timestamp"])), axis=1
        )
        df["level"] = "1d"
        df_to_db(df=df, data_schema=Stock1dKdata, provider="em", force_update=True, drop_duplicates=False)

        # 历史记录
        # df["id"] = df[["entity_id", "timestamp"]].apply(
        #     lambda se: "{}_{}".format(se["entity_id"], to_time_str(se["timestamp"], TIME_FORMAT_MINUTE2)), axis=1
        # )
        # df_to_db(df, data_schema=StockQuoteLog, provider="qmt", force_update=True, drop_duplicates=False)

        cost_time = time.time() - start_time
        logger.info(f"Quotes cost_time:{cost_time} for {len(datas.keys())} stocks")

    return on_data


def clear_history_quote(target_date):
    session = get_db_session("qmt", data_schema=StockQuote)
    session.query(StockQuote).filter(StockQuote.timestamp < target_date).delete()
    session.commit()

    dates = get_recent_trade_dates(entity_type="stock", target_date=target_date, days_count=5)
    if dates:
        start_date = dates[0]
    else:
        start_date = date_time_by_interval(target_date, -5)

    session.query(Stock1mQuote).filter(Stock1mQuote.timestamp < start_date).delete()
    session.query(StockQuoteLog).filter(StockQuoteLog.timestamp < start_date).delete()
    session.commit()


def record_stock_quote(subscribe=False):
    clear_history_quote(target_date=current_date())
    qmt_stocks = get_qmt_stocks()
    entity_list = _build_entity_list(qmt_stocks=qmt_stocks)
    entity_df = entity_list[
        ["entity_id", "code", "name", "limit_up_price", "limit_down_price", "float_volume", "total_volume"]
    ]
    entity_df = entity_df.set_index("entity_id", drop=False)
    on_data_func = tick_to_quote(entity_df=entity_df)

    if subscribe:
        logger.info(f"subscribe tick for {len(qmt_stocks)} stocks")
        sid = xtdata.subscribe_whole_quote(qmt_stocks, callback=on_data_func)

        """阻塞线程接收行情回调"""
        import time

        client = xtdata.get_client()
        while True:
            time.sleep(3)
            if not client.is_connected():
                raise Exception("行情服务连接断开")
            current_timestamp = now_pd_timestamp()
            if not Stock.in_real_trading_time():
                logger.info(f"record tick finished at: {current_timestamp}")
                break
        xtdata.unsubscribe_quote(sid)
    else:
        import time

        first_time = True
        while True:
            if not first_time and Stock.in_trading_time() and not Stock.in_real_trading_time():
                logger.info(f"Sleeping time......")
                time.sleep(60 * 1)
                continue

            datas = xtdata.get_full_tick(code_list=qmt_stocks)
            on_data_func(datas=datas)

            time.sleep(3)
            current_timestamp = now_pd_timestamp()
            if not Stock.in_trading_time():
                logger.info(f"record tick finished at: {current_timestamp}")
                break

            first_time = False


if __name__ == "__main__":
    from apscheduler.schedulers.background import BackgroundScheduler

    sched = BackgroundScheduler()
    record_stock_quote()
    sched.add_job(func=record_stock_quote, trigger="cron", hour=9, minute=18, day_of_week="mon-fri")
    sched.start()
    sched._thread.join()

# the __all__ is generated
__all__ = [
    "get_qmt_stocks",
    "get_entity_list",
    "get_kdata",
    "tick_to_quote",
    "clear_history_quote",
]
