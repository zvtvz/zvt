# -*- coding: utf-8 -*-

import pandas as pd

from zvdata.contract import *
from zvt.settings import LOG_PATH, DATA_SAMPLE_ZIP_PATH, DATA_SAMPLE_PATH, DATA_PATH, UI_PATH


def init_log():
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    fh = logging.FileHandler(os.path.join(LOG_PATH, 'zvt.log'))
    fh.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(levelname)s  %(threadName)s  %(asctime)s  %(name)s:%(filename)s:%(lineno)s  %(funcName)s  %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    root_logger.addHandler(fh)
    root_logger.addHandler(ch)

    logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.ERROR)


pd.set_option('expand_frame_repr', False)
pd.set_option('mode.chained_assignment', 'raise')

init_log()

if os.getenv('TESTING_ZVT'):
    init_context(data_path=DATA_SAMPLE_PATH, ui_path=UI_PATH, log_path=LOG_PATH, domain_module='zvt.domain',
                 register_api=False)
else:
    init_context(data_path=DATA_PATH, ui_path=UI_PATH, log_path=LOG_PATH, domain_module='zvt.domain',
                 register_api=False)

from zvt.domain import init_schema

init_schema()
