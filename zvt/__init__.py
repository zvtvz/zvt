# -*- coding: utf-8 -*-
import enum
import importlib
import json
import logging
import os
import pkgutil
import pprint
from logging.handlers import RotatingFileHandler

import pandas as pd
import pkg_resources
from pkg_resources import get_distribution, DistributionNotFound

from zvt.settings import DATA_SAMPLE_ZIP_PATH, ZVT_TEST_HOME, ZVT_HOME, ZVT_TEST_DATA_PATH, ZVT_TEST_ZIP_DATA_PATH

try:
    dist_name = __name__
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = 'unknown'
finally:
    del get_distribution, DistributionNotFound

logger = logging.getLogger(__name__)


# common class
class IntervalLevel(enum.Enum):
    LEVEL_TICK = 'tick'
    LEVEL_1MIN = '1m'
    LEVEL_5MIN = '5m'
    LEVEL_15MIN = '15m'
    LEVEL_30MIN = '30m'
    LEVEL_1HOUR = '1h'
    LEVEL_4HOUR = '4h'
    LEVEL_1DAY = '1d'
    LEVEL_1WEEK = '1wk'
    LEVEL_1MON = '1mon'

    def to_pd_freq(self):
        if self == IntervalLevel.LEVEL_1MIN:
            return '1min'
        if self == IntervalLevel.LEVEL_5MIN:
            return '5min'
        if self == IntervalLevel.LEVEL_15MIN:
            return '15min'
        if self == IntervalLevel.LEVEL_30MIN:
            return '30min'
        if self == IntervalLevel.LEVEL_1HOUR:
            return '1H'
        if self == IntervalLevel.LEVEL_4HOUR:
            return '4H'
        if self >= IntervalLevel.LEVEL_1DAY:
            return '1D'

    def floor_timestamp(self, pd_timestamp):
        if self == IntervalLevel.LEVEL_1MIN:
            return pd_timestamp.floor('1min')
        if self == IntervalLevel.LEVEL_5MIN:
            return pd_timestamp.floor('5min')
        if self == IntervalLevel.LEVEL_15MIN:
            return pd_timestamp.floor('15min')
        if self == IntervalLevel.LEVEL_30MIN:
            return pd_timestamp.floor('30min')
        if self == IntervalLevel.LEVEL_1HOUR:
            return pd_timestamp.floor('1h')
        if self == IntervalLevel.LEVEL_4HOUR:
            return pd_timestamp.floor('4h')
        if self == IntervalLevel.LEVEL_1DAY:
            return pd_timestamp.floor('1d')

    def to_minute(self):
        return int(self.to_second() / 60)

    def to_second(self):
        return int(self.to_ms() / 1000)

    def to_ms(self):
        # we treat tick intervals is 5s, you could change it
        if self == IntervalLevel.LEVEL_TICK:
            return 5 * 1000
        if self == IntervalLevel.LEVEL_1MIN:
            return 60 * 1000
        if self == IntervalLevel.LEVEL_5MIN:
            return 5 * 60 * 1000
        if self == IntervalLevel.LEVEL_15MIN:
            return 15 * 60 * 1000
        if self == IntervalLevel.LEVEL_30MIN:
            return 30 * 60 * 1000
        if self == IntervalLevel.LEVEL_1HOUR:
            return 60 * 60 * 1000
        if self == IntervalLevel.LEVEL_4HOUR:
            return 4 * 60 * 60 * 1000
        if self == IntervalLevel.LEVEL_1DAY:
            return 24 * 60 * 60 * 1000
        if self == IntervalLevel.LEVEL_1WEEK:
            return 7 * 24 * 60 * 60 * 1000
        if self == IntervalLevel.LEVEL_1MON:
            return 31 * 7 * 24 * 60 * 60 * 1000

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.to_ms() >= other.to_ms()
        return NotImplemented

    def __gt__(self, other):

        if self.__class__ is other.__class__:
            return self.to_ms() > other.to_ms()
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.to_ms() <= other.to_ms()
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.to_ms() < other.to_ms()
        return NotImplemented


class AdjustType(enum.Enum):
    # 这里用拼音，因为英文不直观 split-adjusted？wtf?
    # 不复权
    bfq = 'bfq'
    # 前复权
    qfq = 'qfq'
    # 后复权
    hfq = 'hfq'


def init_log(file_name='zvt.log', log_dir=None, simple_formatter=True):
    if not log_dir:
        log_dir = zvt_env['log_path']

    root_logger = logging.getLogger()

    # reset the handlers
    root_logger.handlers = []

    root_logger.setLevel(logging.INFO)

    file_name = os.path.join(log_dir, file_name)

    file_log_handler = RotatingFileHandler(file_name, maxBytes=524288000, backupCount=10)

    file_log_handler.setLevel(logging.INFO)

    console_log_handler = logging.StreamHandler()
    console_log_handler.setLevel(logging.INFO)

    # create formatter and add it to the handlers
    if simple_formatter:
        formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s  %(threadName)s  %(message)s")
    else:
        formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s  %(threadName)s  %(name)s:%(filename)s:%(lineno)s  %(funcName)s  %(message)s")
    file_log_handler.setFormatter(formatter)
    console_log_handler.setFormatter(formatter)

    # add the handlers to the logger
    root_logger.addHandler(file_log_handler)
    root_logger.addHandler(console_log_handler)


pd.set_option('expand_frame_repr', False)
pd.set_option('mode.chained_assignment', 'raise')
# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)

zvt_env = {}

zvt_config = {}

_plugins = {}


def init_env(zvt_home: str, **kwargs) -> dict:
    """
    init env

    :param zvt_home: home path for zvt
    """
    data_path = os.path.join(zvt_home, 'data')
    tmp_path = os.path.join(zvt_home, 'tmp')
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    zvt_env['zvt_home'] = zvt_home
    zvt_env['data_path'] = data_path
    zvt_env['tmp_path'] = tmp_path

    # path for storing ui results
    zvt_env['ui_path'] = os.path.join(zvt_home, 'ui')
    if not os.path.exists(zvt_env['ui_path']):
        os.makedirs(zvt_env['ui_path'])

    # path for storing logs
    zvt_env['log_path'] = os.path.join(zvt_home, 'logs')
    if not os.path.exists(zvt_env['log_path']):
        os.makedirs(zvt_env['log_path'])

    init_log()

    pprint.pprint(zvt_env)

    # init config
    init_config(current_config=zvt_config, **kwargs)
    # init plugin
    # init_plugins()

    return zvt_env


def init_config(pkg_name: str = None, current_config: dict = None, **kwargs) -> dict:
    """
    init config
    """

    # create default config.json if not exist
    if pkg_name:
        config_file = f'{pkg_name}_config.json'
    else:
        pkg_name = 'zvt'
        config_file = 'config.json'

    logger.info(f'init config for {pkg_name}, current_config:{current_config}')

    config_path = os.path.join(zvt_env['zvt_home'], config_file)
    if not os.path.exists(config_path):
        from shutil import copyfile
        try:
            sample_config = pkg_resources.resource_filename(pkg_name, 'config.json')
            if os.path.exists(sample_config):
                copyfile(sample_config, config_path)
        except Exception as e:
            logger.warning(f'could not load config.json from package {pkg_name}')

    if os.path.exists(config_path):
        with open(config_path) as f:
            config_json = json.load(f)
            for k in config_json:
                current_config[k] = config_json[k]

    # set and save the config
    for k in kwargs:
        current_config[k] = kwargs[k]
        with open(config_path, 'w+') as outfile:
            json.dump(current_config, outfile)

    pprint.pprint(current_config)
    logger.info(f'current_config:{current_config}')

    return current_config


def init_plugins():
    for finder, name, ispkg in pkgutil.iter_modules():
        if name.startswith('zvt_'):
            try:
                _plugins[name] = importlib.import_module(name)
            except Exception as e:
                logger.warning(f'failed to load plugin {name}', e)
    logger.info(f'loaded plugins:{_plugins}')


if os.getenv('TESTING_ZVT'):
    init_env(zvt_home=ZVT_TEST_HOME)

    # init the sample data if need
    same = False
    if os.path.exists(ZVT_TEST_ZIP_DATA_PATH):
        import filecmp

        same = filecmp.cmp(ZVT_TEST_ZIP_DATA_PATH, DATA_SAMPLE_ZIP_PATH)

    if not same:
        from shutil import copyfile
        from zvt.utils.zip_utils import unzip

        copyfile(DATA_SAMPLE_ZIP_PATH, ZVT_TEST_ZIP_DATA_PATH)
        unzip(ZVT_TEST_ZIP_DATA_PATH, ZVT_TEST_DATA_PATH)

else:
    init_env(zvt_home=ZVT_HOME)

# import the recorders for register them to the domain
import zvt.recorders as zvt_recorders

__all__ = ['zvt_env', 'zvt_config', 'init_log', 'init_env', 'init_config', 'IntervalLevel', '__version__', 'AdjustType']
