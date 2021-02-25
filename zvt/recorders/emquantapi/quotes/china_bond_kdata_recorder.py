# -*- coding: utf-8 -*-
import argparse

import pandas as pd

from EmQuantAPI import *

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.domain.quotes.bond import Bond1dKdata

from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_time_str, now_pd_timestamp, TIME_FORMAT_DAY

class EmChinaBondKdataRecorder(Recorder):
    data_schema = Bond1dKdata

    provider = 'emquantapi'

    def __init__(self, batch_size=10, force_update=True, sleeping_time=10) -> None:
        super().__init__(batch_size, force_update, sleeping_time)

    # 调用登录函数（激活后使用，不需要用户名密码）
    loginResult = c.start("ForceLogin=1", '')
    if (loginResult.ErrorCode != 0):
        print("login in fail")
        exit()

    def run(self):
        from zvt.api import get_kdata
        bond_data = get_kdata(entity_id='bond_cn_EMM00166466')
        now_date = to_time_str(now_pd_timestamp())
        if bond_data.empty:
            # 初始时间定在2007年
            start = '2007-01-01'
        else:
            start = to_time_str(bond_data.timestamp.max())
        # EMM00166466 中债国债到期收益率：10年
        df = c.edb("EMM00166466", f"IsLatest=0,StartDate={start},EndDate={now_date},ispandas=1")

        if pd_is_not_null(df):
            df['name'] = "中债国债到期收益率：10年"
            df.rename(columns={'RESULT': 'data_value', 'DATES': 'timestamp'}, inplace=True)

            df['entity_id'] = 'bond_cn_EMM00166466'
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['provider'] = 'emquantapi'
            df['exchange'] = 'cn'
            df['level'] = '1d'
            df['code'] = "EMM00166466"


            def generate_kdata_id(se):
                return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))

            df['id'] = df[['entity_id', 'timestamp']].apply(generate_kdata_id, axis=1)

            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)


__all__ = ['EmChinaBondKdataRecorder']

if __name__ == '__main__':

    spider = EmChinaBondKdataRecorder(provider='emquantapi')
    spider.run()