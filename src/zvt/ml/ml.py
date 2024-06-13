# -*- coding: utf-8 -*-
import logging
from typing import Union, Type, List

import pandas as pd
from sklearn.linear_model import LinearRegression, SGDRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from zvt.api.kdata import default_adjust_type, get_kdata
from zvt.contract import IntervalLevel, AdjustType
from zvt.contract import TradableEntity
from zvt.contract.drawer import Drawer
from zvt.domain import Stock
from zvt.factors.transformers import MaTransformer
from zvt.ml.lables import RelativePerformance, BehaviorCategory
from zvt.utils.pd_utils import group_by_entity_id, normalize_group_compute_result, pd_is_not_null
from zvt.utils.time_utils import to_pd_timestamp

logger = logging.getLogger(__name__)


def cal_change(s: pd.Series, predict_range):
    return s.pct_change(periods=-predict_range)


def cal_behavior_cls(s: pd.Series, predict_range):
    return s.pct_change(periods=-predict_range).apply(
        lambda x: BehaviorCategory.up.value if x > 0 else BehaviorCategory.down.value
    )


def cal_predict(s: pd.Series, predict_range):
    return s.shift(periods=-predict_range)


def cal_relative_performance(s: pd.Series):
    if s >= RelativePerformance.best.value:
        return RelativePerformance.best
    if s >= RelativePerformance.ordinary.value:
        return RelativePerformance.ordinary
    if s >= RelativePerformance.poor.value:
        return RelativePerformance.poor


class MLMachine(object):
    entity_schema: Type[TradableEntity] = None

    def __init__(
        self,
        entity_ids: List[str] = None,
        start_timestamp: Union[str, pd.Timestamp] = "2015-01-01",
        end_timestamp: Union[str, pd.Timestamp] = "2021-12-01",
        predict_start_timestamp: Union[str, pd.Timestamp] = "2021-06-01",
        predict_steps: int = 20,
        level: Union[IntervalLevel, str] = IntervalLevel.LEVEL_1DAY,
        adjust_type: Union[AdjustType, str] = None,
        data_provider: str = None,
        label_method: str = "raw",
    ) -> None:
        """

        :param entity_ids:
        :param start_timestamp:
        :param end_timestamp:
        :param predict_start_timestamp:
        :param predict_steps:
        :param level:
        :param adjust_type:
        :param data_provider:
        :param label_method: raw, change, or behavior_cls
        """
        super().__init__()
        self.entity_ids = entity_ids
        self.start_timestamp = to_pd_timestamp(start_timestamp)
        self.end_timestamp = to_pd_timestamp(end_timestamp)
        self.predict_start_timestamp = to_pd_timestamp(predict_start_timestamp)
        assert self.start_timestamp < self.predict_start_timestamp < self.end_timestamp
        self.predict_steps = predict_steps

        self.level = level
        if not adjust_type:
            adjust_type = default_adjust_type(entity_type=self.entity_schema.__name__)
        self.adjust_type = adjust_type

        self.data_provider = data_provider
        self.label_method = label_method

        self.kdata_df = self.build_kdata()
        if not pd_is_not_null(self.kdata_df):
            logger.error("not kdta")
            assert False

        self.feature_df = self.build_feature(self.entity_ids, self.start_timestamp, self.end_timestamp)
        # drop na in feature
        self.feature_df = self.feature_df.dropna()
        self.feature_names = list(set(self.feature_df.columns) - {"entity_id", "timestamp"})
        self.feature_df = self.feature_df.loc[:, self.feature_names]

        self.label_ser = self.build_label()
        # keep same index with feature df
        self.label_ser = self.label_ser.loc[self.feature_df.index]
        self.label_name = self.label_ser.name

        self.training_X, self.training_y, self.testing_X, self.testing_y = self.split_data()

        logger.info(self.training_X)
        logger.info(self.training_y)

        self.model = None
        self.pred_y = None

    def split_data(self):
        training_x = self.feature_df[self.feature_df.index.get_level_values("timestamp") < self.predict_start_timestamp]
        training_y = self.label_ser[self.label_ser.index.get_level_values("timestamp") < self.predict_start_timestamp]

        testing_x = self.feature_df[self.feature_df.index.get_level_values("timestamp") >= self.predict_start_timestamp]
        testing_y = self.label_ser[self.label_ser.index.get_level_values("timestamp") >= self.predict_start_timestamp]
        return training_x, training_y, testing_x, testing_y

    def build_kdata(self):
        columns = ["entity_id", "timestamp", "close"]
        return get_kdata(
            entity_ids=self.entity_ids,
            start_timestamp=self.start_timestamp,
            end_timestamp=self.end_timestamp,
            columns=columns,
            level=self.level,
            adjust_type=self.adjust_type,
            provider=self.data_provider,
            index=["entity_id", "timestamp"],
            drop_index_col=True,
        )

    def build_label(self):
        label_name = f"y_{self.predict_steps}"
        if self.label_method == "raw":
            y = (
                group_by_entity_id(self.kdata_df["close"])
                .apply(lambda x: cal_predict(x, self.predict_steps))
                .rename(label_name)
            )
        elif self.label_method == "change":
            y = (
                group_by_entity_id(self.kdata_df["close"])
                .apply(lambda x: cal_change(x, self.predict_steps))
                .rename(label_name)
            )
        elif self.label_method == "behavior_cls":
            y = (
                group_by_entity_id(self.kdata_df["close"])
                .apply(lambda x: cal_behavior_cls(x, self.predict_steps))
                .rename(label_name)
            )
        else:
            assert False
        y = normalize_group_compute_result(y)

        return y

    def train(self, model=LinearRegression(), **params):
        self.model = model.fit(self.training_X, self.training_y, **params)
        return self.model

    def draw_result(self, entity_id):
        if self.label_method == "raw":
            df = self.kdata_df.loc[[entity_id], ["close"]].copy()

            pred_df = self.pred_y.to_frame(name="pred_close")
            pred_df = pred_df.loc[[entity_id], :].shift(self.predict_steps)

            drawer = Drawer(
                main_df=df,
                factor_df_list=[pred_df],
            )
            drawer.draw_line(show=True)
        else:
            pred_df = self.pred_y.to_frame(name="pred_result").loc[[entity_id], :]
            df = self.testing_y.to_frame(name="real_result").loc[[entity_id], :].join(pred_df, how="outer")

            drawer = Drawer(main_df=df)
            drawer.draw_table()

    def predict(self):
        predictions = self.model.predict(self.testing_X)
        self.pred_y = pd.Series(data=predictions, index=self.testing_y.index)
        # explained_variance_score(self.testing_y, self.pred_y)
        # mean_squared_error(self.testing_y, self.pred_y)

    def build_feature(
        self, entity_ids: List[str], start_timestamp: pd.Timestamp, end_timestamp: pd.Timestamp
    ) -> pd.DataFrame:
        """
        result df format
                                  col1    col2    col3    ...
        entity_id    timestamp
                                  1.2     0.5     0.3     ...
                                  1.0     0.7     0.2     ...

        :param entity_ids: entity id list
        :param start_timestamp:
        :param end_timestamp:
        :rtype: pd.DataFrame
        """
        raise NotImplementedError


class StockMLMachine(MLMachine):
    entity_schema = Stock


class MaStockMLMachine(StockMLMachine):
    def build_feature(
        self, entity_ids: List[str], start_timestamp: pd.Timestamp, end_timestamp: pd.Timestamp
    ) -> pd.DataFrame:
        """

        :param entity_ids:
        :param start_timestamp:
        :param end_timestamp:
        :return:
        """
        t = MaTransformer(windows=[5, 10, 120, 250])
        df = t.transform(self.kdata_df)
        return df


if __name__ == "__main__":
    machine = MaStockMLMachine(entity_ids=["stock_sz_000001"])
    reg = make_pipeline(StandardScaler(), SGDRegressor(max_iter=1000, tol=1e-3))
    machine.train(model=reg)
    machine.predict()
    machine.draw_result(entity_id="stock_sz_000001")

# the __all__ is generated
__all__ = [
    "cal_change",
    "cal_behavior_cls",
    "cal_predict",
    "cal_relative_performance",
    "MLMachine",
    "StockMLMachine",
    "MaStockMLMachine",
]
