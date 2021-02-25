# -*- coding: utf-8 -*-
from zvt.utils.time_utils import to_pd_timestamp
from zvt.utils.utils import add_func_to_value, first_item_to_float
from zvt.api.quote import to_report_period_type
from zvt.domain import StockPerformanceForecast
from zvt.recorders.joinquant.finance.base_jq_stock_finance_recorder import BaseJqStockFinanceRecorder

performance_forecast_map = {
     # 预告类型
    "preview_type": "type",
     # 预告净利润（下限）
    "profit_min": "profit_min",
    # 预告净利润（上限）
    "profit_max": "profit_max",
    # 去年同期净利润（上限）
    "profit_last": "profit_last",
    # 预告净利润变动幅度(下限)单位：%
    "profit_ratio_min": "profit_ratio_min",
    # 预告净利润变动幅度(上限)单位：%
    "profit_ratio_max": "profit_ratio_max",
    # 预告内容
    "content": "content",
}

add_func_to_value(performance_forecast_map, first_item_to_float)
performance_forecast_map["report_period"] = ("ReportDate", to_report_period_type)
performance_forecast_map["report_date"] = ("ReportDate", to_pd_timestamp)

class JqStockPerformanceForecastRecorder(BaseJqStockFinanceRecorder):
    data_schema = StockPerformanceForecast
    # 业绩预告
    # STK_FIN_FORCAST
    finance_report_type = 'FIN_FORCAST'
    data_type = 4
    def get_data_map(self):
        return performance_forecast_map


__all__ = ['JqStockPerformanceForecastRecorder']

if __name__ == '__main__':
    # init_log('blance_sheet.log')
    recorder = JqStockPerformanceForecastRecorder(codes=['002572'])
    recorder.run()
