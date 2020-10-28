# -*- coding: utf-8 -*-
import os
import string

from pkg_resources import resource_string

from zvt.utils.file_utils import list_all_files


def all_tpls(project: str, entity_type: str):
    """
    return list of templates(location,Template)

    :param project:
    :return:
    """
    tpl_dir = os.path.join(os.path.dirname(__file__))
    tpl_files = list_all_files(tpl_dir, ext='template', return_base_name=True)
    tpls = []
    for tpl in tpl_files:
        data = resource_string(__name__, tpl)
        file_location = os.path.splitext(os.path.basename(tpl))[0]
        # we assure that line endings are converted to '\n' for all OS
        data = data.decode(encoding="utf-8").replace(os.linesep, "\n")

        # change path for specific file
        # domain
        if file_location == 'kdata_common.py':
            file_location = f'{project}/domain/quotes/__init__.py'
        elif file_location == 'meta.py':
            file_location = f'{project}/domain/{entity_type}_meta.py'
        # recorder
        elif file_location == 'kdata_recorder.py':
            file_location = f'{project}/recorders/{entity_type}_kdata_recorder.py'
        elif file_location == 'meta_recorder.py':
            file_location = f'{project}/recorders/{entity_type}_meta_recorder.py'
        # fill script
        elif file_location == 'fill_project.py':
            file_location = f'{project}/fill_project.py'
        # tests
        elif file_location == 'test_pass.py':
            file_location = f'tests/test_pass.py'
        elif file_location == 'pkg_init.py':
            file_location = f'{project}/__init__.py'

        tpls.append((file_location, string.Template(data)))
    return tpls


# the __all__ is generated
__all__ = ['all_tpls']
