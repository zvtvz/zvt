# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from zvt.settings import DATA_SAMPLE_ZIP_PATH, ZVT_TEST_DATA_PATH
from zvt.utils.zip_utils import unzip

if __name__ == '__main__':
    unzip(DATA_SAMPLE_ZIP_PATH, ZVT_TEST_DATA_PATH)
