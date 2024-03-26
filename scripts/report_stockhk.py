# -*- coding: utf-8 -*-
from examples.data_runner.kdata_runner import record_stockhk_data
from examples.reports.report_tops import report_top_stockhks
from examples.reports.report_vol_up import report_vol_up_stockhks

if __name__ == "__main__":
    record_stockhk_data()

    report_top_stockhks()
    report_vol_up_stockhks()
