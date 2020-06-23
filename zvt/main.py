from zvt.app import app
from zvt.apps.trader_app import serve_layout

app.layout = serve_layout


def main():
    app.run_server(debug=True)


if __name__ == '__main__':
    main()
