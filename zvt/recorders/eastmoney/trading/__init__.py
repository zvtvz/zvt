# the __all__ is generated
__all__ = []

# __init__.py structure:
# common code of the package
# export interface in __all__ which contains __all__ of its sub modules

# import all from submodule eastmoney_manager_trading_recorder
from .eastmoney_manager_trading_recorder import *
from .eastmoney_manager_trading_recorder import __all__ as _eastmoney_manager_trading_recorder_all
__all__ += _eastmoney_manager_trading_recorder_all

# import all from submodule eastmoney_holder_trading_recorder
from .eastmoney_holder_trading_recorder import *
from .eastmoney_holder_trading_recorder import __all__ as _eastmoney_holder_trading_recorder_all
__all__ += _eastmoney_holder_trading_recorder_all