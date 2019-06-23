from ..context import init_context

init_context()

from typing import List

from zvt.api import fundamental
from zvt.domain import get_db_session, StoreCategory, Provider, TopTenHolder, TopTenTradableHolder

session = get_db_session(provider='eastmoney', store_category=StoreCategory.holder)  # type: sqlalchemy.orm.Session


# 十大股东
def test_000778_top_ten_holder():
    result: List[TopTenHolder] = fundamental.get_top_ten_holder(session=session, provider=Provider.EASTMONEY,
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
    result: List[TopTenHolder] = fundamental.get_top_ten_tradable_holder(session=session, provider=Provider.EASTMONEY,
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
