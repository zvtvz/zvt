# -*- coding: utf-8 -*-

import pandas as pd

from zvt.contract.api import df_to_db
from zvt.contract.recorder import FixedCycleDataRecorder
from zvt.domain import Stock, DragonAndTiger
from zvt.recorders.em import em_api
from zvt.utils.time_utils import to_pd_timestamp, to_time_str, TIME_FORMAT_DAY, date_time_by_interval

{
    "TRADE_ID": "3066028",
    "TRADE_DATE": "2018-10-31 00:00:00",
    # 原因
    "EXPLANATION": "日涨幅偏离值达到7%的前五只证券",
    "SECUCODE": "000989.SZ",
    "SECURITY_CODE": "000989",
    "SECURITY_NAME_ABBR": "九芝堂",
    # 成交额
    "ACCUM_AMOUNT": 361620405,
    # 涨跌幅
    "CHANGE_RATE": 10.0324,
    # 净买入
    "NET_BUY": 101274668.45,
    "BUY_BUY_TOTAL": 150153489.67,
    "BUY_SELL_TOTAL": 6319593.12,
    "BUY_RATIO_TOTAL": 41.810172373984,
    "SELL_BUY_TOTAL": 31575718.69,
    "SELL_SELL_TOTAL": 49862244.22,
    "SELL_RATIO_TOTAL": 13.80437760972,
    # 买入金额
    "BUY_TOTAL": 151194114.67,
    # 卖出金额
    "SELL_TOTAL": 49919446.22,
    "BUY_TOTAL_NET": 143833896.55,
    "SELL_TOTAL_NET": -18286525.53,
    "LIST": [
        {
            "TRADE_DIRECTION": "0",
            "RANK": 1,
            "OPERATEDEPT_NAME": "西藏东方财富证券股份有限公司武汉建设大道证券营业部",
            "BUY_AMT_REAL": 92701932.28,
            "SELL_AMT_REAL": 0,
            "BUY_RATIO": 25.635149731111,
            "SELL_RATIO": 0,
            "NET": 92701932.28,
        },
        {
            "TRADE_DIRECTION": "1",
            "RANK": 1,
            "OPERATEDEPT_NAME": "中泰证券股份有限公司惠州文明一路证券营业部",
            "BUY_AMT_REAL": 0,
            "SELL_AMT_REAL": 20806577,
            "BUY_RATIO": 0,
            "SELL_RATIO": 5.753706569739,
            "NET": -20806577,
        },
        {
            "TRADE_DIRECTION": "1",
            "RANK": 2,
            "OPERATEDEPT_NAME": "中泰证券股份有限公司深圳泰然九路证券营业部",
            "BUY_AMT_REAL": 0,
            "SELL_AMT_REAL": 9999269.85,
            "BUY_RATIO": 0,
            "SELL_RATIO": 2.765128768107,
            "NET": -9999269.85,
        },
        {
            "TRADE_DIRECTION": "0",
            "RANK": 2,
            "OPERATEDEPT_NAME": "深股通专用",
            "BUY_AMT_REAL": 30535093.69,
            "SELL_AMT_REAL": 6262391.12,
            "BUY_RATIO": 8.443963135874,
            "SELL_RATIO": 1.731758228632,
            "NET": 24272702.57,
        },
        {
            "TRADE_DIRECTION": "0",
            "RANK": 3,
            "OPERATEDEPT_NAME": "联储证券有限责任公司郑州文化路证券营业部",
            "BUY_AMT_REAL": 10185863,
            "SELL_AMT_REAL": 45600,
            "BUY_RATIO": 2.816727944321,
            "SELL_RATIO": 0.012609907895,
            "NET": 10140263,
        },
        {
            "TRADE_DIRECTION": "1",
            "RANK": 3,
            "OPERATEDEPT_NAME": "中信证券股份有限公司杭州文三路证券营业部",
            "BUY_AMT_REAL": 1040625,
            "SELL_AMT_REAL": 7246342.25,
            "BUY_RATIO": 0.287767223755,
            "SELL_RATIO": 2.003853253248,
            "NET": -6205717.25,
        },
        {
            "TRADE_DIRECTION": "0",
            "RANK": 4,
            "OPERATEDEPT_NAME": "华泰证券股份有限公司北京广渠门内大街证券营业部",
            "BUY_AMT_REAL": 9089939.7,
            "SELL_AMT_REAL": 0,
            "BUY_RATIO": 2.513668912018,
            "SELL_RATIO": 0,
            "NET": 9089939.7,
        },
        {
            "TRADE_DIRECTION": "1",
            "RANK": 4,
            "OPERATEDEPT_NAME": "深股通专用",
            "BUY_AMT_REAL": 30535093.69,
            "SELL_AMT_REAL": 6262391.12,
            "BUY_RATIO": 8.443963135874,
            "SELL_RATIO": 1.731758228632,
            "NET": 24272702.57,
        },
        {
            "TRADE_DIRECTION": "1",
            "RANK": 5,
            "OPERATEDEPT_NAME": "英大证券有限责任公司深圳园岭三街证券营业部",
            "BUY_AMT_REAL": 0,
            "SELL_AMT_REAL": 5547664,
            "BUY_RATIO": 0,
            "SELL_RATIO": 1.534112545447,
            "NET": -5547664,
        },
        {
            "TRADE_DIRECTION": "0",
            "RANK": 5,
            "OPERATEDEPT_NAME": "申万宏源证券有限公司南宁长湖路证券营业部",
            "BUY_AMT_REAL": 7640661,
            "SELL_AMT_REAL": 11602,
            "BUY_RATIO": 2.112895426905,
            "SELL_RATIO": 0.003208336653,
            "NET": 7629059,
        },
    ],
}


class EMDragonAndTigerRecorder(FixedCycleDataRecorder):
    entity_provider = "em"
    entity_schema = Stock

    provider = "em"
    data_schema = DragonAndTiger

    def record(self, entity, start, end, size, timestamps):
        if start:
            start_date = to_time_str(date_time_by_interval(start))
        else:
            start_date = None
        datas = em_api.get_dragon_and_tiger(code=entity.code, start_date=start_date)
        if datas:
            records = []
            for data in datas:
                timestamp = to_pd_timestamp(data["TRADE_DATE"])
                record = {
                    "id": "{}_{}_{}".format(entity.id, data["TRADE_ID"], to_time_str(timestamp, fmt=TIME_FORMAT_DAY)),
                    "entity_id": entity.id,
                    "timestamp": timestamp,
                    "code": entity.code,
                    "name": entity.name,
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
            self.logger.info(f"no data for {entity.id}")


if __name__ == "__main__":
    EMDragonAndTigerRecorder(sleeping_time=0.1, exchanges=["sh"]).run()


# the __all__ is generated
__all__ = ["EMDragonAndTigerRecorder"]
