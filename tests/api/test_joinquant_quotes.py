from zvdata.domain import get_db_session
from zvdata.structs import IntervalLevel
from ..context import init_context

init_context()

from zvt.api import technical

day_k_session = get_db_session(provider='joinquant',
                               db_name='stock_1d_kdata')  # type: sqlalchemy.orm.Session

day_1h_session = get_db_session(provider='joinquant',
                                db_name='stock_1h_kdata')  # type: sqlalchemy.orm.Session


def test_jq_603220_kdata():
    df = technical.get_kdata(entity_id='stock_sh_603220', session=day_k_session, level=IntervalLevel.LEVEL_1DAY,
                             provider='joinquant')
    print(df)
    df = technical.get_kdata(entity_id='stock_sh_603220', session=day_1h_session, level=IntervalLevel.LEVEL_1HOUR,
                             provider='joinquant')
    print(df)
