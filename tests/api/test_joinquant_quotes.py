from zvdata.contract import get_db_session
from zvdata import IntervalLevel
from ..context import init_test_context

init_test_context()

from zvt.api import quote

day_k_session = get_db_session(provider='joinquant',
                               db_name='stock_1d_kdata')  # type: sqlalchemy.orm.Session

day_1h_session = get_db_session(provider='joinquant',
                                db_name='stock_1h_kdata')  # type: sqlalchemy.orm.Session


def test_jq_603220_kdata():
    df = quote.get_kdata(entity_id='stock_sh_603220', session=day_k_session, level=IntervalLevel.LEVEL_1DAY,
                         provider='joinquant')
    print(df)
    df = quote.get_kdata(entity_id='stock_sh_603220', session=day_1h_session, level=IntervalLevel.LEVEL_1HOUR,
                         provider='joinquant')
    print(df)
