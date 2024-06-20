# -*- coding: utf-8 -*-
from sqlalchemy import func

from zvt.api.selector import get_entity_ids_by_filter
from zvt.contract import Exchange
from zvt.domain import Stock, BlockStock
from zvt.recorders.em import em_api
from zvt.tag.tag_schemas import StockTags


def query_json():

    df = StockTags.query_data(
        filters=[func.json_extract(StockTags.sub_tags, '$."低空经济"') != None], columns=[StockTags.sub_tags]
    )
    print(df)


def get_stocks_has_tag():
    df = StockTags.query_data(filters=[StockTags.latest.is_(True)], columns=[StockTags.entity_id])
    return df["entity_id"].tolist()


def get_stocks_without_tag():
    entity_ids = get_entity_ids_by_filter(provider="em", ignore_delist=True, ignore_st=True, ignore_new_stock=False)
    stocks_has_tag = get_stocks_has_tag()
    return list(set(entity_ids) - set(stocks_has_tag))


def get_all_delist_stocks():
    stocks = []
    df1 = em_api.get_tradable_list(entity_type="stock", exchange=Exchange.sh)
    stocks = stocks + df1["entity_id"].tolist()
    df2 = em_api.get_tradable_list(entity_type="stock", exchange=Exchange.sz)
    stocks = stocks + df2["entity_id"].tolist()
    df3 = em_api.get_tradable_list(entity_type="stock", exchange=Exchange.bj)
    stocks = stocks + df3["entity_id"].tolist()
    return stocks


def get_block_stocks(name="低空经济"):
    df = BlockStock.query_data(provider="em", filters=[BlockStock.name == name], columns=[BlockStock.stock_id])
    return df["stock_id"].tolist()


def get_sub_tag_stocks(tag="低空经济"):
    df = StockTags.query_data(
        provider="zvt",
        filters=[func.json_extract(StockTags.sub_tags, f'$."{tag}"') != None],
        columns=[StockTags.entity_id],
    )
    return df["entity_id"].tolist()


if __name__ == "__main__":
    # a = get_block_stocks()
    # b = get_sub_tag_stocks()
    # print(set(a) - set(b))
    print(Stock.query_data(provider="em", return_type="dict"))
