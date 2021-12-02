# -*- coding: utf-8 -*-
from zvt.factors import ZFactor


def test_z_factor():
    z = ZFactor(codes=["000338"], need_persist=False)
    z.draw(show=True)

    z = ZFactor(codes=["000338", "601318"], need_persist=True)
    z.draw(show=True)
