# -*- coding: utf-8 -*-
from zvt.api.stats import get_top_performance_by_month
from zvt.domain import Stock1dHfqKdata
from zvt.utils.time_utils import date_time_by_interval, month_end_date, is_same_date


# 每月涨幅前30，市值90%分布在100亿以下
# 重复上榜的有1/4左右
# 连续两个月上榜的1/10左右
def top_tags(data_provider="em", start_timestamp="2020-01-01", end_timestamp="2021-01-01"):
    records = []
    for _, timestamp, df in get_top_performance_by_month(
        start_timestamp=start_timestamp, end_timestamp=end_timestamp, list_days=250, data_provider=data_provider
    ):
        for entity_id in df.index[:30]:
            query_timestamp = timestamp
            while True:
                kdata = Stock1dHfqKdata.query_data(
                    provider=data_provider,
                    entity_id=entity_id,
                    start_timestamp=query_timestamp,
                    order=Stock1dHfqKdata.timestamp.asc(),
                    limit=1,
                    return_type="domain",
                )
                if not kdata or kdata[0].turnover_rate == 0:
                    if is_same_date(query_timestamp, month_end_date(query_timestamp)):
                        break
                    query_timestamp = date_time_by_interval(query_timestamp)
                    continue
                cap = kdata[0].turnover / kdata[0].turnover_rate
                break

            records.append(
                {"entity_id": entity_id, "timestamp": timestamp, "cap": cap, "score": df.loc[entity_id, "score"]}
            )

    return records


if __name__ == "__main__":
    print(top_tags())
