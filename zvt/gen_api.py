import os

from zvdata.domain import generate_api, init_context
from zvt import DATA_PATH

init_context(data_path=DATA_PATH, domain_module='zvt.domain', register_api=True)

# domain_path = zvt.domain.__path__[0]
api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'api'))

generate_api(api_path=api_path, tmp_api_dir='.')
