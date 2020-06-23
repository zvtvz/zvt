# script to auto generate some files
from zvt import ZVT_TEST_DATA_PATH, DATA_SAMPLE_ZIP_PATH
from zvt.utils.zip_utils import zip_dir

if __name__ == '__main__':
    zip_dir(ZVT_TEST_DATA_PATH, zip_file_name=DATA_SAMPLE_ZIP_PATH)
