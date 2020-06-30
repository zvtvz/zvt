import logging

from zvt.app import app
from zvt.apps.trader_app import serve_layout

app.layout = serve_layout

import pluggy

from zvt import impls, zvt_env, specs

logger = logging.getLogger(__name__)


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
        self.hook.zvt_setup_env(config=zvt_env)


def main():
    try:
        pm = get_plugin_manager()
        runner = ZvtRunner(pm.hook)
        runner.run()
    except Exception as e:
        logger.warning(e)

    app.run_server()


if __name__ == '__main__':
    main()
