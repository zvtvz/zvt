# -*- coding: utf-8 -*-
from zvt.settings import DATA_SAMPLE_PATH, DATA_SAMPLE_ZIP_PATH
from zvt.utils.zip_utils import unzip

if __name__ == '__main__':
    unzip(DATA_SAMPLE_ZIP_PATH, DATA_SAMPLE_PATH)
