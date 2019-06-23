# -*- coding: utf-8 -*-
import inspect
from typing import List

from zvt.utils.utils import marshal_object_for_ui


class ConstructorMeta(object):

    def __init__(self) -> None:
        self.args: List[str] = None
        self.annotations: dict = None
        self.defaults: List = None
        self.metas: dict = None

    def __repr__(self):
        return str(self.__dict__)


class Constructor(object):
    @classmethod
    def get_constructor_meta(cls):
        spec = inspect.getfullargspec(cls)
        meta = ConstructorMeta()
        meta.args = [arg for arg in spec.args if arg != 'self']
        meta.annotations = spec.annotations
        meta.defaults = [marshal_object_for_ui(default) for default in spec.defaults]
        meta.metas = {}
        return meta
