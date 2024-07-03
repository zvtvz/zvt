import platform
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page

import zvt.contract.api as contract_api
import zvt.trading.trading_service as trading_service
from zvt.common.trading_models import BuyParameter, SellParameter, TradingResult
from zvt.trading.trading_models import (
    BuildTradingPlanModel,
    TradingPlanModel,
    QueryTradingPlanModel,
    QueryStockQuoteModel,
    StockQuoteStatsModel,
    QueryStockQuoteSettingModel,
    BuildQueryStockQuoteSettingModel,
    QueryTagQuoteModel,
    TagQuoteStatsModel,
)
from zvt.trading.trading_schemas import QueryStockQuoteSetting

trading_router = APIRouter(
    prefix="/api/trading",
    tags=["trading"],
    responses={404: {"description": "Not found"}},
)


@trading_router.get("/get_query_stock_quote_setting", response_model=Optional[QueryStockQuoteSettingModel])
def get_query_stock_quote_setting():
    with contract_api.DBSession(provider="zvt", data_schema=QueryStockQuoteSetting)() as session:
        query_setting: List[QueryStockQuoteSetting] = QueryStockQuoteSetting.query_data(
            session=session, return_type="domain"
        )
        if query_setting:
            return query_setting[0]
        return None


@trading_router.post("/build_query_stock_quote_setting", response_model=QueryStockQuoteSettingModel)
def build_query_stock_quote_setting(build_query_stock_quote_setting_model: BuildQueryStockQuoteSettingModel):
    return trading_service.build_query_stock_quote_setting(build_query_stock_quote_setting_model)


@trading_router.post("/query_tag_quotes", response_model=List[TagQuoteStatsModel])
def query_trading_plan(query_tag_quote_model: QueryTagQuoteModel):
    return trading_service.query_tag_quotes(query_tag_quote_model)


@trading_router.post("/query_stock_quotes", response_model=StockQuoteStatsModel)
def query_trading_plan(query_stock_quote_model: QueryStockQuoteModel):
    return trading_service.query_stock_quotes(query_stock_quote_model)


@trading_router.post("/build_trading_plan", response_model=TradingPlanModel)
def build_trading_plan(build_trading_plan_model: BuildTradingPlanModel):
    return trading_service.build_trading_plan(build_trading_plan_model)


@trading_router.post("/query_trading_plan", response_model=Page[TradingPlanModel])
def query_trading_plan(query_trading_plan_model: QueryTradingPlanModel):
    return trading_service.query_trading_plan(query_trading_plan_model)


@trading_router.get("/get_current_trading_plan", response_model=List[TradingPlanModel])
def get_current_trading_plan():
    return trading_service.get_current_trading_plan()


@trading_router.get("/get_future_trading_plan", response_model=List[TradingPlanModel])
def get_future_trading_plan():
    return trading_service.get_future_trading_plan()


@trading_router.post("/buy", response_model=TradingResult)
def buy(buy_position_strategy: BuyParameter):
    if platform.system() == "Windows":
        from zvt.broker.qmt.context import qmt_context

        return qmt_context.qmt_account.buy(buy_position_strategy)
    else:
        raise HTTPException(status_code=500, detail="Please use qmt in windows! ")


@trading_router.post("/sell", response_model=TradingResult)
def sell(sell_position_strategy: SellParameter):
    if platform.system() == "Windows":
        from zvt.broker.qmt.context import qmt_context

        return qmt_context.qmt_account.sell(sell_position_strategy)
    else:
        raise HTTPException(status_code=500, detail="Please use qmt in windows! ")
