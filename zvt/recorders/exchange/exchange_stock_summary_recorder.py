import demjson
import pandas as pd
import requests

from zvt.contract.recorder import TimestampsDataRecorder
from zvt.domain import Index
from zvt.domain.misc import StockSummary
from zvt.recorders.consts import DEFAULT_SH_SUMMARY_HEADER
from zvt.utils.time_utils import to_time_str
from zvt.utils.utils import to_float


class ExchangeStockSummaryRecorder(TimestampsDataRecorder):
    entity_provider = 'exchange'
    entity_schema = Index

    provider = 'exchange'
    data_schema = StockSummary

    original_page_url = 'http://www.sse.com.cn/market/stockdata/overview/day/'

    url = 'http://query.sse.com.cn/marketdata/tradedata/queryTradingByProdTypeData.do?jsonCallBack=jsonpCallback30731&searchDate={}&prodType=gp&_=1515717065511'

    def __init__(self, force_update=False, sleeping_time=5, exchanges=None, entity_ids=None, day_data=False,
                 entity_filters=None, ignore_failed=True, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None) -> None:
        super().__init__(force_update, sleeping_time, exchanges, entity_ids, ['000001'], day_data, entity_filters,
                         ignore_failed, real_time, fix_duplicate_way, start_timestamp, end_timestamp)

    def init_timestamps(self, entity):
        return pd.date_range(start=entity.timestamp,
                             end=pd.Timestamp.now(),
                             freq='B').tolist()

    def record(self, entity, start, end, size, timestamps):
        json_results = []
        for timestamp in timestamps:
            timestamp_str = to_time_str(timestamp)
            url = self.url.format(timestamp_str)
            response = requests.get(url=url, headers=DEFAULT_SH_SUMMARY_HEADER)

            results = demjson.decode(response.text[response.text.index("(") + 1:response.text.index(")")])['result']
            result = [result for result in results if result['productType'] == '1']
            if result and len(result) == 1:
                result_json = result[0]
                # 有些较老的数据不存在,默认设为0.0
                json_results.append({
                    'provider': 'exchange',
                    'timestamp': timestamp,
                    'name': '上证指数',
                    'pe': to_float(result_json['profitRate'], 0.0),
                    'total_value': to_float(result_json['marketValue1'] + '亿', 0.0),
                    'total_tradable_vaule': to_float(result_json['negotiableValue1'] + '亿', 0.0),
                    'volume': to_float(result_json['trdVol1'] + '万', 0.0),
                    'turnover': to_float(result_json['trdAmt1'] + '亿', 0.0),
                    'turnover_rate': to_float(result_json['exchangeRate'], 0.0),
                })

                if len(json_results) > 30:
                    return json_results

        return json_results

    def get_data_map(self):
        return None


if __name__ == '__main__':
    ExchangeStockSummaryRecorder().run()
# the __all__ is generated
__all__ = ['ExchangeStockSummaryRecorder']