# -*- coding: utf-8 -*-


# the __all__ is generated
__all__ = []

# __init__.py structure:
# common code of the package
# export interface in __all__ which contains __all__ of its sub modules

# import all from submodule emotion
from .emotion import *
from .emotion import __all__ as _emotion_all

__all__ += _emotion_all
