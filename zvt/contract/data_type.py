# -*- coding: utf-8 -*-

class Bean(object):

    def __init__(self) -> None:
        super().__init__()
        self.__dict__

    def dict(self):
        return self.__dict__

    def from_dct(self, dct: dict):
        if dct:
            for k in dct:
                self.__dict__[k] = dct[k]
