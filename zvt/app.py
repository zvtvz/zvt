# -*- coding: utf-8 -*-

import dash

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)

server = app.server

app.config.suppress_callback_exceptions = True
