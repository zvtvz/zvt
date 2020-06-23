# -*- coding: utf-8 -*-
import pluggy

hookspec = pluggy.HookspecMarker("zvt")


@hookspec
def zvt_setup_env(config: dict):
    pass
