# -*- coding: utf-8 -*-

from zvdata.recorder import TimeSeriesDataRecorder
from zvt.domain import StockValuation, Index, IndexValuation, StockIndex


class ChinaIndexValuationRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Index

    # 数据来自jq
    provider = 'joinquant'

    data_schema = IndexValuation

    def __init__(self, entity_type='index', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)

    def record(self, entity, start, end, size, timestamps):
        stock_index: StockIndex = StockIndex.query_data(provider='joinquant', entity_id=entity.id,
                                                  return_type='domain',
                                                  start_timestamp='2019-06-30', end_timestamp='2019-09-29')
        stocks = [item.stock_id for item in stock_index]
        df = StockValuation.query_data(entity_ids=stocks, start_timestamp=start)
        df.groupby('timestamp')

        for timestamp, df in df.groupby('timestamp'):
            df['pe']

        # df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

        return None


if __name__ == '__main__':
    ChinaIndexValuationRecorder(entity_ids=['index_sh_510050']).run()
