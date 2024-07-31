# -*- coding: utf-8 -*-
from zvt.domain import StockQuote
from zvt.utils.pd_utils import pd_is_not_null


def get_limit_up():
    df = StockQuote.query_data(filters=[StockQuote.is_limit_up], columns=[StockQuote.entity_id])
    if pd_is_not_null(df):
        return df["entity_id"].to_list()


def get_top_50():
    df = StockQuote.query_data(columns=[StockQuote.entity_id], order=StockQuote.change_pct.desc(), limit=50)
    if pd_is_not_null(df):
        return df["entity_id"].to_list()


def get_limit_down():
    df = StockQuote.query_data(filters=[StockQuote.is_limit_down], columns=[StockQuote.entity_id])
    if pd_is_not_null(df):
        return df["entity_id"].to_list()


if __name__ == "__main__":
    print(get_limit_up())
    print(get_limit_down())
    print(get_top_50())


# the __all__ is generated
__all__ = ["get_limit_up", "get_top_50", "get_limit_down"]
