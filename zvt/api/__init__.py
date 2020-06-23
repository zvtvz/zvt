# -*- coding: utf-8 -*-
import enum


class AdjustType(enum.Enum):
    # 这里用拼音，因为英文不直观 split-adjusted？wtf?
    # 不复权
    bfq = 'bfq'
    # 前复权
    qfq = 'qfq'
    # 后复权
    hfq = 'hfq'


from .quote import *
