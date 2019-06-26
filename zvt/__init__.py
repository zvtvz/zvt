# -*- coding: utf-8 -*-
import logging
import os

import pandas as pd

from zvt.settings import LOG_PATH, DATA_SAMPLE_ZIP_PATH, DATA_SAMPLE_PATH
from zvt.utils.zip_utils import unzip, zip_dir


def load_data():
    unzip(DATA_SAMPLE_ZIP_PATH, DATA_SAMPLE_PATH)


def upload_data():
    zip_dir(DATA_SAMPLE_PATH, zip_file_name='datasample.zip')


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
        "%(levelname)s  %(threadName)s  %(asctime)s  %(name)s:%(lineno)s  %(funcName)s  %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    root_logger.addHandler(fh)
    root_logger.addHandler(ch)

    logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.ERROR)


pd.set_option('expand_frame_repr', False)
pd.set_option('mode.chained_assignment', 'raise')

# init_schema()
init_log()
