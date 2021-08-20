# the __all__ is generated
__all__ = []

# __init__.py structure:
# common code of the package
# export interface in __all__ which contains __all__ of its sub modules

# import all from submodule manager_trading_recorder
from .manager_trading_recorder import *
from .manager_trading_recorder import __all__ as _manager_trading_recorder_all
__all__ += _manager_trading_recorder_all

# import all from submodule holder_trading_recorder
from .holder_trading_recorder import *
from .holder_trading_recorder import __all__ as _holder_trading_recorder_all
__all__ += _holder_trading_recorder_all