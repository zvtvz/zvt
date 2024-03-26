# -*- coding: utf-8 -*-
from sklearn.linear_model import SGDClassifier, SGDRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from zvt.contract import AdjustType
from zvt.ml import MaStockMLMachine

start_timestamp = "2015-01-01"
end_timestamp = "2019-01-01"
predict_start_timestamp = "2018-06-01"


def test_sgd_classification():
    machine = MaStockMLMachine(
        data_provider="joinquant",
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        predict_start_timestamp=predict_start_timestamp,
        entity_ids=["stock_sz_000001"],
        label_method="behavior_cls",
        adjust_type=AdjustType.qfq,
    )
    clf = make_pipeline(StandardScaler(), SGDClassifier(max_iter=1000, tol=1e-3))
    machine.train(model=clf)
    machine.predict()
    machine.draw_result(entity_id="stock_sz_000001")


def test_sgd_regressor():
    machine = MaStockMLMachine(
        data_provider="joinquant",
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        predict_start_timestamp=predict_start_timestamp,
        entity_ids=["stock_sz_000001"],
        label_method="raw",
        adjust_type=AdjustType.qfq,
    )
    reg = make_pipeline(StandardScaler(), SGDRegressor(max_iter=1000, tol=1e-3))
    machine.train(model=reg)
    machine.predict()
    machine.draw_result(entity_id="stock_sz_000001")
