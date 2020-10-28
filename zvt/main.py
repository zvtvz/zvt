from zvt import init_plugins
from zvt.ui import zvt_app
from zvt.ui.apps.trader_app import serve_layout

zvt_app.layout = serve_layout


def main():
    init_plugins()
    zvt_app.run_server()


if __name__ == '__main__':
    main()
