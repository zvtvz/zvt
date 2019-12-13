# script for generate api for the domain with decorator @register_api
if __name__ == '__main__':
    import os

    from zvdata.contract import generate_api
    from zvt import *

    print(domain.global_schemas)

    # domain_path = zvt.domain.__path__[0]
    api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'api'))

    generate_api(api_path=api_path)
