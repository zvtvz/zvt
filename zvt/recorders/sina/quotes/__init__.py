# the __all__ is generated
__all__ = []

# __init__.py structure:
# common code of the package
# export interface in __all__ which contains __all__ of its sub modules

# import all from submodule sina_etf_kdata_recorder
from .sina_etf_kdata_recorder import *
from .sina_etf_kdata_recorder import __all__ as _sina_etf_kdata_recorder_all
__all__ += _sina_etf_kdata_recorder_all

# import all from submodule sina_index_kdata_recorder
from .sina_index_kdata_recorder import *
from .sina_index_kdata_recorder import __all__ as _sina_index_kdata_recorder_all
__all__ += _sina_index_kdata_recorder_all