from zvt.ui import zvt_app
from zvt.ui.apps.trader_app import serve_layout

zvt_app.layout = serve_layout


def main():
    zvt_app.run_server()


if __name__ == '__main__':
    main()
