# -*- coding: utf-8 -*-
import enum
from typing import Union

from zvt.api import get_kdata_schema
from zvt.contract import IntervalLevel, AdjustType
from zvt.domain import IndexStock, Stock1dKdata
from zvt.utils import next_date


class PerformanceClass(enum.Enum):
    # 表现比85%好
    best = 0.85
    ok = 0.7
    ordinary = 0.4
    poor = 0


def cal_change(s):
    return (s[-1] - s[0]) / s[0]


def cal_performance(s):
    if s >= PerformanceClass.best.value:
        return PerformanceClass.best.value
    if s >= PerformanceClass.ok.value:
        return PerformanceClass.ok.value
    if s >= PerformanceClass.ordinary.value:
        return PerformanceClass.ordinary.value
    if s >= PerformanceClass.poor.value:
        return PerformanceClass.poor.value


def cal_state(df):
    # 中枢上
    s = df.iloc[-1]
    if s['close'] > s['current_zhongshu_y1'] * 1.1:
        return 1
    # 中枢下
    if s['close'] < s['current_zhongshu_y0']:
        return -1
    return 0


# features ->
# change positive_slope negative_slope current_zhongshu_change
# positive_opposite_slope negative_opposite_slope state

# Y -> [PerformanceClass]
def get_samples(data_schema,
                columns,
                start_timestamp,
                end_timestamp,
                entity_type='stock',
                entity_ids=None,
                predict_range=20,
                level: Union[IntervalLevel, str] = IntervalLevel.LEVEL_1DAY,
                adjust_type: Union[AdjustType, str] = None):
    # features
    x_df = data_schema.query_data(start_timestamp=start_timestamp, end_timestamp=end_timestamp,
                                  entity_ids=entity_ids,
                                  columns=columns,
                                  index=['entity_id', 'timestamp'])
    x_df = x_df.dropna()

    # Y
    kdata_schema = get_kdata_schema(entity_type=entity_type, level=level, adjust_type=adjust_type)
    y_df = kdata_schema.query_data(start_timestamp=end_timestamp,
                                   end_timestamp=next_date(end_timestamp, predict_range), entity_ids=entity_ids,
                                   columns=['entity_id', 'timestamp', 'close'],
                                   index=['entity_id', 'timestamp'])
    y_df = y_df.dropna()

    y_change = y_df.groupby(level=0)['close'].apply(
        lambda x: cal_change(x)).rename('y_change')
    y_change = y_change.rank(pct=True).apply(
        lambda x: cal_performance(x)).rename('y_score')

    print(y_change)
    return x_df.to_numpy(), y_change.loc[x_df.index & y_change.index].to_numpy().tolist()


if __name__ == '__main__':
    df = IndexStock.query_data(entity_id='index_sz_399370')
    entity_ids = df['stock_id'].tolist()
    print(entity_ids)
    X, y = get_samples(data_schema=Stock1dKdata, columns=['entity_id', 'timestamp', 'close'],
                       start_timestamp='2020-01-01', end_timestamp='2020-03-01', entity_ids=entity_ids)

    print(X)
    print(y)
