# -*- coding: utf-8 -*-
import enum
from typing import Union, Type, List

import pandas as pd
from sklearn import preprocessing

from zvt.api import get_kdata_schema
from zvt.api.kdata import default_adjust_type
from zvt.contract import IntervalLevel, AdjustType
from zvt.contract import TradableEntity
from zvt.domain import Stock
from zvt.factors import Stock1dMaStatsFactor
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
        return RelativePerformance.best
    if s >= RelativePerformance.ordinary.value:
        return RelativePerformance.ordinary
    if s >= RelativePerformance.poor.value:
        return RelativePerformance.poor


class MLMachine(object):
    entity_schema: Type[TradableEntity] = None

    training_start_timestamp = "2005-01-01"

    testing_start_timestamp = "2010-01-01"
    testing_end_timestamp = "2011-01-01"

    def __init__(
        self,
        entity_ids=None,
        predict_range=20,
        level: Union[IntervalLevel, str] = IntervalLevel.LEVEL_1DAY,
        adjust_type: Union[AdjustType, str] = None,
        relative_performance: bool = False,
    ) -> None:
        super().__init__()
        self.entity_ids = entity_ids
        self.predict_range = predict_range
        self.level = level
        if not adjust_type:
            adjust_type = default_adjust_type(entity_type=self.entity_schema.__name__)
        self.adjust_type = adjust_type

        self.relative_performance = relative_performance

        self.training_start_timestamp = to_pd_timestamp(self.training_start_timestamp)
        self.testing_start_timestamp = to_pd_timestamp(self.testing_start_timestamp)
        self.testing_end_timestamp = to_pd_timestamp(self.testing_end_timestamp)

        # init training data
        (self.training_x_timestamps, self.training_y_timestamps,) = self.get_x_y_timestamps(
            start_timestamp=self.training_start_timestamp,
            end_timestamp=self.testing_start_timestamp,
        )

        self.training_x_df = self.get_features(self.entity_ids, self.training_x_timestamps)
        self.training_y_df = self.get_labels(
            self.entity_ids,
            x_timestamps=self.training_x_timestamps,
            y_timestamps=self.training_y_timestamps,
        )

        # init test data
        self.testing_x_timestamps, self.testing_y_timestamps = self.get_x_y_timestamps(
            start_timestamp=self.testing_start_timestamp,
            end_timestamp=self.testing_end_timestamp,
        )
        self.testing_x_df = self.get_features(self.entity_ids, self.testing_x_timestamps)
        self.testing_y_df = self.get_labels(
            self.entity_ids,
            x_timestamps=self.testing_x_timestamps,
            y_timestamps=self.testing_y_timestamps,
        )

    def normalize(self):
        if self.category_nominal_features():
            df = self.training_x_df[self.category_nominal_features()]
            enc = preprocessing.OneHotEncoder()
            X = enc.fit_transform(df)

    def ml(self):
        self.normalize()
        print(self.training_x_df)
        print(self.training_y_df)

        X = self.training_x_df.to_numpy()
        y = self.training_y_df.to_numpy().tolist()

        from sklearn.linear_model import SGDClassifier

        clf = SGDClassifier(loss="hinge", penalty="l2", max_iter=5)
        clf.fit(X, y)
        SGDClassifier(max_iter=5)

        clf.predict(self.testing_x_df.to_numpy())

    def get_x_y_timestamps(self, start_timestamp, end_timestamp):
        x_timestamps = []
        y_timestamps = []
        x_timestamp = start_timestamp
        y_timestamp = next_date(x_timestamp, self.predict_range)
        while y_timestamp <= end_timestamp:
            x_timestamps.append(x_timestamp)
            y_timestamps.append(y_timestamp)

            x_timestamp = y_timestamp
            y_timestamp = next_date(x_timestamp, self.predict_range)

        return x_timestamps, y_timestamps

    def category_ordinal_features(self):
        return []

    def category_nominal_features(self):
        return []

    def get_features(self, entity_ids: List[str], timestamps: List[pd.Timestamp]) -> pd.DataFrame:
        """
        result df format:

                                  col1    col2    col3    ...
        entity_id    timestamp
                                  1.2     0.5     0.3     ...
                                  1.0     0.7     0.2     ...

        :param entity_ids: entity id list
        :param timestamps: timestamp list of the features, (entity_id, timestamp) represents one instance x
        :rtype: pd.DataFrame
        """
        raise NotImplementedError

    def get_labels(self, entity_ids, x_timestamps, y_timestamps):
        dfs = []
        for idx, timestamp in enumerate(x_timestamps):
            kdata_schema = get_kdata_schema(
                entity_type=self.entity_schema.__name__.lower(),
                level=self.level,
                adjust_type=self.adjust_type,
            )
            y_df = kdata_schema.query_data(
                start_timestamp=timestamp,
                end_timestamp=y_timestamps[idx],
                entity_ids=entity_ids,
                columns=["entity_id", "timestamp", "close"],
                index=["entity_id", "timestamp"],
            )
            y_df = y_df.dropna()
            y_change = y_df.groupby(level=0)["close"].apply(lambda x: cal_change(x)).rename("y_change")

            if self.relative_performance:
                y_score = y_change.rank(pct=True).apply(lambda x: cal_performance(x)).rename("y_score")
            else:
                y_score = y_change
            df = y_score.to_frame()
            df["timestamp"] = timestamp
            df.set_index("timestamp", append=True)
            dfs.append(df)

        return pd.concat(dfs)


class MyMLMachine(MLMachine):
    entity_schema = Stock

    def get_features(self, entity_ids, timestamps):
        return Stock1dMaStatsFactor.query_data(
            columns=["entity_id", "timestamp", "cycle_tag"],
            filters=[StockTags.timestamp.in_(timestamps)],
        )


if __name__ == "__main__":
    MyMLMachine().ml()

# the __all__ is generated
__all__ = [
    "RelativePerformance",
    "cal_change",
    "cal_performance",
    "MLMachine",
    "MyMLMachine",
]
