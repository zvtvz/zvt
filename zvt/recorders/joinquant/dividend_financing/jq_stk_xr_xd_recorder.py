# -*- coding: utf-8 -*-
import pandas as pd

from zvt import zvt_env
from zvt.api import TIME_FORMAT_DAY, get_str_schema
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimeSeriesDataRecorder
from zvt.domain import DividendDetail,StockDetail
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import now_pd_timestamp, to_time_str
from jqdatasdk import auth, query, indicator, get_fundamentals, logout, finance
from zvt.recorders.joinquant.common import to_jq_entity_id

class JqDividendDetailRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = StockDetail
    provider = 'joinquant'

    data_schema = DividendDetail

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False,
                 fix_duplicate_way='add', start_timestamp=None, end_timestamp=None, close_hour=0,
                 close_minute=0) -> None:
        self.data_schema = get_str_schema('DividendDetail')
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)
        auth(zvt_env['jq_username'], zvt_env['jq_password'])


    def record(self, entity, start, end, size, timestamps):
        if not end:
            end = to_time_str(now_pd_timestamp())
        start = to_time_str(start)
        em_code = to_jq_entity_id(entity)

        div_columns_dict = {
            "report_date": "report_date", #报告时间
            "board_plan_pub_date": "announce_date",  #公告日
            "a_registration_date": "record_date",  #股权登记日
            "a_bonus_date": "dividend_date",  # 除权除息日
            "shareholders_plan_bonusnote": "dividend",  # 方案
            "announce_date_general_meeting": "shareholders_plan_pub_date",  # 股东大会公告日
            "implementation_pub_date": "announce_date_dividend_implementation",  # 分红实施公告日
            "b_registration_date": "last_trading_day_b_shares",  # B股最后交易日 股权登记日
            "at_bonus_ratio_rmb": "dividend_per_share_after_tax",  # 每股股利(税后) 原始数据/10
            "bonus_ratio_rmb": "dividend_per_share_before_tax",  # 每股股利(税前) 原始数据/10
            "plan_progress": "dividend_plan_progress",  # 分红方案进度
            "dividend_arrival_date": "dividend_pay_date",  # 派息日,红利到账日
            "dividend_ratio": "share_bonus_per_share",  # 每股送股比例  原始数据/10
            "transfer_ratio": "per_share_conversion_ratio",  # 每股转增比例 应该 原始数据/10
        }

        df = finance.run_query(query(finance.STK_XR_XD).filter(
            finance.STK_XR_XD.code == em_code,
            finance.STK_XR_XD.board_plan_pub_date >= start).order_by(
            finance.STK_XR_XD.report_date).limit(100))
        df.rename(columns=div_columns_dict, inplace=True)
        df.dropna(subset=['dividend_date'], inplace=True)
        if pd_is_not_null(df):
            df.reset_index(drop=True,inplace=True)
            df['dividend_per_share_after_tax'] = df['dividend_per_share_after_tax']/10
            df['dividend_per_share_before_tax'] = df['dividend_per_share_before_tax']/10
            df['share_bonus_per_share'] = df['share_bonus_per_share']/10
            df['per_share_conversion_ratio'] = df['per_share_conversion_ratio']/10
            # df['dividend'] = df['dividend'].apply(lambda x: str(x).split('（')[0])
            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df.report_date)
            df['provider'] = 'joinquant'
            df['code'] = entity.code

            def generate_id(se):
                return "{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY))

            df['id'] = df[['entity_id', 'timestamp']].apply(generate_id, axis=1)
            # df.replace('None',pd.NaT,inplace=True)
            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None


__all__ = ['JqDividendDetailRecorder']

if __name__ == '__main__':
    # 上证50
    JqDividendDetailRecorder(codes=['050002']).run()
    # JqChinaEtfValuationRecorder(codes=['512290']).run()
