# -*- coding: utf-8 -*-
from typing import List

from zvt.contract import Exchange
from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.domain import Stock
from zvt.recorders.em import em_api
from zvt.utils.pd_utils import pd_is_not_null
from zvt.utils.time_utils import to_pd_timestamp


class EMStockRecorder(Recorder):
    provider = "em"
    data_schema = Stock

    def run(self):
        for exchange in [Exchange.sh, Exchange.sz, Exchange.bj]:
            df = em_api.get_tradable_list(entity_type="stock", exchange=exchange)

            if pd_is_not_null(df):
                df["total_cap"] = df["total_cap"].fillna(0)
                df["float_cap"] = df["float_cap"].fillna(0)

                self.logger.info(df.head())
                df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)

                for item in df[["id", "name", "total_cap", "float_cap"]].values.tolist():
                    entity_id = item[0]
                    datas: List[Stock] = Stock.query_data(
                        entity_id=entity_id, return_type="domain", session=self.session
                    )

                    if datas:
                        entity_domain = datas[0]

                        if "退" in entity_domain.name:
                            self.logger.info(f"Ignore: {entity_domain.entity_id} {entity_domain.name} {item}")
                            continue

                        entity_domain.name = item[1]
                        entity_domain.total_cap = item[2]
                        entity_domain.float_cap = item[3]

                        if not entity_domain.list_date:
                            basic_info = em_api.get_basic_info(entity_id=entity_id, session=self.http_session)
                            self.logger.info(f"basic info: {basic_info}")
                            if basic_info:
                                entity_domain.timestamp = to_pd_timestamp(basic_info.get("LISTING_DATE"))
                                entity_domain.list_date = to_pd_timestamp(basic_info.get("LISTING_DATE"))
                            else:
                                entity_domain.name = entity_domain.name + "退市"
                        self.session.add(entity_domain)
                        self.session.commit()


if __name__ == "__main__":
    recorder = EMStockRecorder()
    recorder.run()


# the __all__ is generated
__all__ = ["EMStockRecorder"]
