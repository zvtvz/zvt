# the __all__ is generated
__all__ = []

# __init__.py structure:
# common code of the package
# export interface in __all__ which contains __all__ of its sub modules

# import all from submodule sina_china_stock_category_recorder
from .sina_china_stock_category_recorder import *
from .sina_china_stock_category_recorder import __all__ as _sina_china_stock_category_recorder_all
__all__ += _sina_china_stock_category_recorder_all