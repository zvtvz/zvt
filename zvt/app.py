# -*- coding: utf-8 -*-

import dash

app = dash.Dash(__name__)

server = app.server

app.config.suppress_callback_exceptions = True
