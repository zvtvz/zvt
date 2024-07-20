# -*- coding: utf-8 -*-
from typing import List

from zvt.contract.model import MixinModel


class PositionModel(MixinModel):
    #: 机器人名字
    trader_name: str
    #: 做多数量
    long_amount: float
    #: 可平多数量
    available_long: float
    #: 平均做多价格
    average_long_price: float
    #: 做空数量
    short_amount: float
    #: 可平空数量
    available_short: float
    #: 平均做空价格
    average_short_price: float
    #: 盈亏
    profit: float
    #: 盈亏比例
    profit_rate: float
    #: 市值 或者 占用的保证金(方便起见，总是100%)
    value: float
    #: 交易类型(0代表T+0,1代表T+1)
    trading_t: int


class AccountStatsModel(MixinModel):
    #: 投入金额
    input_money: float
    #: 机器人名字
    trader_name: str
    #: 具体仓位
    positions: List[PositionModel]
    #: 市值
    value: float
    #: 可用现金
    cash: float
    #: value + cash
    all_value: float

    #: 盈亏
    profit: float
    #: 盈亏比例
    profit_rate: float

    #: 收盘计算
    closing: bool
