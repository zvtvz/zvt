# -*- coding: utf-8 -*-
import enum
from typing import Union, Type

import pandas as pd

from zvt.api import get_kdata_schema
from zvt.contract import IntervalLevel, AdjustType
from zvt.contract import TradableEntity
from zvt.domain import Stock
from zvt.tag.dataset.stock_tags import StockTags
from zvt.utils import next_date, to_pd_timestamp


class RelativePerformance(enum.Enum):
    # 表现比90%好
    best = 0.9
    ordinary = 0.5
    poor = 0


def cal_change(s):
    return (s[-1] - s[0]) / s[0]


def cal_performance(s):
    if s >= RelativePerformance.best.value:
        return RelativePerformance.best.value
    if s >= RelativePerformance.ordinary.value:
        return RelativePerformance.ordinary.value
    if s >= RelativePerformance.poor.value:
        return RelativePerformance.poor.value


def get_performance(x_timestamp,
                    entity_type='stock',
                    entity_ids=None,
                    predict_range=20,
                    level: Union[IntervalLevel, str] = IntervalLevel.LEVEL_1DAY,
                    adjust_type: Union[AdjustType, str] = None):
    kdata_schema = get_kdata_schema(entity_type=entity_type, level=level, adjust_type=adjust_type)
    y_df = kdata_schema.query_data(start_timestamp=x_timestamp,
                                   end_timestamp=next_date(x_timestamp, predict_range), entity_ids=entity_ids,
                                   columns=['entity_id', 'timestamp', 'close'],
                                   index=['entity_id', 'timestamp'])
    y_df = y_df.dropna()
    y_change = y_df.groupby(level=0)['close'].apply(
        lambda x: cal_change(x)).rename('y_change')
    y_score = y_change.rank(pct=True).apply(
        lambda x: cal_performance(x)).rename('y_score')

    df = y_score.to_frame()
    df['timestamp'] = x_timestamp
    df.set_index('timestamp', append=True)

    return df


def get_samples(data_schema,
                columns,
                x_timestamp,
                entity_type='stock',
                entity_ids=None,
                predict_range=20,
                level: Union[IntervalLevel, str] = IntervalLevel.LEVEL_1DAY,
                adjust_type: Union[AdjustType, str] = None):
    # features
    x_df = data_schema.query_data(start_timestamp=x_timestamp, end_timestamp=x_timestamp, entity_ids=entity_ids,
                                  columns=columns, index=['entity_id'])
    x_df = x_df.dropna()

    # Y
    y = get_performance(x_timestamp=x_timestamp, entity_type=entity_type, entity_ids=entity_ids,
                        predict_range=predict_range, level=level, adjust_type=adjust_type)
    index = x_df.index & y.index
    print(index)
    return x_df.loc[index].to_numpy(), y.loc[index].to_numpy().tolist()


class MLMachine(object):
    entity_schema: Type[TradableEntity] = None

    sample_start_timestamp = '2005-01-01'

    test_start_timestamp = '2010-01-01'

    def __init__(self, entity_ids=None, predict_range=20, level: Union[IntervalLevel, str] = IntervalLevel.LEVEL_1DAY,
                 adjust_type: Union[AdjustType, str] = None) -> None:
        super().__init__()
        self.entity_ids = entity_ids
        self.predict_range = predict_range
        self.level = level
        if not adjust_type and self.entity_schema == Stock:
            self.adjust_type = AdjustType.hfq
        else:
            self.adjust_type = adjust_type

        self.sample_start_timestamp = to_pd_timestamp(self.sample_start_timestamp)
        self.test_start_timestamp = to_pd_timestamp(self.test_start_timestamp)

        self.x_timestamps, self.y_timestamps = self.get_x_y_timestamps()

        self.x_df = self.get_features(self.entity_ids, self.x_timestamps)
        self.y_df = self.get_labels(self.entity_ids, x_timestamps=self.x_timestamps, y_timestamps=self.y_timestamps)

    def ml(self):
        print(self.x_df)
        print(self.y_df)

    def get_x_y_timestamps(self):
        x_timestamps = []
        y_timestamps = []
        x_timestamp = self.sample_start_timestamp
        y_timestamp = next_date(x_timestamp, self.predict_range)
        while y_timestamp <= self.test_start_timestamp:
            x_timestamps.append(x_timestamp)
            y_timestamps.append(y_timestamp)

            x_timestamp = y_timestamp
            y_timestamp = next_date(x_timestamp, self.predict_range)

        return y_timestamps, y_timestamps

    def get_features(self, entity_ids, timestamps):
        raise NotImplementedError

    def get_labels(self, entity_ids, x_timestamps, y_timestamps):
        dfs = []
        for idx, timestamp in enumerate(x_timestamps):
            kdata_schema = get_kdata_schema(entity_type=self.entity_schema.__name__.lower(), level=self.level,
                                            adjust_type=self.adjust_type)
            y_df = kdata_schema.query_data(start_timestamp=timestamp,
                                           end_timestamp=y_timestamps[idx],
                                           entity_ids=entity_ids,
                                           columns=['entity_id', 'timestamp', 'close'],
                                           index=['entity_id', 'timestamp'])
            y_df = y_df.dropna()
            y_change = y_df.groupby(level=0)['close'].apply(
                lambda x: cal_change(x)).rename('y_change')
            y_score = y_change.rank(pct=True).apply(
                lambda x: cal_performance(x)).rename('y_score')

            df = y_score.to_frame()
            df['timestamp'] = timestamp
            df.set_index('timestamp', append=True)
            dfs.append(df)

        return pd.concat(dfs)

    def make_samples(self):
        pass


class MyMLMachine(MLMachine):
    entity_schema = Stock

    def get_features(self, entity_ids, timestamps):
        return StockTags.query_data(columns=['entity_id', 'timestamp', 'cycle_tag'],
                                    filters=[StockTags.timestamp.in_(timestamps)])


if __name__ == '__main__':
    MyMLMachine().ml()
