# -*- coding: utf-8 -*-
from typing import List

import pandas as pd

from zvt.api.utils import to_report_period_type, value_to_pct
from zvt.contract import ActorType
from zvt.contract.api import df_to_db
from zvt.contract.recorder import TimestampsDataRecorder
from zvt.domain import Stock, ActorMeta
from zvt.domain.actor.stock_actor import StockInstitutionalInvestorHolder
from zvt.recorders.em.em_api import get_ii_holder_report_dates, get_ii_holder, actor_type_to_org_type
from zvt.utils import to_pd_timestamp, to_time_str


# {'END_DATE': '2021-03-31 00:00:00',
#   'HOLDER_CODE': '10015776',
#   'HOLDER_CODE_OLD': '80010104',
#   'HOLDER_NAME': '香港中央结算代理人有限公司',
#   'HOLDER_RANK': 1,
#   'HOLD_NUM': 1938664086,
#   'HOLD_NUM_RATIO': 24.44,
#   'HOLD_RATIO_QOQ': '0.04093328',
#   'IS_HOLDORG': '1',
#   'SECUCODE': '000338.SZ'}

#  {'END_DATE': '2021-03-31 00:00:00',
#   'FREE_HOLDNUM_RATIO': 0.631949916991,
#   'FREE_RATIO_QOQ': '-5.33046217',
#   'HOLDER_CODE': '161606',
#   'HOLDER_CODE_OLD': '161606',
#   'HOLDER_NAME': '交通银行-融通行业景气证券投资基金',
#   'HOLDER_RANK': 10,
#   'HOLD_NUM': 39100990,
#   'IS_HOLDORG': '1',
#   'SECUCODE': '000338.SZ'}


class EMStockIIRecorder(TimestampsDataRecorder):
    entity_provider = "em"
    entity_schema = Stock

    provider = "em"
    data_schema = StockInstitutionalInvestorHolder

    def init_timestamps(self, entity_item) -> List[pd.Timestamp]:
        result = get_ii_holder_report_dates(code=entity_item.code)
        if result:
            return [to_pd_timestamp(item["REPORT_DATE"]) for item in result]

    def record(self, entity, start, end, size, timestamps):
        for timestamp in timestamps:
            the_date = to_time_str(timestamp)
            self.logger.info(f"to {entity.code} {the_date}")
            for actor_type in ActorType:
                if actor_type == ActorType.private_equity or actor_type == ActorType.individual:
                    continue
                result = get_ii_holder(
                    code=entity.code, report_date=the_date, org_type=actor_type_to_org_type(actor_type)
                )
                if result:
                    holders = [
                        {
                            "id": f'{entity.entity_id}_{the_date}_{actor_type.value}_cn_{item["HOLDER_CODE"]}',
                            "entity_id": entity.entity_id,
                            "timestamp": timestamp,
                            "code": entity.code,
                            "name": entity.name,
                            "actor_id": f'{actor_type.value}_cn_{item["HOLDER_CODE"]}',
                            "actor_type": actor_type.value,
                            "actor_code": item["HOLDER_CODE"],
                            "actor_name": f'{item["HOLDER_NAME"]}',
                            "report_date": timestamp,
                            "report_period": to_report_period_type(timestamp),
                            "holding_numbers": item["TOTAL_SHARES"],
                            "holding_ratio": value_to_pct(item["FREESHARES_RATIO"], 0),
                            "holding_values": item["HOLD_VALUE"],
                        }
                        for item in result
                    ]
                    df = pd.DataFrame.from_records(holders)
                    df_to_db(
                        data_schema=self.data_schema,
                        df=df,
                        provider=self.provider,
                        force_update=True,
                        drop_duplicates=True,
                    )

                    # save the actors
                    actors = [
                        {
                            "id": f'{actor_type.value}_cn_{item["HOLDER_CODE"]}',
                            "entity_id": f'{actor_type.value}_cn_{item["HOLDER_CODE"]}',
                            "entity_type": actor_type.value,
                            "exchange": "cn",
                            "code": item["HOLDER_CODE"],
                            "name": f'{item["HOLDER_NAME"]}',
                        }
                        for item in result
                    ]
                    df1 = pd.DataFrame.from_records(actors)
                    df_to_db(
                        data_schema=ActorMeta, df=df1, provider=self.provider, force_update=False, drop_duplicates=True
                    )


if __name__ == "__main__":
    EMStockIIRecorder(codes=["000562"]).run()
# the __all__ is generated
__all__ = ["EMStockIIRecorder"]
