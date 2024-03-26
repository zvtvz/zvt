# -*- coding: utf-8 -*-
from sklearn.linear_model import SGDClassifier, SGDRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from zvt.ml import MaStockMLMachine


def sgd_classification():
    machine = MaStockMLMachine(data_provider="em", entity_ids=["stock_sz_000001"], label_method="behavior_cls")
    clf = make_pipeline(StandardScaler(), SGDClassifier(max_iter=1000, tol=1e-3))
    machine.train(model=clf)
    machine.predict()
    machine.draw_result(entity_id="stock_sz_000001")


def sgd_regressor():
    machine = MaStockMLMachine(data_provider="em", entity_ids=["stock_sz_000001"], label_method="raw")
    reg = make_pipeline(StandardScaler(), SGDRegressor(max_iter=1000, tol=1e-3))
    machine.train(model=reg)
    machine.predict()
    machine.draw_result(entity_id="stock_sz_000001")


if __name__ == "__main__":
    sgd_classification()
    sgd_regressor()
