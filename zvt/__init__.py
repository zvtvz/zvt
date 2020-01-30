# -*- coding: utf-8 -*-
import json
import logging
import os
from logging.handlers import RotatingFileHandler

import pandas as pd

from zvdata.contract import init_data_env
from zvt.settings import DATA_SAMPLE_ZIP_PATH, ZVT_TEST_HOME, ZVT_HOME, ZVT_TEST_DATA_PATH, ZVT_TEST_ZIP_DATA_PATH
from zvt.utils.zip_utils import unzip


def init_log(file_name='zvt.log', log_dir=None, simple_formatter=True):
    if not log_dir:
        log_dir = zvt_env['log_path']

    root_logger = logging.getLogger()

    # reset the handlers
    root_logger.handlers = []

    root_logger.setLevel(logging.INFO)

    file_name = os.path.join(log_dir, file_name)

    fh = RotatingFileHandler(file_name, maxBytes=524288000, backupCount=10)

    fh.setLevel(logging.INFO)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # create formatter and add it to the handlers
    if simple_formatter:
        formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s  %(threadName)s  %(message)s")
    else:
        formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s  %(threadName)s  %(name)s:%(filename)s:%(lineno)s  %(funcName)s  %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    root_logger.addHandler(fh)
    root_logger.addHandler(ch)


pd.set_option('expand_frame_repr', False)
pd.set_option('mode.chained_assignment', 'raise')

zvt_env = {}


def init_env(zvt_home: str) -> None:
    """

    :param zvt_home: home path for zvt
    """
    data_path = os.path.join(zvt_home, 'data')
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    init_data_env(data_path=data_path, domain_module='zvt.domain')

    zvt_env['zvt_home'] = zvt_home
    zvt_env['data_path'] = data_path
    zvt_env['domain_module'] = 'zvt.domain'

    # path for storing ui results
    zvt_env['ui_path'] = os.path.join(zvt_home, 'ui')
    if not os.path.exists(zvt_env['ui_path']):
        os.makedirs(zvt_env['ui_path'])

    # path for storing logs
    zvt_env['log_path'] = os.path.join(zvt_home, 'logs')
    if not os.path.exists(zvt_env['log_path']):
        os.makedirs(zvt_env['log_path'])

    # create default config.json if not exist
    config_path = os.path.join(zvt_home, 'config.json')
    if not os.path.exists(config_path):
        from shutil import copyfile
        copyfile(os.path.abspath(os.path.join(os.path.dirname(__file__), 'samples', 'config.json')), config_path)

    with open(config_path) as f:
        config_json = json.load(f)
        for k in config_json:
            zvt_env[k] = config_json[k]

    init_log()

    import pprint
    pprint.pprint(zvt_env)


if os.getenv('TESTING_ZVT'):
    init_env(zvt_home=ZVT_TEST_HOME)

    # init the sample data if need
    same = False
    if os.path.exists(ZVT_TEST_ZIP_DATA_PATH):
        import filecmp

        same = filecmp.cmp(ZVT_TEST_ZIP_DATA_PATH, DATA_SAMPLE_ZIP_PATH)

    if not same:
        from shutil import copyfile

        copyfile(DATA_SAMPLE_ZIP_PATH, ZVT_TEST_ZIP_DATA_PATH)
        unzip(ZVT_TEST_ZIP_DATA_PATH, ZVT_TEST_DATA_PATH)

else:
    init_env(zvt_home=ZVT_HOME)

import zvt.domain as domain
import zvt.recorders as recorders

__all__ = ['domain', 'recorders', 'zvt_env', 'init_log', 'init_env']
