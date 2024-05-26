# -*- coding: utf-8 -*-
from typing import List

from fastapi import APIRouter

from zvt.contract import zvt_context
from zvt.factors import factor_service
from zvt.factors.factor_models import FactorRequestModel, TradingSignalModel, KdataModel, KdataRequestModel

factor_router = APIRouter(
    prefix="/api/factor",
    tags=["factor"],
    responses={404: {"description": "Not found"}},
)


@factor_router.get("/get_factors", response_model=List[str])
def get_factors():
    return [name for name in zvt_context.factor_cls_registry.keys()]


@factor_router.post("/query_factor_result", response_model=List[TradingSignalModel])
def query_factor_result(factor_request_model: FactorRequestModel):
    return factor_service.query_factor_result(factor_request_model)


@factor_router.post("/query_kdata", response_model=List[KdataModel])
def query_kdata(kdata_request_model: KdataRequestModel):
    return factor_service.query_kdata(kdata_request_model)
