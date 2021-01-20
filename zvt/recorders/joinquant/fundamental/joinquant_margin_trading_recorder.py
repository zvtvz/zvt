# -*- coding: utf-8 -*-

import pandas as pd
from jqdatapy.api import get_mtss

from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimeSeriesDataRecorder
from zvt.domain import Stock, MarginTrading
from zvt.recorders.joinquant.common import to_jq_entity_id
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_time_str, TIME_FORMAT_DAY


class MarginTradingRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Stock

    # 数据来自jq
    provider = 'joinquant'

    data_schema = MarginTrading

    def __init__(self, entity_type='stock', exchanges=None, entity_ids=None, codes=None, day_data=True, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False, fix_duplicate_way='add',
                 start_timestamp=None, end_timestamp=None, close_hour=0, close_minute=0) -> None:
        super().__init__(entity_type, exchanges, entity_ids, codes, day_data, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)

    def record(self, entity, start, end, size, timestamps):
        df = get_mtss(code=to_jq_entity_id(entity), date=to_time_str(start))

        if pd_is_not_null(df):
            df['entity_id'] = entity.id
            df['code'] = entity.code
            df.rename(columns={'date': 'timestamp'}, inplace=True)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['id'] = df[['entity_id', 'timestamp']].apply(
                lambda se: "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY)), axis=1)

            print(df)
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

        return None


if __name__ == '__main__':
    MarginTradingRecorder(codes=['000004']).run()
# the __all__ is generated
__all__ = ['MarginTradingRecorder']