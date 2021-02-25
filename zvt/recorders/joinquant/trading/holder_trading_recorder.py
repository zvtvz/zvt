# -*- coding: utf-8 -*-
from jqdatasdk import auth, get_query_count, finance, query, normalize_code
import pandas as pd
from zvt.recorders.joinquant.common import to_jq_entity_id

from zvt import zvt_env
from zvt.api import get_str_schema, to_time_str, pd_is_not_null, generate_kdata_id, TIME_FORMAT_ISO8601, TIME_FORMAT_DAY
from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.utils.utils import to_float
from zvt.domain import HolderTrading
from zvt.domain import Stock


class HolderTradingRecorder(FixedCycleDataRecorder):
    """
    大股东交易
    """
    entity_provider = 'joinquant'
    entity_schema = Stock

    # 数据来自jq
    provider = 'joinquant'

    data_schema = HolderTrading

    def __init__(self,
                 entity_type='stock',
                 exchanges=['sh', 'sz'],
                 entity_ids=None,
                 codes=None,
                 batch_size=10,
                 force_update=True,
                 sleeping_time=0,
                 default_size=2000,
                 real_time=False,
                 fix_duplicate_way='ignore',
                 start_timestamp=None,
                 end_timestamp=None,
                 kdata_use_begin_time=False,
                 level=None,
                 close_hour=15,
                 close_minute=0,
                 one_day_trading_minutes=4 * 60,
                 ) -> None:
        self.data_schema = get_str_schema('HolderTrading')

        super().__init__('fund', exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute, level, kdata_use_begin_time, one_day_trading_minutes)

        auth(zvt_env['jq_username'], zvt_env['jq_password'])
        print(f"剩余{get_query_count()['spare'] / 10000}万")

    def record(self, entity, start, end, size, timestamps):
        df = finance.run_query(query(finance.STK_SHAREHOLDERS_SHARE_CHANGE).filter(
            finance.STK_SHAREHOLDERS_SHARE_CHANGE.code == to_jq_entity_id(entity)).filter(
            finance.STK_SHAREHOLDERS_SHARE_CHANGE.pub_date >= to_time_str(start)))
        if pd_is_not_null(df):
            df.reset_index(inplace=True, drop=True)
            df['name'] = entity.name
            df['index_columns'] = df.index

            df.rename(columns={
                'pub_date': 'timestamp',  # 公告日期
                'end_date': 'holder_end_date',  # 变动截至日期
                'shareholder_name': 'holder_name',  # 股东名称
                'change_number': 'volume',  # 变动数量
                'change_ratio': 'change_pct',  # 变动比例  变动数量占总股本比例(%)
                'after_change_ratio': 'holding_pct',  # 变动后_占总股本比例(%)
                'price_ceiling': 'price',  # 交易均价(元)
            }, inplace=True)
            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df.timestamp)
            df['provider'] = 'joinquant'
            df['code'] = entity.code
            df['holder_direction'] = df.type.replace(1, '减持').replace(0, '增持')

            def generate_id(se):
                return "{}_{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY), se.name)

            df = pd.concat([i.reset_index(drop=True) for i in dict(list(df.groupby('timestamp'))).values()])
            df.index += 1
            df['id'] = df[['entity_id', 'timestamp']].apply(generate_id, axis=1)

            df['holder_name'] = df['holder_name'].apply(lambda x: str(x).replace('(有限合伙)', ''))
            df['holder_name'] = df['holder_name'].apply(lambda x: str(x).replace('（有限合伙）', ''))
            df['holder_name'] = df['holder_name'].apply(lambda x: str(x).split('-')[0])
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None


__all__ = ['HolderTradingRecorder']

if __name__ == '__main__':
    # init_log('holder_trading.log')

    recorder = HolderTradingRecorder(codes=['002572'])
    recorder.run()
