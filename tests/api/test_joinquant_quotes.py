from zvt.api.quote import get_kdata
from zvt.contract import IntervalLevel
from zvt.contract.api import get_db_session
from ..context import init_test_context

init_test_context()

day_k_session = get_db_session(provider='joinquant',
                               db_name='stock_1d_kdata')  # type: sqlalchemy.orm.Session

day_1h_session = get_db_session(provider='joinquant',
                                db_name='stock_1h_kdata')  # type: sqlalchemy.orm.Session


def test_jq_603220_kdata():
    df = get_kdata(entity_id='stock_sh_603220', session=day_k_session, level=IntervalLevel.LEVEL_1DAY,
                   provider='joinquant')
    print(df)
    df = get_kdata(entity_id='stock_sh_603220', session=day_1h_session, level=IntervalLevel.LEVEL_1HOUR,
                   provider='joinquant')
    print(df)
