# -*- coding: utf-8 -*-#
# the __all__ is generated
__all__ = []

# __init__.py structure:
# common code of the package
# export interface in __all__ which contains __all__ of its sub modules

# import all from submodule generator
from .generator import *
from .generator import __all__ as _generator_all
__all__ += _generator_all

# import all from submodule templates
from .templates import *
from .templates import __all__ as _templates_all
__all__ += _templates_all