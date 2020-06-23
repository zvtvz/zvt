# -*- coding: utf-8 -*-
import zvt


@zvt.hookimpl
def zvt_setup_env(config: dict):
    return "zvt", {}
