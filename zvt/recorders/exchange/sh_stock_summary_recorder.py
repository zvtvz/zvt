import demjson
import pandas as pd
import requests

from zvt.domain import Provider, StoreCategory, SecurityType, Index
from zvt.domain.macro import StockSummary
from zvt.recorders.consts import DEFAULT_SH_SUMMARY_HEADER
from zvt.recorders.recorder import TimestampsDataRecorder, ApiWrapper, TimeSeriesFetchingStyle
from zvt.utils.time_utils import to_time_str
from zvt.utils.utils import to_float


#     id = Column(String(length=128), primary_key=True)
#     provider = Column(Enum(Provider, values_callable=enum_value), primary_key=True)
#     timestamp = Column(DateTime)
#     security_id = Column(String(length=128))
#     code = Column(String(length=32))
#     name = Column(String(length=32))
#
#     total_value = Column(Float)
#     total_tradable_vaule = Column(Float)
#     pe = Column(Float)
#     volume = Column(Float)
#     turnover = Column(Float)
#     turnover_rate = Column(Float)
class StockSummaryApiWrapper(ApiWrapper):
    def request(self, url=None, method='get', param=None, path_fields=None):
        url = url.format(param)
        response = requests.get(url=url, headers=DEFAULT_SH_SUMMARY_HEADER)

        results = demjson.decode(response.text[response.text.index("(") + 1:response.text.index(")")])['result']
        result = [result for result in results if result['productType'] == '1']
        if result and len(result) == 1:
            result_json = result[0]
            # 有些较老的数据不存在,默认设为0.0
            return [{
                'provider': Provider.EXCHANGE.value,
                'timestamp': param,
                'name': '上证指数',
                'pe': to_float(result_json['profitRate'], 0.0),
                'total_value': to_float(result_json['marketValue1'] + '亿', 0.0),
                'total_tradable_vaule': to_float(result_json['negotiableValue1'] + '亿', 0.0),
                'volume': to_float(result_json['trdVol1'] + '万', 0.0),
                'turnover': to_float(result_json['trdAmt1'] + '亿', 0.0),
                'turnover_rate': to_float(result_json['exchangeRate'], 0.0),
            }]


class StockSummaryRecorder(TimestampsDataRecorder):
    meta_provider = Provider.EXCHANGE
    meta_schema = Index

    provider = Provider.EXCHANGE
    store_category = StoreCategory.macro  # type: StoreCategory
    data_schema = StockSummary
    url = 'http://query.sse.com.cn/marketdata/tradedata/queryTradingByProdTypeData.do?jsonCallBack=jsonpCallback30731&searchDate={}&prodType=gp&_=1515717065511'
    api_wrapper = StockSummaryApiWrapper()

    def __init__(self, security_type=SecurityType.index, exchanges=['cn'], codes=['000001'], batch_size=10,
                 force_update=False, sleeping_time=5, fetching_style=TimeSeriesFetchingStyle.end_size,
                 default_size=2000) -> None:
        super().__init__(security_type, exchanges, codes, batch_size, force_update, sleeping_time, fetching_style,
                         default_size)

    def init_timestamps(self, security_item):
        self.security_timestamps_map[security_item.id] = pd.date_range(start=security_item.timestamp,
                                                                       end=pd.Timestamp.now(),
                                                                       freq='B').tolist()

    def generate_request_param(self, security_item, start, end, size, timestamp):
        return to_time_str(timestamp)

    def get_data_map(self):
        return None


if __name__ == '__main__':
    StockSummaryRecorder(batch_size=30).run()
