# -*- coding: utf-8 -*-
import logging

import pandas as pd
from xtquant import xtdata

from zvt import init_log

logger = logging.getLogger(__name__)


def download_data():
    period = "1d"
    xtdata.download_sector_data()
    stock_codes = xtdata.get_stock_list_in_sector("沪深A股")
    stock_codes = sorted(stock_codes)
    count = len(stock_codes)

    for index, stock_code in enumerate(stock_codes):
        logger.info(f"run to {index + 1}/{count}")

        xtdata.download_history_data(stock_code, period=period)
        logger.info(f"download {stock_code} {period} kdata ok")
        records = xtdata.get_market_data(
            stock_list=[stock_code],
            period=period,
            count=5,
            dividend_type="front",
            fill_data=False,
        )
        dfs = []
        for col in records:
            df = records[col].T
            df.columns = [col]
            dfs.append(df)
        kdatas = pd.concat(dfs, axis=1)
        logger.info(kdatas)

        start_time = kdatas.index.to_list()[0]
        xtdata.download_history_data(stock_code, period="tick", start_time=start_time)
        logger.info(f"download {stock_code} tick from {start_time} ok")
        # records = xtdata.get_market_data(
        #     stock_list=[stock_code],
        #     period="tick",
        #     count=5,
        #     fill_data=False,
        # )
        # logger.info(records[stock_code])

    xtdata.download_financial_data2(
        stock_list=stock_codes, table_list=["Capital"], start_time="", end_time="", callback=lambda x: print(x)
    )
    logger.info("download capital data ok")


if __name__ == "__main__":
    init_log("qmt_data_manager.log")
    download_data()
