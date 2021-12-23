# -*- coding: utf-8 -*-
# the __all__ is generated
__all__ = []

# __init__.py structure:
# common code of the package
# export interface in __all__ which contains __all__ of its sub modules

# import all from submodule dataset
from .dataset import *
from .dataset import __all__ as _dataset_all

__all__ += _dataset_all

# import all from submodule tags
from .tags import *
from .tags import __all__ as _tags_all

__all__ += _tags_all

# import all from submodule tag
from .tag import *
from .tag import __all__ as _tag_all

__all__ += _tag_all
