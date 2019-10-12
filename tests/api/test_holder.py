from zvdata.contract import get_db_session
from zvt.api.api import get_top_ten_holder, get_top_ten_tradable_holder
from ..context import init_test_context

init_test_context()

from typing import List

from zvt.domain import TopTenHolder, TopTenTradableHolder

session = get_db_session(provider='eastmoney', db_name='holder')  # type: sqlalchemy.orm.Session


# 十大股东
def test_000778_top_ten_holder():
    result: List[TopTenHolder] = get_top_ten_holder(session=session, provider='eastmoney',
                                                    return_type='domain',
                                                    codes=['000778'], end_timestamp='2018-09-30',
                                                    start_timestamp='2018-09-30',
                                                    order=TopTenHolder.shareholding_ratio.desc())
    assert len(result) == 10
    assert result[0].holder_name == '新兴际华集团有限公司'
    assert result[0].shareholding_numbers == 1595000000
    assert result[0].shareholding_ratio == 0.3996
    assert result[0].change == 32080000
    assert result[0].change_ratio == 0.0205


def test_000778_top_ten_tradable_holder():
    result: List[TopTenHolder] = get_top_ten_tradable_holder(session=session, provider='eastmoney',
                                                             return_type='domain',
                                                             codes=['000778'], end_timestamp='2018-09-30',
                                                             start_timestamp='2018-09-30',
                                                             order=TopTenTradableHolder.shareholding_ratio.desc())
    assert len(result) == 10
    assert result[0].holder_name == '新兴际华集团有限公司'
    assert result[0].shareholding_numbers == 1525000000
    assert result[0].shareholding_ratio == 0.389
    assert result[0].change == 38560000
    assert result[0].change_ratio == 0.0259
