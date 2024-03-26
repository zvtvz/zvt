# -*- coding: utf-8 -*-
import json

from examples.data_runner.kdata_runner import record_stock_data, record_stock_news, record_stock_events
from examples.reports.report_tops import report_top_stocks, report_top_blocks
from examples.reports.report_vol_up import report_vol_up_stocks
from examples.utils import get_hot_topics
from zvt import zvt_config
from zvt.factors.top_stocks import compute_top_stocks
from zvt.informer import EmailInformer
from zvt.utils import current_date

if __name__ == "__main__":

    # record_stock_news()

    record_stock_data()
    # record_stock_events()
    compute_top_stocks()

    report_top_stocks()
    # report_top_blocks()
    report_vol_up_stocks()
