from jqdatasdk import auth, query, finance

from zvdata.recorder import TimeSeriesDataRecorder
from zvdata.utils.time_utils import to_time_str
from zvt import zvt_env
from zvt.domain import Index, MarginTradingSummary

# 聚宽编码
# XSHG-上海证券交易所
# XSHE-深圳证券交易所

code_map_jq = {
    '000001': 'XSHG',
    '399106': 'XSHE'
}


class MarginTradingSummaryRecorder(TimeSeriesDataRecorder):
    entity_provider = 'exchange'
    entity_schema = Index

    provider = 'joinquant'
    data_schema = MarginTradingSummary

    def __init__(self, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False,
                 fix_duplicate_way='add') -> None:
        # 上海A股,深圳市场
        codes = ['000001', '399106']
        super().__init__('index', ['cn'], None, codes, batch_size,
                         force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way)

        auth(zvt_env['jq_username'], zvt_env['jq_password'])

    def record(self, entity, start, end, size, timestamps):
        jq_code = code_map_jq.get(entity.code)

        q = query(finance.STK_MT_TOTAL).filter(
            finance.STK_MT_TOTAL.exchange_code == jq_code,
            finance.STK_MT_TOTAL.date >= to_time_str(start)).limit(2000)

        df = finance.run_query(q)
        print(df)

        json_results = []

        for item in df.to_dict(orient='records'):
            result = {
                'provider': self.provider,
                'timestamp': item['date'],
                'name': entity.name,
                'margin_value': item['fin_value'],
                'margin_buy': item['fin_buy_value'],
                'short_value': item['sec_value'],
                'short_volume': item['sec_sell_volume'],
                'total_value': item['fin_sec_value']
            }

            json_results.append(result)

        if len(json_results) < 100:
            self.one_shot = True

        return json_results

    def get_data_map(self):
        return None


if __name__ == '__main__':
    MarginTradingSummaryRecorder(batch_size=30).run()
