# -*- coding: utf-8 -*-
import pandas as pd
from EmQuantAPI import *

from zvt.api import TIME_FORMAT_DAY, get_str_schema
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimeSeriesDataRecorder
from zvt.domain import HolderTradePlan, StockDetail, StockValuation
from zvt.recorders.emquantapi.common import mainCallback, to_em_entity_id
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import now_pd_timestamp, to_time_str


class EmHolderTradePlanRecorder(TimeSeriesDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = StockDetail

    # 数据来自jq
    provider = 'emquantapi'

    data_schema = HolderTradePlan

    def __init__(self, entity_type='stock', exchanges=['sh', 'sz'], entity_ids=None, codes=None, batch_size=10,
                 force_update=False, sleeping_time=5, default_size=2000, real_time=False,
                 fix_duplicate_way='add', start_timestamp=None, end_timestamp=None, close_hour=0,
                 close_minute=0) -> None:
        self.data_schema = get_str_schema('HolderTradePlan')
        super().__init__(entity_type, exchanges, entity_ids, codes, batch_size, force_update, sleeping_time,
                         default_size, real_time, fix_duplicate_way, start_timestamp, end_timestamp, close_hour,
                         close_minute)
        # 调用登录函数（激活后使用，不需要用户名密码）
        loginResult = c.start("ForceLogin=1", '', mainCallback)
        if (loginResult.ErrorCode != 0):
            print("login in fail")
            exit()

    def on_finish(self):
        # 退出
        loginresult = c.stop()
        if (loginresult.ErrorCode != 0):
            print("login in fail")
            exit()

    def record(self, entity, start, end, size, timestamps):
        if not end:
            end = to_time_str(now_pd_timestamp())
        start = to_time_str(start)
        em_code = to_em_entity_id(entity)
        columns_list = list(self.data_schema.get_data_map(self))
        df = pd.DataFrame()
        i = 0
        underweight_trade_day = c.css(em_code, "HOLDDECREASEANNCDATEPLAN",
                                      f"StartDate={start},EndDate={end},ispandas=1")
        if underweight_trade_day.HOLDDECREASEANNCDATEPLAN[0]:
            underweight_trade_day_list = underweight_trade_day.HOLDDECREASEANNCDATEPLAN[0].split(',')
            for end_date in underweight_trade_day_list:

                # 减持
                Underweight_data = c.css(em_code,
                                         "HOLDDECREASEANNCDATENEWPLAN,HOLDDECREASENAMENEWPLAN,DECRENEWPROGRESS,"
                                         "DECRENEWMAXSHANUM,DECRENEWMINSHANUM",
                                         f"EndDate={end_date},ispandas=1")

                values_data = StockValuation.query_data(entity_id=entity.id, limit=1,
                                                        order=StockValuation.timestamp.desc(),
                                                        end_timestamp=end_date, columns=["capitalization"])
                name_list = Underweight_data.HOLDDECREASENAMENEWPLAN.tolist()[0].split(',')
                max_shanum = Underweight_data.DECRENEWMAXSHANUM.tolist()[0].split(',') if \
                Underweight_data.DECRENEWMAXSHANUM.tolist()[0] else None
                min_shanum = Underweight_data.DECRENEWMINSHANUM.tolist()[0].split(',') if \
                Underweight_data.DECRENEWMINSHANUM.tolist()[0] else None
                progress_data = Underweight_data.DECRENEWPROGRESS.tolist()[0] if \
                Underweight_data.DECRENEWPROGRESS.tolist()[0] else None
                try:
                    data_end = pd.DataFrame(
                        {"holder_name": name_list, "volume_plan_max": max_shanum, "volume_plan_mix": min_shanum},
                        index=[i for i in range(len(name_list))])
                except:
                    continue
                data_end['capitalization'] = values_data.capitalization.values[0]
                data_end = data_end.astype({'volume_plan_max': 'float64', 'volume_plan_mix': 'float64'})
                data_end['change_pct'] = round((data_end['volume_plan_max'] / data_end['capitalization']) * 100, 2)
                data_end['report_date'] = pd.to_datetime(end_date)
                data_end['plan_progress'] = progress_data if progress_data else None
                data_end['holder_direction'] = '减持'
                df = df.append(data_end)

        overweight_trade_day = c.css(em_code, "HOLDINCREASEANNCDATEPLAN", f"StartDate={start},EndDate={end},ispandas=1")
        if overweight_trade_day.HOLDINCREASEANNCDATEPLAN[0]:
            overweight_trade_day_list = overweight_trade_day.HOLDINCREASEANNCDATEPLAN[0].split(',')
            for end_date in overweight_trade_day_list:
                # 增持
                Overweight_data = c.css(em_code, "HOLDDECREASEANNCDATENEWPLAN,HOLDINCREASENAMENEWPLAN,HOLDPLANSCHEDULE,"
                                                 "HOLDMAXSHARENEWPLAN,HOLDMINSHARENEWPLAN",
                                        f"EndDate={end_date},ispandas=1")
                values_data = StockValuation.query_data(entity_id=entity.id, limit=1,
                                                        order=StockValuation.timestamp.desc(),
                                                        end_timestamp=end_date, columns=["capitalization"])
                name_list = Overweight_data.HOLDINCREASENAMENEWPLAN.tolist()[0].split(',')
                max_shanum = Overweight_data.HOLDMAXSHARENEWPLAN.tolist()[0].split(',') if \
                    Overweight_data.HOLDMAXSHARENEWPLAN.tolist()[0] else None
                min_shanum = Overweight_data.HOLDMINSHARENEWPLAN.tolist()[0].split(',') if \
                    Overweight_data.HOLDMINSHARENEWPLAN.tolist()[0] else None
                progress_data = Overweight_data.HOLDPLANSCHEDULE.tolist()[0] if \
                    Overweight_data.HOLDPLANSCHEDULE.tolist()[0] else None
                try:
                    data_end = pd.DataFrame(
                        {"holder_name": name_list, "volume_plan_max": max_shanum, "volume_plan_mix": min_shanum},
                        index=[i for i in range(len(name_list))])
                except:
                    continue
                data_end['capitalization'] = values_data.capitalization.values[0]
                data_end = data_end.astype({'volume_plan_max': 'float64', 'volume_plan_mix': 'float64'})
                data_end['change_pct'] = round((data_end['volume_plan_max'] / data_end['capitalization']) * 100, 2)
                data_end['report_date'] = pd.to_datetime(end_date)
                data_end['plan_progress'] = progress_data if progress_data else None
                data_end['holder_direction'] = '增持'
                df = df.append(data_end)

        if pd_is_not_null(df):
            df.reset_index(drop=True, inplace=True)
            df.rename(columns=self.data_schema.get_data_map(self), inplace=True)
            df['entity_id'] = entity.id
            df['timestamp'] = pd.to_datetime(df.report_date)
            df['provider'] = 'emquantapi'
            df['code'] = entity.code

            def generate_id(se):
                holdname = se['holder_name']
                if len(holdname) > 20:
                    holdname = str(holdname).split('、')[0]
                return "{}_{}_{}".format(se['entity_id'], to_time_str(se['timestamp'], fmt=TIME_FORMAT_DAY),
                                         holdname)

            df['id'] = df[['entity_id', 'timestamp', 'holder_name']].apply(generate_id, axis=1)

            df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
        return None


__all__ = ['EmHolderTradePlanRecorder']

if __name__ == '__main__':
    # 上证50
    EmHolderTradePlanRecorder(codes=['050002']).run()
    # JqChinaEtfValuationRecorder(codes=['512290']).run()
