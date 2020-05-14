# script to auto generate some files
from zvt import ZVT_TEST_DATA_PATH, DATA_SAMPLE_ZIP_PATH
from zvt.utils.zip_utils import zip_dir

if __name__ == '__main__':
    import os

    from zvt.core.contract import generate_api
    from zvt import *

    print(domain.zvt_schemas)

    # domain_path = zvt.domain.__path__[0]
    api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'api'))

    generate_api(api_path=api_path)

    zip_dir(ZVT_TEST_DATA_PATH, zip_file_name=DATA_SAMPLE_ZIP_PATH)
