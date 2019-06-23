from ..context import init_context

init_context()

from zvt.api import technical
from zvt.domain import get_db_session, StoreCategory, TradingLevel

day_k_session = get_db_session(provider='joinquant',
                               store_category=StoreCategory.stock_1d_kdata)  # type: sqlalchemy.orm.Session

day_1h_session = get_db_session(provider='joinquant',
                                store_category=StoreCategory.stock_1h_kdata)  # type: sqlalchemy.orm.Session


def test_jq_603220_kdata():
    df = technical.get_kdata(security_id='stock_sh_603220', session=day_k_session, level=TradingLevel.LEVEL_1DAY,
                             provider='joinquant')
    print(df)
    df = technical.get_kdata(security_id='stock_sh_603220', session=day_1h_session, level=TradingLevel.LEVEL_1HOUR,
                             provider='joinquant')
    print(df)
