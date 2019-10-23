# -*- coding: utf-8 -*-

import pandas as pd

from zvdata.contract import *
from zvt.settings import LOG_PATH, DATA_SAMPLE_ZIP_PATH, DATA_SAMPLE_PATH, DATA_PATH, UI_PATH


def init_log():
    if not os.path.exists(zvt_env['log_path']):
        os.makedirs(zvt_env['log_path'])

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    fh = logging.FileHandler(os.path.join(zvt_env['log_path'], 'zvt.log'))
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

zvt_env = {}


def init_env(data_path):
    init_data_env(data_path=data_path, domain_module='zvt.domain')

    zvt_env['data_path'] = data_path
    zvt_env['domain_module'] = 'zvt.domain'

    # path for storing ui results
    zvt_env['ui_path'] = os.path.join(data_path, 'ui')
    if not os.path.exists(zvt_env['ui_path']):
        os.makedirs(zvt_env['ui_path'])

    # path for storing logs
    zvt_env['log_path'] = os.path.join(data_path, 'log_path')
    if not os.path.exists(zvt_env['log_path']):
        os.makedirs(zvt_env['log_path'])

    init_log()

    from zvt.domain import init_schema

    init_schema()


if os.getenv('TESTING_ZVT'):
    init_env(data_path=DATA_SAMPLE_PATH)
else:
    init_env(data_path=DATA_PATH)

    if not zvt_env.get('data_path'):
        print('please use init_env to set zvt data path at first')
