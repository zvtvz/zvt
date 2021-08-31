# -*- coding: utf-8 -*-
from typing import List

import pandas as pd

from zvt.api.utils import to_report_period_type, value_to_pct
from zvt.contract import ActorType
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimestampsDataRecorder
from zvt.domain import Stock
from zvt.domain.actor.stock_actor import StockActorSummary
from zvt.recorders.em.em_api import get_ii_holder_report_dates, actor_type_to_org_type, get_ii_summary
from zvt.utils import to_pd_timestamp, to_time_str


# [{'CHANGE_RATIO': -1.045966694333,
#   'IS_COMPLETE': '1',
#   'ORG_TYPE': '07',
#   'REPORT_DATE': '2021-03-31 00:00:00',
#   'SECUCODE': '000338.SZ',
#   'SECURITY_CODE': '000338',
#   'TOTAL_FREE_SHARES': 2598718411,
#   'TOTAL_MARKET_CAP': 49999342227.64,
#   'TOTAL_ORG_NUM': 5,
#   'TOTAL_SHARES_RATIO': 29.51742666}]

class EMStockActorSummaryRecorder(TimestampsDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Stock

    provider = 'em'
    data_schema = StockActorSummary

    def init_timestamps(self, entity_item) -> List[pd.Timestamp]:
        result = get_ii_holder_report_dates(code=entity_item.code)
        if result:
            return [to_pd_timestamp(item['REPORT_DATE']) for item in result]

    def record(self, entity, start, end, size, timestamps):
        for timestamp in timestamps:
            the_date = to_time_str(timestamp)
            self.logger.info(f'to {entity.code} {the_date}')
            for actor_type in ActorType:
                if actor_type == ActorType.private_equity or actor_type == ActorType.individual:
                    continue
                result = get_ii_summary(code=entity.code, report_date=the_date,
                                        org_type=actor_type_to_org_type(actor_type))
                if result:
                    summary_list = [{'id': f'{entity.entity_id}_{the_date}_{actor_type.value}',
                                     'entity_id': entity.entity_id,
                                     'timestamp': timestamp,
                                     'code': entity.code,
                                     'name': entity.name,

                                     'actor_type': actor_type.value,
                                     'actor_count': item['TOTAL_ORG_NUM'],

                                     'report_date': timestamp,
                                     'report_period': to_report_period_type(timestamp),

                                     'change_ratio': value_to_pct(item['CHANGE_RATIO'], default=1),
                                     'is_complete': item['IS_COMPLETE'],
                                     'holding_numbers': item['TOTAL_FREE_SHARES'],
                                     'holding_ratio': value_to_pct(item['TOTAL_SHARES_RATIO'], default=0),
                                     'holding_values': item['TOTAL_MARKET_CAP']
                                     } for item in result]
                    df = pd.DataFrame.from_records(summary_list)
                    df_to_db(data_schema=self.data_schema, df=df, provider=self.provider,
                             force_update=True, drop_duplicates=True)


if __name__ == '__main__':
    EMStockActorSummaryRecorder(codes=['000338']).run()
# the __all__ is generated
__all__ = ['EMStockActorSummaryRecorder']