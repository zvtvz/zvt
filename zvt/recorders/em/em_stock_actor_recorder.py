# -*- coding: utf-8 -*-
from typing import List

import pandas as pd

from zvt.api import to_report_period_type
from zvt.contract import ActorType
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimestampsDataRecorder
from zvt.domain import Stock
from zvt.domain.actor.stock_actor import StockInstitutionalInvestorHolder
from zvt.recorders.em.common import get_ii_holder_report_dates, get_ii_holder, actor_type_to_org_type
from zvt.utils import to_pd_timestamp, to_time_str


class EMStockActorRecorder(TimestampsDataRecorder):
    entity_provider = 'joinquant'
    entity_schema = Stock

    provider = 'em'
    data_schema = StockInstitutionalInvestorHolder

    def init_timestamps(self, entity_item) -> List[pd.Timestamp]:
        result = get_ii_holder_report_dates(code=entity_item.code)
        return [to_pd_timestamp(item['REPORT_DATE']) for item in result]

    def record(self, entity, start, end, size, timestamps):
        for timestamp in timestamps:
            the_date = to_time_str(timestamp)
            for actor_type in ActorType:
                if actor_type == ActorType.private_equity:
                    continue
                result = get_ii_holder(code=entity.code, report_date=the_date,
                                       org_type=actor_type_to_org_type(actor_type))
                if result:
                    holders = [{'id': f'{entity.entity_id}_{the_date}_{actor_type.value}_cn_{item["HOLDER_CODE"]}',
                                'entity_id': entity.entity_id,
                                'timestamp': timestamp,
                                'code': entity.code,
                                'name': entity.name,

                                'actor_id': f'{actor_type.value}_cn_{item["HOLDER_CODE"]}',
                                'actor_type': actor_type.value,
                                'actor_code': item["HOLDER_CODE"],
                                'actor_name': f'{item["HOLDER_NAME"]}',

                                'report_date': timestamp,
                                'report_period': to_report_period_type(timestamp),

                                'holding_numbers': item['TOTAL_SHARES'],
                                'holding_ratio': item['FREESHARES_RATIO'],
                                'holding_values': item['HOLD_VALUE']
                                } for item in result]
                    df = pd.DataFrame.from_records(holders)
                    df_to_db(data_schema=self.data_schema, df=df, provider=self.provider,
                             force_update=True)


if __name__ == '__main__':
    EMStockActorRecorder(codes=['000338']).run()
