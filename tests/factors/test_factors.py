# -*- coding: utf-8 -*-
from zvt.factors.zen.zen_factor import ZenFactor


def test_zen_factor():
    z = ZenFactor(
        codes=["000338"],
        need_persist=False,
        provider="joinquant",
    )
    z.draw(show=True)

    z = ZenFactor(
        codes=["000338", "601318"],
        need_persist=True,
        provider="joinquant",
    )
    z.draw(show=True)
