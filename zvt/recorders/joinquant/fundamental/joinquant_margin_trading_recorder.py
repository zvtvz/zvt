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