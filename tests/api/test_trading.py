from zvdata.contract import get_db_session
from zvt.api.api import get_holder_trading, get_manager_trading
from ..context import init_test_context

init_test_context()

from typing import List

from zvt.domain import HolderTrading, ManagerTrading

session = get_db_session(provider='eastmoney', db_name='trading')  # type: sqlalchemy.orm.Session


# 股东交易
def test_000778_holder_trading():
    result: List[HolderTrading] = get_holder_trading(session=session, provider='eastmoney',
                                                     return_type='domain',
                                                     codes=['000778'],
                                                     end_timestamp='2018-09-30',
                                                     start_timestamp='2018-09-30',
                                                     order=HolderTrading.holding_pct.desc())
    assert len(result) == 6
    assert result[0].holder_name == '新兴际华集团有限公司'
    assert result[0].change_pct == 0.0205
    assert result[0].volume == 32080000
    assert result[0].holding_pct == 0.3996


# 高管交易
def test_000778_manager_trading():
    result: List[ManagerTrading] = get_manager_trading(session=session, provider='eastmoney',
                                                       return_type='domain',
                                                       codes=['000778'],
                                                       end_timestamp='2018-09-30',
                                                       start_timestamp='2017-09-30',
                                                       order=ManagerTrading.holding.desc())
    assert len(result) == 1
    assert result[0].trading_person == '巩国平'
    assert result[0].volume == 8400
    assert result[0].price == None
    assert result[0].holding == 18700
    assert result[0].trading_way == '增持'
    assert result[0].manager_position == '职工监事'
    assert result[0].manager == '巩国平'
    assert result[0].relationship_with_manager == '本人'
