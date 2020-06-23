# -*- coding: utf-8 -*-

import pluggy

from zvt import impls, zvt_env, specs
from zvt.contract import zvt_context
from zvt.domain import Stock1dHfqKdata


def main():
    pm = get_plugin_manager()

    runner = ZvtRunner(pm.hook)
    runner.run()


def get_plugin_manager():
    pm = pluggy.PluginManager("zvt")
    pm.add_hookspecs(specs)
    pm.load_setuptools_entrypoints("zvt")
    pm.register(impls)
    return pm


class ZvtRunner:

    def __init__(self, hook):
        self.hook = hook

    def run(self):
        # setup the plugin config
        kvs = self.hook.zvt_setup_env(config=zvt_env)
        for kv in kvs:
            zvt_env[kv[0]] = kv[1]

        print(zvt_env)

        for schema in zvt_context.schemas:
            print(schema)
            if schema.__name__ == 'Coin':
                schema.record_data()


if __name__ == "__main__":
    # main()
    Stock1dHfqKdata.record_data(codes=['000338'])
