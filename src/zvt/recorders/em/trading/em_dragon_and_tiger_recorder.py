# -*- coding: utf-8 -*-

import pandas as pd

from zvt.contract.api import df_to_db
from zvt.contract.recorder import Recorder
from zvt.domain import DragonAndTiger
from zvt.recorders.em import em_api
from zvt.utils.time_utils import to_pd_timestamp, to_date_time_str, TIME_FORMAT_DAY, date_time_by_interval, current_date


class EMDragonAndTigerRecorder(Recorder):
    provider = "em"
    data_schema = DragonAndTiger

    def run(self):
        latest_infos = DragonAndTiger.query_data(
            provider=self.provider, order=DragonAndTiger.timestamp.desc(), limit=1, return_type="domain"
        )
        if latest_infos:
            start_date = latest_infos[0].timestamp
        else:
            start_date = date_time_by_interval(current_date(), -10)

        dragon_list = em_api.get_dragon_and_tiger_list(start_date=start_date)

        entity_list = [{"code": data["SECURITY_CODE"], "exchange": data["MARKET"].lower()} for data in dragon_list]
        df = pd.DataFrame(entity_list)
        unique_df = df.drop_duplicates(subset=["code"])
        unique_list = unique_df.to_dict("records")

        self.logger.info("Get dragon and tiger for entities: %s", unique_list)
        for entity in unique_list:
            code = entity["code"]
            entity_id = f"stock_{entity['exchange']}_{entity['code']}"

            datas = em_api.get_dragon_and_tiger(code=entity["code"], start_date=start_date)
            if datas:
                records = []
                for data in datas:
                    timestamp = to_pd_timestamp(data["TRADE_DATE"])
                    record = {
                        "id": f"{entity_id}_{data['TRADE_ID']}_{to_date_time_str(timestamp, fmt=TIME_FORMAT_DAY)}",
                        "entity_id": entity_id,
                        "timestamp": timestamp,
                        "code": code,
                        "name": data["SECURITY_NAME_ABBR"],
                        "reason": data["EXPLANATION"],
                        "turnover": data["ACCUM_AMOUNT"],
                        "change_pct": data["CHANGE_RATE"],
                        "net_in": data["NET_BUY"],
                    }

                    # 营业部列表
                    deps = data["LIST"]
                    for dep in deps:
                        flag = "" if dep["TRADE_DIRECTION"] == "0" else "_"
                        rank = dep["RANK"]
                        dep_name = f"dep{flag}{rank}"
                        dep_in = f"{dep_name}_in"
                        dep_out = f"{dep_name}_out"
                        dep_rate = f"{dep_name}_rate"

                        record[dep_name] = dep["OPERATEDEPT_NAME"]
                        record[dep_in] = dep["BUY_AMT_REAL"]
                        record[dep_out] = dep["SELL_AMT_REAL"]
                        record[dep_rate] = (dep["BUY_RATIO"] if dep["BUY_RATIO"] else 0) - (
                            dep["SELL_RATIO"] if dep["SELL_RATIO"] else 0
                        )

                    records.append(record)
                df = pd.DataFrame.from_records(records)
                df_to_db(df=df, data_schema=self.data_schema, provider=self.provider, force_update=self.force_update)
            else:
                self.logger.info(f"no data for {entity_id}")


if __name__ == "__main__":
    EMDragonAndTigerRecorder(sleeping_time=2).run()


# the __all__ is generated
__all__ = ["EMDragonAndTigerRecorder"]
